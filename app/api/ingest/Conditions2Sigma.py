from sigma.rule import SigmaDetection, SigmaDetectionItem, SigmaLogSource, SigmaRule, SigmaDetections
from sigma.modifiers import SigmaAllModifier, SigmaEndswithModifier, SigmaContainsModifier, SigmaStartswithModifier

class Conditions2Sigma:

    def __init__(self, conditions):

        self.conditions : dict = conditions
        print(self.conditions, "\n", "\n", "\n")
        
        self.condition_string = self.convert_json_to_string(self.conditions)
        self.conditions_list : list[dict] = []
        self.operator_list : list[str] = []

        self.detections : list[SigmaDetection] = []
        self.sigma_detections : SigmaDetections
        self.rule : SigmaRule

        single_definition = self.__check_for_single_definition(self.conditions)
        
        if single_definition == True:
            self.__build_sigma_detection(self.conditions.get("definitions"), self.conditions.get("type"))
            self.__build_sigma_detections()
            self.__build_sigma_rule()

        else:
            for entry in self.conditions["definitions"]:
                self.conditions_list.append(entry)
                operator = self.conditions.get("type")
                if entry.get("type") == "not":
                    operator += " not"
                self.operator_list.append(operator)

            self.operator_list.pop(0)
        
        self.__parse_conditions(self.conditions_list)
        self.__build_sigma_detection(self.conditions.get("definitions"), self.conditions.get("type"))
        self.__build_sigma_detections()
        self.__build_sigma_rule()
        #print(self.operator_list)
        
        
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

    def __check_for_single_definition(self, conditions):

        flag = True

        for entry in conditions["definitions"]:
            if entry.get("type") != None:
                flag = False
        return flag
    
    def __parse_conditions(self, condition_list):
        
        if isinstance(condition_list, list):
            for entry in condition_list:
                if entry.get("definitions")[0].get("definitions") is None:
                    self.__build_sigma_detection(entry.get("definitions"), entry.get("type"))
                else:
                    while len(entry.get("definitions")) > 0:
                        item = entry.get("definitions").pop(0)
                        self.__parse_conditions(item)
        elif isinstance(condition_list, dict):
            self.__build_sigma_detection(condition_list.get("definitions"), condition_list.get("type"))
                    

    def __build_sigma_detection(self, condition_list: list[dict], operator: str):

        if operator == "or":
            value_list = []
            for condition in condition_list:
                value_list.append(condition["value"][1:-1])
            detection_item = SigmaDetectionItem(
                field=condition_list[0]["term"],
                modifiers=self.__get_sigma_modifiers(condition_list[0]["operator"]),
                value=value_list
            )
            detection = SigmaDetection(detection_items=[detection_item])
            self.detections.append(detection)

    def __build_sigma_detections(self):

        temp = {}
        temp_conditions = []
        for idx, entry in enumerate(self.detections):
            name = f"condition-{idx}"
            temp_conditions.append(name)
            temp[name] = entry

        self.sigma_detections = SigmaDetections(temp, temp_conditions)

    def __build_sigma_rule(self):

        logsource = SigmaLogSource("TEST")

        self.rule = SigmaRule(
            title="TEST",
            logsource=logsource,
            detection=self.sigma_detections,
        )

    def __get_sigma_modifiers(self, operator:str):

        mods = []

        lookup = {
            "StartsWith" : SigmaStartswithModifier
        }

        if lookup.get(operator) is not None:
            mods.append(lookup.get(operator))
        
        return mods


        
            
                
                

    
        
        
            
        

        
    
    
    
    
        
