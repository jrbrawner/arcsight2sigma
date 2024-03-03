import json
import copy

class ConvertArcSightJSON:

    def __init__(self, conditions):

        self.conditions : dict = conditions
        #print(self.conditions, "\n")
        self.condition_list : list[list] = []
        self.operator_list : list[str] = []
        self.condition_string = self.convert_json_to_string(self.conditions)
        
        self.temp_conditions = []

        for d in conditions["definitions"]:
            self.operator_list.append(conditions["type"])

        #self.testing(self.conditions)
        #if len(self.condition_list) == 0:
        #    self.condition_list.append({"key" : conditions.get("type"), "value" : self.temp_conditions})
        self.condition_list = self.process_definitions(conditions.get("definitions"), conditions.get("type"))
        self.next()
        
    def convert_json_to_string(self, data: dict):

        if data["type"] in ["and", "or"]:
            string = f" {data['type'].upper()} ".join([self.parse_condition(d) for d in data["definitions"]])
            
            return string
        else:
            return self.parse_condition(data)

    def parse_condition(self, condition: dict):

        #print(condition, "\n")
        #base condition
        if condition.get("type") is None:
            return self.parse_basic_condition(condition)

        #list of dicts
        elif condition["type"] in ["and", "or"]:
            string =  f" {condition['type'].upper()} ".join([self.parse_condition(d) for d in condition["definitions"]])
            return string

        #negated condition
        elif condition["type"] == "not":
            string = f"NOT ({self.parse_condition(condition['definitions'][0])})"
            return string

    def parse_basic_condition(self, condition: dict):
        string = f"{condition['term']} {condition['operator']} {condition['value']}"
        return string

    def testing(self, data: dict):
        
        while len(data.get("definitions")) > 0:
            item = data.get("definitions").pop(0)
            if item.get("definitions") is not None:
                #only one condition can be NOT
                self.testing(item)
                if self.temp_conditions != []:
                    #self.operator_list.append(data["type"])
                    self.condition_list.append({"key" : item.get("type"), "value" : self.temp_conditions})
                    self.temp_conditions = []
            else:
                self.temp_conditions.append(item)
                ### additional nested conditions with different logical combination, clear current buffer
                if len(data.get("definitions")) > 0 and data.get("definitions")[0].get("type") is not None:
                    self.condition_list.append({"key" : data.get("type"), "value" : self.temp_conditions})
                    self.temp_conditions = []
    
    def process_definitions(self, definitions, parent_type):
        """Process JSON definitions to build Sigma conditions."""
        conditions = []
        for definition in definitions:
            if 'type' in definition:
                condition = self.process_definitions(definition['definitions'], definition['type'])
                if definition['type'] == 'not':
                    conditions.append(condition)
                else:
                    conditions.append(condition)
            else:
                conditions.append(definition)

        if parent_type == 'and':
            return conditions
        elif parent_type == 'or':
            return conditions
        elif parent_type == 'not':
            return conditions
            
    def next(self):

        for x in self.condition_list:
            print(x)
        print(self.operator_list)
        pass
    
    
    
    
        
