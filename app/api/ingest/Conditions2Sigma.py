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
                
    def __process_or_conditions(self, condition_list):
        terms = []
        remove = []
        for entry in condition_list:
            if type(entry) == dict:
                terms.append(entry)
                remove.append(entry)

        terms = list(set([x["term"] for x in terms]))
        ## all dicts?
        if len(terms) == 1:
            values = [x["value"] for x in remove]
            operators = list(set([x["operator"] for x in remove]))
            if len(operators) > 1:
                detections = []
                for operator in operators:
                    values = [x["value"] for x in remove if x["operator"] == operator]
                    detection_item = SigmaDetectionItem(
                        field=terms[0],
                        modifiers=self.__get_modifiers(operator, values[0]),
                        value=values
                    )
                    detections.append(detection_item)
                [condition_list.remove(x) for x in remove]
                
                for idx, detection_item in enumerate(detections):
                    detections[idx] = SigmaDetection(detection_items=[detection_item])

                return detections
            else:
                detection_item = SigmaDetectionItem(
                    field=terms[0],
                    modifiers=self.__get_modifiers(operators[0], values[0]),
                    value=values
                )
                [condition_list.remove(x) for x in remove]

                if len(condition_list) > 0:
                    condition_list.insert(0, detection_item)
                    return condition_list
                else:
                    return detection_item

        else:
            #dicts and detection items
            for idx, entry in enumerate(condition_list):
                if type(entry) == dict:
                    detection_item = SigmaDetectionItem(
                        field=entry["term"],
                        modifiers=self.__get_modifiers(entry["operator"], entry["value"]),
                        value=entry["value"]
                    )
                    condition_list.insert(idx, detection_item)
                    condition_list.remove(entry)
            return condition_list

    def __process_and_conditions(self, condition_list):

        if dict in [type(x) for x in condition_list] and list in [type(x) for x in condition_list]:
            for idx, entry in enumerate(condition_list):
                if type(entry) == dict:
                    detection_item = SigmaDetectionItem(
                        field=entry["term"],
                        modifiers=self.__get_modifiers(entry["operator"], entry["value"]),
                        value=entry["value"]
                    )
                    condition_list.insert(idx, detection_item)
                    condition_list.remove(entry)

            temp = []
            [temp.append(x) for x in condition_list if type(x) == SigmaDetectionItem]
            [condition_list.remove(x) for x in temp]
            detection = SigmaDetection(detection_items=temp)
            condition_list.insert(0, detection)
            return condition_list
            
        elif dict in [type(x) for x in condition_list]:
            for idx, entry in enumerate(condition_list):
                if type(entry) == dict:
                    detection_item = SigmaDetectionItem(
                        field=entry["term"],
                        modifiers=self.__get_modifiers(entry["operator"], entry["value"]),
                        value=entry["value"]
                    )
                    condition_list.insert(idx, detection_item)
                    condition_list.remove(entry)
            detection = SigmaDetection(detection_items=condition_list)
            
            return detection
        elif SigmaDetectionItem in [type(x) for x in condition_list] and dict not in [type(x) for x in condition_list]:
            detection = SigmaDetection(detection_items=condition_list)
            return detection
        else:
            return condition_list

    def __process_conditions(self):
        

        for x in self.condition_list.detection_items:
            print(type(x), "\n")

        if type(self.condition_list) == SigmaDetection:
            self.sigma_detection_list.append(self.condition_list)
        elif type(self.condition_list) == SigmaDetectionItem:
            self.sigma_detection_list.append(SigmaDetection(detection_items=[self.condition_list]))
        elif type(self.condition_list) == dict:
            detection_item = SigmaDetectionItem(
                field=self.condition_list["term"],
                modifiers=self.__get_modifiers(self.condition_list["operator"], self.condition_list["value"]),
                value=self.condition_list["value"]
            )
            self.sigma_detection_list.append(SigmaDetection(detection_items=[detection_item]))
        else:
            for conditions in self.condition_list:
                conditions = self.__innermost(conditions)
                for condition in conditions:
                    detection = SigmaDetection(detection_items=[condition])
                    self.sigma_detection_list.append(detection)

    def __process_detections(self):

        detections = {}
        conditions_list = []
        for idx, detection in enumerate(self.sigma_detection_list):
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
