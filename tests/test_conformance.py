import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from htmd import HTMDError, parse

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "conformance/cases.json").read_text())
SCHEMA = json.loads((ROOT / "schemas/htmd-ir.schema.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_official_conformance(case):
    if not case["valid"]:
        with pytest.raises(HTMDError) as exc:
            parse(case["source"], profile=case["profile"])
        assert exc.value.code == case["error"]
        return
    doc = parse(case["source"], profile=case["profile"])
    projection = doc.to_ir()
    assert projection["htmd"] == case["expected"]["metadata"]["htmd"]
    Draft202012Validator(SCHEMA).validate(projection)
    for field in ("metadata", "references", "relations"):
        assert projection[field] == case["expected"][field]
