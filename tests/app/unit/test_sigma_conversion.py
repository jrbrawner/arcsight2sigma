from fastapi.testclient import TestClient
from app.main import app
from app.api.ingest.QueryParser import QueryParser


client = TestClient(app)

def test_simple_rule():
    input_data = 'sourceProcessName Contains "thor.exe"' 
    parser = QueryParser(input_data)
    
    rule = parser.rule.to_dict()

    condition_0 = rule.get("detection").get("condition-0")
    assert condition_0 == {'sourceProcessName|contains' : 'thor.exe'}


def test_simple_or_rule():

    input_data = '(sourceProcessName Contains "thor.exe" OR sourceProcessName Contains "thor64.exe")'
    
    parser = QueryParser(input_data)

    rule = parser.rule.to_dict()

    condition_0 = rule.get("detection").get("condition-0")

    assert condition_0 == {'sourceProcessName|contains' : ['thor.exe', 'thor64.exe']}

def test_simple_and_rule():

    input_data = '(sourceProcessName Contains "thor.exe" AND sourceProcessName Contains "thor64.exe")'

    parser = QueryParser(input_data)

    rule = parser.rule.to_dict()

    condition_0 = rule.get("detection").get("condition-0")

    assert condition_0 == {'sourceProcessName|contains|all' : ['thor.exe', 'thor64.exe']}

def test_complex_rule():

    input_data = r'(((((fileName ENDSWITH "\Appdata\Local\Microsoft\Windows\WebCache\WebCacheV01.dat") OR ((fileName ENDSWITH "\cookies.sqlite" OR fileName ENDSWITH "release\key3.db" OR fileName ENDSWITH "release\key4.db" OR fileName ENDSWITH "release\logins.json")) OR ((fileName CONTAINS "\Appdata\Local\Chrome\User Data\Default\Login Data" OR fileName CONTAINS "\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies" OR fileName CONTAINS "\AppData\Local\Google\Chrome\User Data\Local State")))) AND  NOT ((((sourceProcessName = "System")) OR (((sourceProcessName CONTAINS ":\Program Files\" OR sourceProcessName CONTAINS ":\Program Files (x86)\" OR sourceProcessName CONTAINS ":\WINDOWS\system32\" OR sourceProcessName CONTAINS ":\WINDOWS\SysWOW64\")))))) AND  NOT ((((sourceProcessName CONTAINS ":\ProgramData\Microsoft\Windows Defender\" AND (sourceProcessName ENDSWITH "\MpCopyAccelerator.exe" OR sourceProcessName ENDSWITH "\MsMpEng.exe"))) OR (((sourceProcessName ENDSWITH "\thor64.exe" OR sourceProcessName ENDSWITH "\thor.exe"))))))'

    parser = QueryParser(input_data)

    rule = parser.rule.to_dict()

    condition_0 = rule.get("detection").get("condition-0")
    condition_1 = rule.get("detection").get("condition-1")
    condition_2 = rule.get("detection").get("condition-2")
    condition_3 = rule.get("detection").get("condition-3")
    condition_4 = rule.get("detection").get("condition-4")
    condition_5 = rule.get("detection").get("condition-5")
    condition_6 = rule.get("detection").get("condition-6")
    
    assert condition_0 == {'fileName|endswith': '\\Appdata\\Local\\Microsoft\\Windows\\WebCache\\WebCacheV01.dat'}
    assert condition_1 == {'fileName|endswith': ['\\cookies.sqlite', 'release\\key3.db', 'release\\key4.db', 'release\\logins.json']}
    assert condition_2 == {'fileName|contains': ['\\Appdata\\Local\\Chrome\\User Data\\Default\\Login Data',\
                                                '\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Network\\Cookies', '\\AppData\\Local\\Google\\Chrome\\User Data\\Local State']}
    assert condition_3 == {'sourceProcessName' : 'System'}
    assert condition_4 == {'sourceProcessName|contains': [':\\Program Files\\', ':\\Program Files (x86)\\', ':\\WINDOWS\\system32\\', ':\\WINDOWS\\SysWOW64\\']}
    assert condition_5 == {'sourceProcessName|contains': ':\\ProgramData\\Microsoft\\Windows Defender\\', 'sourceProcessName|endswith': ['\\MpCopyAccelerator.exe', '\\MsMpEng.exe']}
    assert condition_6 == {'sourceProcessName|endswith': ['\\thor64.exe', '\\thor.exe']}

def test_complex_rule_1():
    input_data = r'(deviceEventCategory = "RoleManagement" AND (OperationName CONTAINS "Add") AND (OperationName CONTAINS "member to role") AND (TargetResources CONTAINS "7698a772-787b-4ac8-901f-60d6b08affd2" OR TargetResources CONTAINS "62e90394-69f5-4237-9190-012177145e10"))'

    parser = QueryParser(input_data)

    rule = parser.rule.to_dict()

    condition_0 = rule.get("detection").get("condition-0")
    condition_1 = rule.get("detection").get("condition-1")
    