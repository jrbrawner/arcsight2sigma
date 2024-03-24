class YamlTest:

    def __init__(self, condition_data):

        self.condition_data = condition_data
        self.condition_list = self.convert_to_sigma_rule(self.condition_data)
        self.final_list : list[dict[str, list]|dict[str, dict]] = []
        self.logical_operators: list[str] = []
        self.detections = {}

        self.last = None
        self.last_type = None


        self.process_dict(self.condition_list)
        self.iterate_final_list()
        self.generate_sigma_rule()

        self.sigma_rule["detection"].update(self.detections)
        temp = []
        for i in self.sigma_rule["detection"]:
            if i != "condition":
                temp.append(i)
        self.sigma_rule["detection"]["condition"] = temp


    def iterate_final_list(self):
        
        dict_handler = SigmaDictHandler()
        
        for idx, condition in enumerate(self.final_list):
            skip = False
            detection = {}
            key = list(condition.keys())[0]
            value = condition.get(key)
            if type(value) == dict:
                dict_handler.add_condition(key, value)

            elif type(value) == list:
                dict_result = dict_handler.result() 
                result = self.__handle_condition_list(key, value)
                
                if type(result) == list:
                    if list in [type(x) for x in result]:
                        #OR WITH MULTIPLE TERMS OR OPERATORS?
                        for temp_idx, entry in enumerate(result):
                            self.detections[f"condition-{idx}-{temp_idx}"] = entry[0]
                            skip = True
                    else:
                        [detection.update(x) for x in result]
                if dict_result is not None:
                    if type(dict_result) == list:
                        if list in [type(x) for x in result]:
                            for temp_idx, entry in enumerate(result):
                                self.detections[f"condition-{idx}-{temp_idx}"] = entry[0]
                                skip = True
                        else:
                            [detection.update(x) for x in dict_result]
                    elif type(dict_result) == dict:
                        detection.update(dict_result)
                if skip == True:
                    pass
                else:
                    self.detections[f"condition-{idx}"] = detection
        
        if len(dict_handler.buffer) > 0:
            dict_result = dict_handler.result()
            self.detections[f"condition-last"] = dict_result 
            
    def __handle_condition_list(self, key, condition_list: list[dict]):
        
        if key == "or":

            terms = list(set([x["term"] for x in condition_list]))
            operators = list(set([x["operator"].lower() for x in condition_list]))
            values = [x["value"] for x in condition_list]

            if len(terms) > 1 or len(operators) > 1:
                #print("OR: TERMS OR OPERATORS GREATER THAN 1")
                result_list = self.__or_terms_or_operators_over_1(condition_list)
                return result_list
            
            if operators[0] != "eq":
                terms = f"{terms[0]}|{operators[0]}"
            else:
                terms = terms[0]
            result = {terms : values}
            return result
        
        elif key == "and" or key == "not":
            terms = list(set([x["term"] for x in condition_list]))
            operators = list(set([x["operator"].lower() for x in condition_list]))
            values = [x["value"] for x in condition_list]

            if len(terms) > 1 or len(operators) > 1:
                result_list = self.__and_terms_or_operators_over_1(condition_list)
                return result_list
            
            if operators[0] != "eq":
                terms = f"{terms[0]}|{operators[0]}"
            else:
                terms = terms[0]
            if len(values) > 1:
                result = {f"{terms}|all" : values}
            else:
                result = {f"{terms}" : values}
            
            return result

    def __and_terms_or_operators_over_1(self, condition_list: list[dict]):
        result_list = []
        temp = {}

        for entry in condition_list:
            if temp.get(f'{entry.get("term")}{entry.get("operator")}') == None:
                temp[f'{entry.get("term")}{entry.get("operator")}'] = [entry]
            elif f'{entry.get("term")}{entry.get("operator")}' is not None:
                temp[f'{entry.get("term")}{entry.get("operator")}'].append(entry)
        
        for key,condition_list in temp.items():
            terms = list(set([x["term"] for x in condition_list]))
            operators = list(set([x["operator"].lower() for x in condition_list]))
            values = [x["value"] for x in condition_list]
            if len(terms) > 1 or len(operators) > 1:
                print("AND: I DONT KNOW WHAT IM DOING")

            if operators[0] != "eq":
                terms = f"{terms[0]}|{operators[0]}"
            else:
                terms = terms[0]

            if len(values) > 1:
                result = {f"{terms}|all" : values}
            else:
                result = {f"{terms}" : values}
            result_list.append(result)
        return result_list

    def __or_terms_or_operators_over_1(self, condition_list):

        result_list = []
        temp = {}
        for entry in condition_list:
            if temp.get(f'{entry.get("term")}{entry.get("operator")}') == None:
                temp[f'{entry.get("term")}{entry.get("operator")}'] = [entry]
            elif f'{entry.get("term")}{entry.get("operator")}' is not None:
                temp[f'{entry.get("term")}{entry.get("operator")}'].append(entry)
        
        for key,condition_list in temp.items():
            terms = list(set([x["term"] for x in condition_list]))
            operators = list(set([x["operator"].lower() for x in condition_list]))
            values = [x["value"] for x in condition_list]
            if len(terms) > 1 or len(operators) > 1:
                print("OR: I DONT KNOW WHAT IM DOING")


            if operators[0] != "eq":
                terms = f"{terms[0]}|{operators[0]}"
            else:
                terms = terms[0]
            result = {f"{terms}" : values}
            result_list.append([result])
            
        return result_list

    def process_dict(self, element, key=None):
        """
        Recursively processes a nested data structure (dicts, lists, dictionaries representing base values).
        When encountering a list of dictionaries representing base values (each dictionary containing 'term',
        'operator', and 'value' keys), it prints the list as a whole. Dictionaries and other types of lists are
        processed recursively as before.

        :param element: The current element to process, which can be a dictionary, list, or base value dictionary.
        :param key: The key associated with the current element, if any.
        """
        if isinstance(element, dict):
            # Process each key-value pair in the dictionary
            if element.get("term") is not None:
                #print(key, element)
                self.final_list.append({key : element})
            else:
                for sub_key, value in element.items():
                    self.process_dict(value, sub_key)  # Recurse with the value and pass the current key
        elif isinstance(element, list):
            # Check if this is a base list: a list where all items are dictionaries with 'term', 'operator', 'value'
            if all(isinstance(item, dict) and {'term', 'operator', 'value'}.issubset(item) for item in element):
                # If it's a base list, print the entire list with its associated key
                #print(f"{key} {element}")
                self.final_list.append({key : element})
            else:
                # If it's not a base list, recurse into its elements
                for item in element:
                    self.process_dict(item, key)
        # No specific handling for base value dictionaries here, as they're part of the base list handling
                
    def convert_to_sigma_rule(self, condition):

        if condition.get("type") == 'and':
            conditions = {"and" : [self.convert_to_sigma_rule(definition) for definition in condition['definitions']]}
            return conditions
        elif condition.get("type") == 'or':
            conditions = {"or" : [self.convert_to_sigma_rule(definition) for definition in condition['definitions']]}
            return conditions
        elif condition.get("type") == 'not':
            conditions = {"not" : [self.convert_to_sigma_rule(condition['definitions'][0])]}
            return conditions
        else:
            return condition

    def generate_sigma_rule(self):
        self.sigma_rule = {
            "title": "Generated Sigma Rule",
            "status": "experimental",
            "description": "Auto-generated Sigma rule from structured data",
            "author": "Generated by script",
            "logsource": {
                "category": "temp",
                "product": "temp"
            },
            "detection": {
                "condition": "temp"
            },
        }
    
    
