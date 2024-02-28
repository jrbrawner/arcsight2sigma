from fastapi.testclient import TestClient
from app.main import app
from app.api.ingest.QueryParser import QueryParser


client = TestClient(app)

def test_single_condition():
    input_data = 'sourceProcessName Contains "thor.exe"' 
    parser = QueryParser(input_data)
    
    rule = parser.rule.to_dict()

    condition_0 = rule.get("detection").get("condition-0")
    assert condition_0 == {'sourceProcessName|contains' : 'thor.exe'}
    
def test_complex_rule():
    input_data = r'''
    (((((fileName ENDSWITH "\Appdata\Local\Microsoft\Windows\WebCache\WebCacheV01.dat") OR ((fileName ENDSWITH "\cookies.sqlite" OR fileName ENDSWITH "release\key3.db" OR fileName ENDSWITH "release\key4.db" OR fileName ENDSWITH "release\logins.json"))
    OR ((fileName CONTAINS "\Appdata\Local\Chrome\User Data\Default\Login Data" OR fileName CONTAINS "\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies" OR fileName CONTAINS "\AppData\Local\Google\Chrome\User Data\Local State"))))
    AND NOT ((((sourceProcessName = "System")) OR (((sourceProcessName CONTAINS ":\Program Files\" OR sourceProcessName CONTAINS ":\Program Files (x86)\" OR sourceProcessName CONTAINS ":\WINDOWS\system32\" OR sourceProcessName CONTAINS ":\WINDOWS\SysWOW64\")))))) 
    AND  NOT ((((sourceProcessName CONTAINS ":\ProgramData\Microsoft\Windows Defender\" AND (sourceProcessName ENDSWITH "\MpCopyAccelerator.exe" OR sourceProcessName ENDSWITH "\MsMpEng.exe")))
    OR (((sourceProcessName ENDSWITH "\thor64.exe" OR sourceProcessName ENDSWITH "\thor.exe"))))))'''

    parser = QueryParser(input_data)

    rule = parser.rule.to_dict()

    print(rule)