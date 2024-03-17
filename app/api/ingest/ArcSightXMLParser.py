import xml.etree.ElementTree as ET
import yaml
import json


class ParseArcSightConditonsXML:

    def __init__(self, xml_data: str):
        """Initiate a class that can be used to convert XML ArcSight rules to Python Sigma rule objects

        Args:
            xml_data (str): An ArcSight XML document in str format

        """
        self.xml_data: str = xml_data

        self.rule_name: str = ""
        self.condition_string: str = ""

        self.arcsight_xml_to_sigma(self.xml_data)

    def arcsight_xml_to_sigma(self, xml_string):
        """Convert ArcSight XML rule to Sigma rule."""
        root = ET.fromstring(xml_string)
        self.rule_name = root.attrib["Name"]

        for condition in root.findall(".//Condition"):
            self.parse_condition(condition)

    def parse_basic_condition(self, basic_condition):
        """Parse a basic condition from the ArcSight XML and convert it to Sigma format."""

        # print(basic_condition.tag, basic_condition.attrib)
        operator = basic_condition.attrib["Operator"]
        column = basic_condition.find(".//Variable").attrib.get("Column")
        value = basic_condition.findall(".//Value")

        if operator == "Is":
            operator = "EQ"

        # might be using active list
        resource_reference = basic_condition.find(".//Resource")
        if resource_reference is not None:

            if column == "generator":
                resource_reference = (
                    resource_reference.attrib.get("URI").split("/").pop()
                )
                return f'{column} {operator} "{resource_reference}"'

            if "Filters" in resource_reference.attrib.get("URI"):
                resource_reference = (
                    resource_reference.attrib.get("URI").split("/").pop()
                )
                value = f'MatchesFilter EQ "{resource_reference}"'
            elif "Active Lists" in resource_reference.attrib.get("URI"):
                resource_reference = (
                    resource_reference.attrib.get("URI").split("/").pop()
                )
                value = f'InActiveList EQ "{resource_reference}"'

            column = basic_condition.findall(".//Variable")

            if column is not None:
                if len(column) > 1:
                    column_list = [
                        x.attrib.get("Column")
                        for x in column
                        if x.attrib.get("Column") != None
                    ]
                    column = column_list
                elif len(column) == 1:
                    column = column[0].attrib.get("Column")
                    if column == None:
                        return f"{value}"
            if "ActiveList" in value:
                return f"{column} {value}"
            return f'{column} "{value}"'

        if value is not None:
            if len(value) > 1:
                value_list = [x.text for x in value]
                value = value_list
            elif len(value) == 1:
                value = value[0].text

        elif value is None:
            # might be using variable instead of value
            pass

        return f'{column} {operator} "{value}"'

    def parse_condition(self, condition):
        """Parse a condition (AND, OR, NOT) from ArcSight XML and convert to Sigma format."""
        condition_type = condition.tag
        conditions = []

        for child in condition:
            if child.tag in ["And", "Or", "Not"]:
                conditions.append(self.parse_condition(child))
            elif child.tag == "BasicCondition":
                conditions.append(self.parse_basic_condition(child))

        self.condition_string = conditions[0]

        if condition_type == "And":
            return f"({' AND '.join(conditions)})"
        elif condition_type == "Or":
            return f"({' OR '.join(conditions)})"
        elif condition_type == "Not":
            return f"NOT {conditions[0]}"
        else:
            return ""
