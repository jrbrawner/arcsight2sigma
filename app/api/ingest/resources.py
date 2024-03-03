from xml.etree import ElementTree as ET
from app.database import get_session
import yaml

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from fastapi import APIRouter

from app.api.ingest.models import ArcSightRuleXML
from app.api.ingest.ArcSightXMLParser import ParseArcSightConditonsXML
from app.api.ingest.Sigma2ES import Sigma2ES
from app.api.ingest.QueryParser import QueryParser
from app.api.ingest.testing import ConvertArcSightJSON

router = APIRouter(prefix="/arcsight", tags=["arcsight"])


@router.get("/TIP-to-db-rules", dependencies=[Depends(get_session)])
def convert_TIP_to_db_rules():

    root = ET.parse("app/resources/Threat Intelligence Platform.xml")

    rules = root.findall("Rule")

    for rule in rules:
        name = rule.attrib.get("name")
        data = ""
        for elem in rule.iter():
            if elem.text != "" and elem.text != None:
                data += elem.text.strip()

        index = data.find("<")
        if index != -1:
            data = data[index:]

        index = data.rfind(">")
        if index != -1:
            data = data[: index + 1]

        file = open(f"app/resources/rules/{name}.xml", encoding="utf-8", mode="w")
        file.write(data)
        file.close()

        converter = ParseArcSightConditonsXML(data)
        rule: ArcSightRuleXML = ArcSightRuleXML.get_by_name(name)
        if rule is None:
            rule = ArcSightRuleXML(
                name=converter.rule_name,
                description=None,
                raw=data,
                logic=converter.condition_string,
            )
            rule.save()
        else:
            rule.logic = converter.condition_string
            rule.save()

    return "Done"


@router.get("/testing-conversion", dependencies=[Depends(get_session)])
def testing_conversion(rule: str = None):

    if rule is None:
        rules = ArcSightRuleXML.get_all()
        rule = rules[4]

        converter = QueryParser(rule.logic.replace(" In ", " Contains "))
    else:
        converter = QueryParser(rule)

        #converter1 = Conditions2Sigma(converter.condition_data)

        converter1 = ConvertArcSightJSON(converter.condition_data)
        #return converter.condition_data
        return PlainTextResponse(converter1.condition_string)
    

    #test = Sigma2ES(converter.rule, converter.logical_operators)
    #return PlainTextResponse(test.query)
    #return converter.rule.to_dict()
    
    #return PlainTextResponse(yaml.dump(converter.rule.to_dict()))
