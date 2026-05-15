from app.logging.db_reader import _parse_json


def test_parse_json_handles_invalid() -> None:
    assert _parse_json(None) is None
    assert _parse_json("not-json") is None
    assert _parse_json("{\"a\": 1}") == {"a": 1}