class SigmaDictHandler:

    def __init__(self):
        self.stack = []
        self.keys = []
        self.buffer = []
        self.detection = {}
    
    def add_condition(self, key: str, condition: dict):
        if len(self.buffer) == 0:
            self.buffer.append({"key" : key, "value" : [condition]})
        elif self.buffer[0].get("key") == key:
            self.buffer[0]["value"].append(condition)
        elif self.buffer[0].get("key") != key:
            print("KEYS DO NOT MATCH ON DICT HANDLER")

    def result(self):
        
        result_list = []
        self.stack = self.buffer
        
        for idx, condition in enumerate(self.stack):
            
            if condition.get("key") is not None:
                result = self.__handle_condition_list(condition.get("key"), condition.get("value"))
                if type(result) == list:    
                    result_list.extend(result)
                elif type(result) == dict:
                    result_list.append(result)
            else:
                result = [self.__handle_dict(x) for x in condition.get("value")]
                if type(result) == list:    
                    result_list.extend(result)
                elif type(result) == dict:
                    result_list.append(result)
        
        self.__clear()

        return result_list
        
    def __handle_dict(self, condition: dict):
        
        term = condition["term"]
        operator = condition["operator"].lower()
        value = condition["value"]

        if operator != "eq":
            term = f"{term}|{operator}"
        else:
            term = term
        result = {term : value}
        return result
    
    def __handle_condition_list(self, key, condition_list: list[dict]):

        if key == "or":

            terms = list(set([x["term"] for x in condition_list]))
            operators = list(set([x["operator"].lower() for x in condition_list]))
            values = [x["value"] for x in condition_list]

            if len(terms) > 1 or len(operators) > 1:
                #print("OR: TERMS OR OPERATORS GREATER THAN 1 - DICT HANDLER")
                result_list = self.__or_terms_or_operators_over_1(condition_list)
                return result_list
            
            if operators[0] != "EQ":
                terms = f"{terms[0]}|{operators[0]}"
            else:
                terms = terms[0]
            result = {terms : values}
            return result
        
        elif key == "and":
            terms = list(set([x["term"] for x in condition_list]))
            operators = list(set([x["operator"].lower() for x in condition_list]))
            values = [x["value"] for x in condition_list]

            if len(terms) > 1 or len(operators) > 1:
                result_list = self.__and_terms_or_operators_over_1(condition_list)
                return result_list
            
            if operators[0] != "eq":
                terms = f"{terms[0]}|{operators[0]}"
            else:
                terms = terms[0]
            if len(values) > 1:
                result = {f"{terms}|all" : values}
            else:
                result = {f"{terms}" : values}
            return result
    
    def __and_terms_or_operators_over_1(self, condition_list: list[dict]):
        result_list = []
        temp = {}

        for entry in condition_list:
            if temp.get(f'{entry.get("term")}{entry.get("operator")}') == None:
                temp[f'{entry.get("term")}{entry.get("operator")}'] = [entry]
            elif f'{entry.get("term")}{entry.get("operator")}' is not None:
                temp[f'{entry.get("term")}{entry.get("operator")}'].append(entry)
        
        for key,condition_list in temp.items():
            terms = list(set([x["term"] for x in condition_list]))
            operators = list(set([x["operator"].lower() for x in condition_list]))
            values = [x["value"] for x in condition_list]
            if len(terms) > 1 or len(operators) > 1:
                print("AND: I DONT KNOW WHAT IM DOING")

            if operators[0] != "eq":
                terms = f"{terms[0]}|{operators[0]}"
            else:
                terms = terms[0]

            if len(values) > 1:
                result = {f"{terms}|all" : values}
            else:
                result = {f"{terms}" : values}
            result_list.append(result)
            print(result_list)
        return result_list
    
    def __or_terms_or_operators_over_1(self, condition_list):

        result_list = []
        temp = {}
        for entry in condition_list:
            if temp.get(f'{entry.get("term")}{entry.get("operator")}') == None:
                temp[f'{entry.get("term")}{entry.get("operator")}'] = [entry]
            elif f'{entry.get("term")}{entry.get("operator")}' is not None:
                temp[f'{entry.get("term")}{entry.get("operator")}'].append(entry)
        
        for key,condition_list in temp.items():
            terms = list(set([x["term"] for x in condition_list]))
            operators = list(set([x["operator"].lower() for x in condition_list]))
            values = [x["value"] for x in condition_list]
            if len(terms) > 1 or len(operators) > 1:
                print("OR: I DONT KNOW WHAT IM DOING")

            if operators[0] != "eq":
                terms = f"{terms[0]}|{operators[0]}"
            else:
                terms = terms[0]
            result = {f"{terms}" : values}
            result_list.append([result])
        return result_list
    
    def __clear(self):
        self.stack = []
        self.keys = []
        self.buffer = []
        self.detection = {}


