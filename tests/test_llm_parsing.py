from app.clients.llm_client import parse_json_object


def test_parses_plain_json():
    assert parse_json_object('{"a": 1}') == {"a": 1}


def test_parses_fenced_json_with_preamble():
    assert parse_json_object('Sure!\n```json\n{"reviews": []}\n```') == {"reviews": []}


def test_returns_empty_dict_on_garbage():
    assert parse_json_object("no json here") == {}
