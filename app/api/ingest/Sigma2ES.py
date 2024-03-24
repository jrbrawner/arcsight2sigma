from sigma.backends.elasticsearch.elasticsearch_lucene import LuceneBackend
from sigma.rule import SigmaRule
from sigma.collection import SigmaCollection


class Sigma2ES:

    def __init__(self, rule: SigmaRule):

        self.rule = rule
        self.query = ""
        self.converted_list: list

        self.__convert_to_lql()

        for i in self.converted_list:
            print(i)

        

    def __convert_to_lql(self):

        converter = LuceneBackend()

        collection = SigmaCollection([self.rule])

        self.converted_list = converter.convert(collection)
