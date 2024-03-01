from sigma.rule import SigmaDetection, SigmaDetections, SigmaLogSource, SigmaRule



class Conditions2Sigma:

    def __init__(self, conditions: dict):
        self.conditions = conditions
        self.temp : list = []
        self.recursive_iterate(self.conditions)
        
    def recursive_iterate(self, data, key=None):
        # Check if the data is a dictionary and contains one of the keys: AND, OR, NOT
        if isinstance(data, dict):
            if data.get("AND") is not None or data.get("OR") is not None or data.get("NOT") is not None:
                if self.temp != []:
                    print(key, self.temp)
                self.temp.clear()
                for key, value in data.items():
                    # KEY - AND, OR, NOT
                    #print(key)
                    self.recursive_iterate(value, key)
            else:
                self.temp.append(data)
                #print(key, self.temp)
                
        # If the data is a list, iterate over each item in the list and process it
        elif isinstance(data, list):
            for item in data:
                self.recursive_iterate(item, key)  # Recursively process each item
                
        
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