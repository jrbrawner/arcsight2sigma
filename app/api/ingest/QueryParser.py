import re
import tempfile
import copy
import pprint
import ply.lex as lex
import ply.yacc as yacc
from ply.yacc import YaccProduction, LRParser
from ply.lex import LexToken, Lexer

import logging

logging.basicConfig(
    filename="example.log",
    filemode="w",
    format="%(name)s - %(levelname)s - %(message)s",
    force=True,
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


### most of the foundational code is taken from the luqum package, credits to the contributors there
class QueryParser:

    def __init__(self, input_string):

        self.lexer: Lexer = lex.lex(module=self, debug=False)
        self.parser: LRParser = yacc.yacc(
            module=self, debug=False, outputdir=tempfile.gettempdir()
        )
        self.input_string : str = input_string

        self.condition_data = {}

        self.temp_detection: dict = {}
        self.logical_operators: list[str] = []

        #self.lex_tokens(input_string)
        self.__preprocess_input__()
        print(self.input_string, "\n")
        self.parse()

    def lex_tokens(self, input_string: str):
        self.lexer.input(input_string)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)

    def parse(self):
        self.parser.parse(self.input_string, lexer=self.lexer)

    def __preprocess_input__(self):
        self.input_string = self.input_string.replace(" CONTAINS ", " Contains ")
        self.input_string = self.input_string.replace(" STARTSWITH ", " StartsWith ")
        self.input_string = self.input_string.replace(" ENDSWITH ", " EndsWith ")
        self.input_string = self.input_string.replace(" = ", " EQ ")

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
        """
        if p[1].get("OR") is not None:
            p[1]["OR"].append(p[3])
            p[0] = p[1]
        else:
            data = {}
            data["OR"] = [p[1], p[3]]
            p[0] = data
        """
        data = {}
        data["OR"] = [p[1], p[3]]
        p[0] = data

    def p_expression_and(self, p: YaccProduction):
        """expression : expression AND_OP expression"""
        logging.debug("AND")
        data = {}
        data["AND"] = [p[1], p[3]]
        p[0] = data
        
    def p_expression_implicit(self, p: YaccProduction):
        """expression : expression expression %prec IMPLICIT_OP"""
        logging.debug("IMPLICIT")

    def p_expression_not(self, p: YaccProduction):
        """unary_expression : NOT unary_expression"""
        logging.debug("NOT")
        # need to fix this
        data = {}
        data["NOT"] = [p[2]]
        p[0] = data

    def p_expression_unary(self, p: YaccProduction):
        """expression : unary_expression"""
        logging.debug("EXPRSSION UNARY")
        p[0] = p[1]

    def p_grouping(self, p: YaccProduction):
        "unary_expression : LPAREN expression RPAREN"
        logging.debug("GROUPING")
        p[0] = p[2]

        self.condition_data = p[0]

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

        data = {
            "term" : p[1],
            "operator" : p[2],
            "value" : p[3]
        }

        p[0] = data
        

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

    def __preprocess_value__(self, value: str):

        value = value[1:-1]
        return value

    def __check_field_for_modifiers__(self, field: str, value: str):

        if "toLower" in field:
            field = field.replace("toLower", "")
            value = value.lower()

        return [field, value]
