import re
import tempfile
import copy
import pprint
import ply.lex as lex
import ply.yacc as yacc
from ply.yacc import YaccProduction, LRParser
from ply.lex import LexToken, Lexer

from sigma.rule import (
    SigmaDetectionItem,
    SigmaDetection,
    SigmaDetections,
    SigmaRule,
    SigmaLogSource,
)
from sigma.modifiers import (
    SigmaEndswithModifier,
    SigmaContainsModifier,
    SigmaListModifier,
    SigmaAllModifier,
    SigmaStartswithModifier,
)
from sigma.conditions import ConditionAND, ConditionOR
from sigma.backends.elasticsearch.elasticsearch_lucene import LuceneBackend
import logging

logging.basicConfig(
    filename="example.log",
    filemode="w",
    format="%(name)s - %(levelname)s - %(message)s",
    force=True,
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


### A lot of the base regex and parser syntax is taken from the luqum package, credits to the contributors there
class QueryParser:

    def __init__(self, input_string):

        self.lexer: Lexer = lex.lex(module=self, debug=False)
        self.parser: LRParser = yacc.yacc(
            module=self, debug=False, outputdir=tempfile.gettempdir()
        )

        self.temp_detection_items: list[SigmaDetectionItem] = []
        self.detections: list[SigmaDetection] = []
        self.detection: SigmaDetections
        self.rule: SigmaRule

        self.temp_detection: dict = {}
        self.logical_operators: list[str] = []

        #self.lex_tokens(input_string)
        self.parser.parse(input_string)

        self.__check_for_single_condition__()
        self.__build_sigma_detection__()
        self.__build_sigma_rule__()

    def lex_tokens(self, input_string: str):
        self.lexer.input(input_string)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)

    def parse(self, input_string: str):
        self.parser.parse(input_string, lexer=self.lexer)

    def __check_for_single_condition__(self):

        if len(self.temp_detection_items) >= 1:
            detection = SigmaDetection(detection_items=self.temp_detection_items)
            self.detections.append(detection)

    def __build_sigma_detection__(self):

        temp = {}
        temp_names = []
        for idx, detection in enumerate(self.detections):
            name = f"condition-{idx}"
            temp[name] = detection
            temp_names.append(name)

        self.detection = SigmaDetections(detections=temp, condition=temp_names)

    def __build_logsource__(self):

        logsource = None

        fields = {}
        for detection in self.detections:
            for detection_item in detection.detection_items:
                temp_list = []
                field = detection_item.field
                for value in detection_item.value:
                    temp_list.append(str(value))
                if fields.get(field) is None:
                    fields[field] = temp_list
                else:
                    fields[field] += temp_list

        product = fields.get("deviceProduct")
        # category - general event, file_create, application, antivirus, etc
        # product - basically deviceProduct
        # service - more specific, auditd, cron, clamav, apache, etc
        if product is not None:
            logsource = SigmaLogSource(product=product)

        if logsource is None:
            logsource = SigmaLogSource("null")

        return logsource

    def __build_sigma_rule__(self):

        logsource = self.__build_logsource__()

        self.rule = SigmaRule(
            title="TEST", logsource=logsource, detection=self.detection
        )

    reserved = {"AND": "AND_OP", "OR": "OR_OP", "NOT": "NOT", "TO": "TO"}

    # tokens of our grammar
    tokens = (
        [
            "TERM",
            "PHRASE",
            "REGEX",
            "OPERATOR",
            "LPAREN",
            "RPAREN",
            "LBRACKET",
            "RBRACKET",
            "LESSTHAN",
            "GREATERTHAN",
        ]
        +
        # we sort to have a deterministic order, so that gammar signature does not changes
        sorted(list(reserved.values()))
    )

    # precedence rules
    precedence = (
        # since IMPLICIT_OP has no lookahead token, everything not defined here has the lowest
        # precedence (e.g. TERM, PHRASE and REGEX). see https://stackoverflow.com/a/40754838
        # note that we do not need to include all tokens here, as there is no confusion about
        # LBRACKET or something; APPROX is also not necessary, as this token can only occur
        # after a TERM or PHRASE, and there is no confusion about operator precedence
        ("left", "IMPLICIT_OP"),
        ("left", "OR_OP"),
        ("left", "AND_OP"),
        ("nonassoc", "TO"),
    )

    # term

    # the case of : which is used in date is problematic because it is also a delimiter
    # lets catch those expressions apart
    # Note : we must use positive look behind, because regexp engine is eager,
    # and it's only arrived at ':' that it will try this rule
    TIME_RE = r"""
    (?<=T\d{2}):  # look behind for T and two digits: hours
    \d{2}         # minutes
    (:\d{2})?     # seconds
    """
    # this is a wide catching expression, to also include date math.
    # Inspired by the original lucene parser:
    # https://github.com/apache/lucene-solr/blob/master/lucene/queryparser/src/java/org/apache/lucene/queryparser/surround/parser/QueryParser.jj#L189
    # We do allow the wildcards operators ('*' and '?') as our parser doesn't deal with them.

    TERM_RE = r"""
    (?P<term>  # group term
    (?:
    [^\s:^~(){{}}[\]/"'+\-\\<>] # first char is not a space neither some char which have meanings
                                # note: escape of "-" and "]"
                                #       and doubling of "{{}}" (because we use format)
    |                          # but
    \\.                        # we can start with an escaped character
    )
    ([^\s:^\\~(){{}}[\]]        # following chars
    |                          # OR
    \\.                        # an escaped char
    |                          # OR
    {time_re}                  # a time expression
    )*
    )
    """.format(
        time_re=TIME_RE
    )
    # phrase
    PHRASE_RE = r"""
    (?P<phrase>  # phrase
    "          # opening quote
    (?:        # repeating
        [^\"]   # - a char which is not escape or end of phrase
        |        # OR
        \\.      # - an escaped char
    )*
    "
    |
    '          # opening quote
    (?:        # repeating
        [^\\"]   # - a char which is not escape or end of phrase
        |        # OR
        \\.      # - an escaped char
    )*
    '            # closing quote
    )"""
    # r'(?P<phrase>"(?:[^\\"]|\\"|\\[^"])*")' # this is quite complicated to handle \"

    # regex
    REGEX_RE = r"""
    (?P<regex>  # regex
    /         # open slash
    (?:       # repeating
        [^\\/]  # - a char which is not escape or end of regex
        |       # OR
        \\.     # an escaped char
    )*
    /         # closing slash
    )"""

    def t_SEPARATOR(self, t):
        r"\s+"
        # token_headtail(t, t.value)
        return None  # discard separators

    def t_OPERATOR(self, t: LexToken):
        r"(EQ|StartsWith|Contains|EndsWith|NE)"
        return t

    @lex.TOKEN(TERM_RE)
    def t_TERM(self, t: LexToken):
        # note: it also handles NOT, OR, AND, TO
        # check if it is not a reserved term (an operation)
        t.type = self.reserved.get(t.value, "TERM")
        # t.type = self.operators.get(t.value, "TERM")
        # print(t.type, t.value)
        if t.type == "TERM":
            m = re.match(self.TERM_RE, t.value, re.VERBOSE)
            value = m.group("term")
            t.value = value
        return t

    # text of some simple tokens
    def t_PLUS(self, t: LexToken):
        r"\+"
        return t

    def t_MINUS(self, t: LexToken):
        r"\-"
        return t

    def t_LPAREN(self, t: LexToken):
        r"\("
        return t

    def t_RPAREN(self, t: LexToken):
        r"\)"
        return t

    def t_LBRACKET(self, t: LexToken):
        r"(\[|\{)"
        return t

    def t_RBRACKET(self, t: LexToken):
        r"(\]|\})"
        return t

    def t_GREATERTHAN(self, t: LexToken):
        r">=?"
        return t

    def t_LESSTHAN(self, t: LexToken):
        r"<=?"
        return t

    @lex.TOKEN(PHRASE_RE)
    def t_PHRASE(self, t):
        m = re.match(self.PHRASE_RE, t.value, re.VERBOSE)
        value = m.group("phrase")
        t.value = value
        return t

    @lex.TOKEN(REGEX_RE)
    def t_REGEX(self, t):
        m = re.match(self.REGEX_RE, t.value, re.VERBOSE)
        value = m.group("regex")
        t.value = value
        return t

    def t_error(self, t):
        raise SyntaxError("Illegal character '%s' at position %d" % (t.value, t.lexpos))

    def p_expression_or(self, p: YaccProduction):
        "expression : expression OR_OP expression"
        logging.debug("OR")
        #print(p[1], "\n", p[2], p[3], "\n")
        if p[2] == "OR":
            self.logical_operators.append(p[2])

        if type(p[1]) == SigmaDetectionItem and type(p[3]) == SigmaDetectionItem:
            p[0] = self.__handle__detection_item_or_detection_item__(p[1], p[3])
        elif type(p[1]) == SigmaDetection and type(p[3]) == SigmaDetectionItem:
            p[0] = self.__detection_or_detection_item__(p[1], p[3])
        elif type(p[1]) == SigmaDetection and type(p[3]) == SigmaDetection:
            p[0] = self.__detection_or_detection__(p[1], p[3])
        elif type(p[1]) == SigmaDetectionItem and type(p[3]) == SigmaDetection:
            p[0] = self.__detection_item_or_detection__(p[1], p[3])

        elif type(p[1]) == list and type(p[3]) == SigmaDetectionItem:
            detection = SigmaDetection(detection_items=[p[3]])
            p[1].append(detection)
            p[0] = p[1]
        elif type(p[1]) == SigmaDetection and type(p[3]) == list:
            p[3].insert(0, p[1])
            p[0] = p[3]
        else:
            print("OR", "\n")
            pprint.pprint(p[1])
            pprint.pprint(p[3])

    def p_expression_and(self, p: YaccProduction):
        """expression : expression AND_OP expression"""
        logging.debug("AND")

        # print(p[1], "\n", p[2], p[3], "\n")
        if p[2] == "AND":
            self.logical_operators.append(p[2])

        if type(p[1]) == SigmaDetectionItem and type(p[3]) == SigmaDetectionItem:
            detection = SigmaDetection(detection_items=[p[1], p[3]])
            p[0] = detection
        elif type(p[1]) == SigmaDetection and type(p[3]) == SigmaDetectionItem:
            p[1].detection_items.append(p[3])
            p[0] = p[1]
        elif type(p[1]) == SigmaDetection and type(p[3]) == SigmaDetection:
            p[0] = [p[1], p[3]]
        elif type(p[1]) == list and type(p[3]) == SigmaDetectionItem:
            detection = SigmaDetection(detection_items=[p[3]])
            p[1].append(p[3])
            p[0] = p[1]

        # might mess up the order
        elif type(p[1]) == SigmaDetectionItem and type(p[3]) == SigmaDetection:
            p[3].detection_items.insert(0, p[1])
            p[0] = p[3]
        elif type(p[1]) == list and type(p[3]) == SigmaDetection:
            p[0] = p[1].append(p[3])

        elif type(p[1]) == SigmaDetectionItem and p[3] == None:
            detection = SigmaDetection(detection_items=[p[1]])
            p[0] = detection

        elif type(p[1]) == SigmaDetectionItem and type(p[3]) == list:
            detection = SigmaDetection(detection_items=[p[1]])
            p[3].insert(0, detection)
            p[0] = p[3]
        else:
            # print("AND", p[1], p[2], p[3], "\n")
            print("AND", "\n")
            pprint.pprint(p[1])
            pprint.pprint(p[3])

    def p_expression_implicit(self, p: YaccProduction):
        """expression : expression expression %prec IMPLICIT_OP"""
        logging.debug("IMPLICIT")
        if type(p[1]) == SigmaDetection and type(p[2]) == SigmaDetection:
            p[0] = [p[1], p[2]]
        elif type(p[1]) == list and type(p[2]) == SigmaDetection:
            p[1].append(p[2])
            p[0] = p[1]
        else:
            print("IMPLICIT: ", p[1], p[2])

    def p_expression_not(self, p: YaccProduction):
        """unary_expression : NOT unary_expression"""
        logging.debug("NOT")
        # need to fix this
        # print("NOT: ", p[1], p[2])
        p[1] = f"{self.logical_operators[len(self.logical_operators) - 1]} NOT"
        self.logical_operators[len(self.logical_operators) - 1] = p[1]
        p[0] = p[2]

    def p_expression_unary(self, p: YaccProduction):
        """expression : unary_expression"""
        logging.debug("EXPRSSION UNARY")
        p[0] = p[1]

    def p_grouping(self, p: YaccProduction):
        "unary_expression : LPAREN expression RPAREN"
        logging.debug("GROUPING")
        p[0] = p[2]

        if isinstance(p[0], list):
            temp = []
            for entry in p[0]:
                if entry not in temp:
                    temp.append(entry)

            for entry in temp:
                if entry not in self.detections:
                    self.detections.append(entry)
            #self.detections = p[2]
        elif type(p[0]) == SigmaDetection:
            if p[0] not in self.detections:
                self.detections.append(p[0])
        self.temp_detection_items.clear()
        # self.logical_operators.pop()

    def p_list(self, p: YaccProduction):
        """unary_expression : LBRACKET phrase_or_term RBRACKET"""
        logging.debug("ACTIVELIST")
        p[0] = p[1] + p[2] + p[3]

    def p_lessthan(self, p: YaccProduction):
        """unary_expression : LESSTHAN phrase_or_term"""
        logging.debug("LESS THAN")
        p[0] = "".join(p[1 : len(p)])

    def p_greaterthan(self, p: YaccProduction):
        """unary_expression : GREATERTHAN phrase_or_term"""
        logging.debug("GREATER THAN")
        p[0] = "".join(p[1 : len(p)])

    def p_field_search(self, p: YaccProduction):
        """unary_expression : TERM OPERATOR unary_expression
        | TERM OPERATOR unary_expression TERM"""
        logging.debug("FIELD SEARCH")
        # print("FIELD SEARCH: ", p[1], p[2], p[3])
        if len(p) == 5:
            p[3] = p[3] + p[4]

        p[3] = self.__preprocess_value__(p[3])
        result = self.__check_field_for_modifiers__(p[1], p[3])
        p[1] = result[0]
        p[3] = result[1]
        detection_item = SigmaDetectionItem(
            field=p[1], modifiers=self.__get_sigma_modifiers__(p[2]), value=p[3]
        )

        p[0] = detection_item
        self.temp_detection_items.append(p[0])

    def p_quoting(self, p: YaccProduction):
        "unary_expression : PHRASE"
        logging.debug("QUOTING")
        p[0] = p[1]

    def p_terms(self, p: YaccProduction):
        """unary_expression : TERM"""
        logging.debug("TERMS")
        p[0] = p[1]

    def p_regex(self, p: YaccProduction):
        """unary_expression : REGEX"""
        logging.debug("REGEX")
        p[0] = p[1]

    # handling a special case, TO is reserved only in range
    def p_to_as_term(self, p: YaccProduction):
        """unary_expression : TO"""
        logging.debug("TO AS TERM")
        p[0] = p[1]

    def p_phrase_or_term(self, p: YaccProduction):
        """phrase_or_term : TERM
        | PHRASE"""
        logging.debug("PHRASE OR TERM")
        p[0] = p[1]

    # Error rule for syntax errors
    def p_error(self, p: YaccProduction):
        if p is None:
            error = "unexpected end of expression (maybe due to unmatched parenthesis)"
            pos = "the end"
        else:
            error = "unexpected  '%s'" % p.value
            pos = "position %d" % p.lexpos
        raise SyntaxError("Syntax error in input : %s at %s!" % (error, pos))

    def __get_sigma_modifiers__(self, operator: str):

        mods = []

        lookup = {
            "Contains": SigmaContainsModifier,
            "EndsWith": SigmaEndswithModifier,
            "StartsWith": SigmaStartswithModifier,
        }

        value = lookup.get(operator)
        if value is not None:
            mods.append(value)

        return mods

    def __handle__detection_item_or_detection_item__(
        self, detection_item0: SigmaDetectionItem, detection_item1: SigmaDetectionItem
    ):
        
        if detection_item0.modifiers == detection_item1.modifiers:
            values = [detection_item0.value[0], detection_item1.value[0]]
            detection_item = SigmaDetectionItem(
                field=detection_item0.field,
                modifiers=detection_item0.modifiers,
                value=values,
            )
            detection = SigmaDetection(detection_items=[detection_item])
            return detection
        else:
            detection0 = SigmaDetection(detection_items=[detection_item0])
            detection1 = SigmaDetection(detection_items=[detection_item1])
            return [detection0, detection1]


    def __detection_item_or_detection__(
        self, detection_item: SigmaDetectionItem, detection: SigmaDetection
    ):


        mods = []
        for item in detection.detection_items:
            for mod in item.modifiers:
                if mod not in mods:
                    mods.append(mod)
        #make sure modifiers are the same
        if detection_item.modifiers != mods:
            new_detection = SigmaDetection(detection_items=[detection_item])
            return [new_detection, detection]

        remove = []
        values = []

        if detection_item.field in [x.field for x in detection.detection_items]:
            for item in detection.detection_items:
                if item.field == detection_item.field:
                    
                    for value in item.value:
                        values.append(value)
                    remove.append(item)

            values.insert(0, detection_item.value[0])
            [detection.detection_items.remove(x) for x in remove]
            remove.clear()
            new_detection_item = SigmaDetectionItem(
                field=detection_item.field,
                modifiers=detection_item.modifiers,
                value=values,
            )
            detection.detection_items.insert(0, new_detection_item)
            return detection

    def __detection_or_detection_item__(
        self, detection: SigmaDetection, detection_item: SigmaDetectionItem
    ):

        mods = []
        for item in detection.detection_items:
            for mod in item.modifiers:
                if mod not in mods:
                    mods.append(mod)
        #make sure modifiers are the same
        if detection_item.modifiers != mods:
            new_detection = SigmaDetection(detection_items=[detection_item])
            return [detection, new_detection]

        remove = []
        values = []

        if detection_item.field in [x.field for x in detection.detection_items]:

            for item in detection.detection_items:
                if item.field == detection_item.field:
                    for value in item.value:
                        values.append(value)
                    remove.append(item)

            values.append(detection_item.value[0])
    
            [detection.detection_items.remove(x) for x in remove]
            remove.clear()
            new_detection_item = SigmaDetectionItem(
                field=detection_item.field,
                modifiers=detection_item.modifiers,
                value=values,
            )
            detection.detection_items.append(new_detection_item)
            return detection
        else:
            new_detection = SigmaDetection(detection_items=[detection_item])
            return [detection, new_detection]

    def __detection_or_detection__(
        self, detection: SigmaDetection, detection1: SigmaDetection
    ):

        temp_detections = []
        temp = {}

        for detection in [detection, detection1]:
            for item in detection.detection_items:
                for value in item.value:
                    if temp.get(item.field) == None:
                        temp[item.field] = [
                            {"value": value.to_plain(), "modifiers": item.modifiers}
                        ]
                    else:
                        temp[item.field].append(
                            {"value": value.to_plain(), "modifiers": item.modifiers}
                        )

        for k, v in temp.items():
            if len(v) > 1:
                mods = []
                for modifier in [x["modifiers"] for x in v if len(x["modifiers"]) > 0]:
                    for mod in modifier:
                        if mod not in mods:
                            mods.append(mod)
            else:
                mods = v[0]["modifiers"]
            detection = SigmaDetectionItem(
                field=k, modifiers=mods, value=[x["value"] for x in v]
            )
            temp_detections.append(detection)

        new_detection = SigmaDetection(detection_items=temp_detections)

        return new_detection

    def __preprocess_value__(self, value: str):

        value = value[1:-1]
        return value

    def __check_field_for_modifiers__(self, field: str, value: str):

        if "toLower" in field:
            field = field.replace("toLower", "")
            value = value.lower()

        return [field, value]
