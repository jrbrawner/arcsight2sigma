import copy

class SigmaYamlConverter:

    def __init__(self, condition_data):

        self.condition_data = condition_data
       

        self.final_list : list[dict[str, list]|dict[str, dict]] = []
        
        self.convert_to_sigma_rule(self.condition_data)

    
                
    def convert_to_sigma_rule(self, condition):

        if condition.get("type") == 'and':
            key = "and"
            conditions = [self.convert_to_sigma_rule(definition) for definition in condition['definitions']]
        elif condition.get("type") == 'or':
            conditions = [self.convert_to_sigma_rule(definition) for definition in condition['definitions']]
            key = "or"
        elif condition.get("type") == 'not':
            conditions = [self.convert_to_sigma_rule(condition['definitions'][0])]
            key = "not"
        else:
            return condition
        
        type_list = [type(x) for x in conditions]
        print(conditions)
        """
        if type(None) in type_list and conditions != [None]:
            count = 0
            while type(None) in [type(x) for x in conditions]:
                conditions.remove()
        else:
            self.final_list.append({key : conditions})
        """

        #None -1 on the idx


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

        self.sigma_rule["detection"] = self.detections

        temp = []

        for i in self.sigma_rule["detection"]:
            if i != "condition":
                temp.append(i)
        self.sigma_rule["detection"]["condition"] = temp



    
        

