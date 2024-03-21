from sigma.rule import SigmaDetection, SigmaDetectionItem, SigmaLogSource, SigmaRule, SigmaDetections
from sigma.modifiers import SigmaEndswithModifier, SigmaContainsModifier, SigmaStartswithModifier

class Conditions2Sigma:

    def __init__(self, conditions):

        self.conditions : dict = conditions
        self.condition_list = []

        self.sigma_detection_list : list[SigmaDetection] = []
        self.sigma_detections : SigmaDetections
        self.rule : SigmaRule

        self.condition_list = self.convert_to_sigma_rule(self.conditions)
        
        self.__process_conditions()
        self.__process_detections()
        self.__create_sigma_rule()
       

    def convert_to_sigma_rule(self, condition):

        if condition.get("type") == 'and':
            conditions = [self.convert_to_sigma_rule(definition) for definition in condition['definitions']]
            conditions = self.__preprocess_list(conditions)
            conditions = self.__process_and_conditions(conditions)
            return conditions
            
        elif condition.get("type") == 'or':
            conditions = [self.convert_to_sigma_rule(definition) for definition in condition['definitions']]
            conditions = self.__preprocess_list(conditions)
            conditions = self.__process_or_conditions(conditions)
            return conditions

        elif condition.get("type") == 'not':
            conditions = [self.convert_to_sigma_rule(condition['definitions'][0])]
            return conditions
        else:
            return condition
        
                
    def __process_and_conditions(self, condition_list):

        type_list = [type(x) for x in condition_list]
        
        if dict in type_list and list not in type_list and SigmaDetectionItem not in type_list:
            condition_list = self.__and_dicts_only(condition_list)
            return condition_list
        elif dict in type_list and SigmaDetectionItem in type_list:
            condition_list = self.__and_dicts_and_sigma_detection_items(condition_list)
            return condition_list
        else:
            print("AND CONDITIONS: ", type_list)
            return condition_list

    
    def __process_or_conditions(self, condition_list):
        type_list = [type(x) for x in condition_list]
         
        if dict in type_list and list not in type_list and SigmaDetectionItem not in type_list:
            condition_list = self.__or_dicts_only(condition_list)
            return condition_list
        else:
            print("OR CONDITIONS: ", type_list)
            return condition_list
        
    
    def __and_dicts_and_sigma_detection_items(self, condition_list: list[dict|SigmaDetectionItem]):
        
        for idx, condition in enumerate(condition_list):
            if type(condition) == dict:
                condition_list[idx] = self.__create_sigma_detection_item(condition)

        return condition_list
        
    
    def __and_dicts_only(self, condition_list: list[dict]):
        
        #print("AND_DICTS_ONLY")
        for idx, condition in enumerate(condition_list):
            condition_list[idx] = self.__create_sigma_detection_item(condition)
        
        detection = SigmaDetection(detection_items=condition_list)

        return detection
    
    def __or_dicts_only(self, condition_list: list[dict]):

        #print("OR_DICTS_ONLY")
        terms = list(set([x["term"] for x in condition_list]))
        operators = list(set([x["operator"] for x in condition_list]))
        values = [x["value"] for x in condition_list]

        if len(terms) > 1 or len(operators) > 1:
            print("TERMS OR OPERATORS GREATER THAN 1")

        detection_item = SigmaDetectionItem(
            field=terms[0],
            modifiers=self.__get_modifiers(operators[0], values[0]),
            value=values
        )
        
        return detection_item


    def __process_conditions(self):

        type_list = [type(x) for x in self.condition_list]
        print(type_list)
        
        if SigmaDetection in type_list and list not in type_list and SigmaDetectionItem not in type_list:
            pass
        elif SigmaDetectionItem in type_list:
            self.condition_list = [SigmaDetection(detection_items=self.condition_list)]
        else:
            print("PROCESS CONDITIONS: ", type_list)


    def __process_detections(self):

        detections = {}
        conditions_list = []
        for idx, detection in enumerate(self.condition_list):
            name = f"condition-{idx}"
            detections[name] = detection
            conditions_list.append(name)
        
        self.sigma_detections = SigmaDetections(detections=detections, condition=conditions_list)
    
    def __create_sigma_rule(self):

        logsource = SigmaLogSource("TEST")

        self.rule = SigmaRule(
            title="TEST",
            logsource=logsource,
            detection=self.sigma_detections
        )


    def __create_sigma_detection_item(self, condition: dict):

        detection_item = SigmaDetectionItem(
            field=condition["term"],
            modifiers=self.__get_modifiers(condition["operator"], condition["value"]),
            value=condition["value"]
        )

        return detection_item

    def __preprocess_list(self, condition_list):

        while None in condition_list:
            condition_list.remove(None)
        return condition_list

    def __get_modifiers(self, operator: str, value: str):

        mods = []

        lookup = {
            "Contains" : SigmaContainsModifier,
            "EndsWith" : SigmaEndswithModifier,
            "StartsWith" : SigmaStartswithModifier,
        }

        modifier = lookup.get(operator)

        if modifier is not None:
            mods.append(modifier)
            return mods
        return mods

    def __innermost(self, data):
        
        if type(data) == SigmaDetectionItem or type(data) == SigmaDetection:
            return [data]
        else:
            for item in data:
                if isinstance(item, list):
                    return self.__innermost(item)
                else:
                    continue
            return data
