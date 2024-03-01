from sigma.rule import SigmaDetection, SigmaDetections, SigmaLogSource, SigmaRule



class Conditions2Sigma:

    def __init__(self, conditions: dict):
        self.conditions = conditions
        self.recursive_iterate(self.conditions)

        

    
    def recursive_iterate(self, data):
        # Check if the data is a dictionary and contains one of the keys: AND, OR, NOT
        if isinstance(data, dict):
            if data.get("AND") is not None or data.get("OR") is not None or data.get("NOT") is not None:
                for key, value in data.items():
                    print(f"KEY: {key}")  
                    self.recursive_iterate(value)  
            else:
                print(data)
                
        # If the data is a list, iterate over each item in the list and process it
        elif isinstance(data, list):
            for item in data:
                self.recursive_iterate(item)  # Recursively process each item
                
        





    def __check_for_single_condition__(self):

            if len(self.temp_detection_items) >= 1:
                detection = SigmaDetection(detection_items=self.temp_detection_items)
                self.detections.append(detection)

    def __build_sigma_detection__(self):

        if len(self.detections) > 1:
            self.detections.pop()
            
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