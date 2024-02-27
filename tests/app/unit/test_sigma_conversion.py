from fastapi.testclient import TestClient
from app.main import app
from app.api.ingest.ArcSightQueryParser import QueryParser


client = TestClient(app)

def test_single_condition():
    input_data = 'sourceProcessName Contains "thor.exe"' 
    parser = QueryParser(input_data)
    
    rule = parser.rule.to_dict()

    condition_0 = rule.get("detection").get("condition-0")
    assert condition_0 == {'sourceProcessName|contains' : 'thor.exe'}
    