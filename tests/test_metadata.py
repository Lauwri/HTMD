"""Version compatibility, metadata preservation, and unchanged trust boundaries."""
import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from htmd import HTMDError, Registry, parse, parse_file, render_html
from htmd.cli import main

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/htmd-ir.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def source(fields, version="0.2", body=""):
    return f'---\nhtmd: "{version}"\n{fields}---\n{body}'


def test_metadata_preserved_in_source_projection_and_cli(tmp_path, capsys):
    text = source('manufacturer: "Example Electronics"\n'
                  'location: "building-a"\npriority: "high"\n'
                  'tags:\n  - "hardware"\n  - "temperature"\n'
                  'owners:\n  - "operations"\n'
                  'workspace:\n  - "lab"\nproject: "inventory"\n'
                  'x-legacy: "retained"\nlabel: "caf\\u00e9\\nnext line"\n')
    doc = parse(text)
    expected = {"htmd": "0.2", "type": "note", "manufacturer": "Example Electronics",
                "location": "building-a", "priority": "high", "tags": ["hardware", "temperature"],
                "owners": ["operations"], "workspace": ["lab"], "project": "inventory",
                "x-legacy": "retained", "label": "café\nnext line"}
    assert doc.source == text
    assert parse(doc.source).metadata == expected
    assert doc.metadata == expected
    projection = json.loads(json.dumps(doc.to_ir(), ensure_ascii=False))
    assert projection["htmd"] == "0.2"
    assert projection["metadata"] == expected
    VALIDATOR.validate(projection)
    path = tmp_path / "custom.htmd"
    path.write_text(text, encoding="utf-8")
    assert main(["parse", str(path)]) == 0
    assert json.loads(capsys.readouterr().out) == projection


@pytest.mark.parametrize("version", ["0.1", "0.2"])
@pytest.mark.parametrize("key", ["htmd", "id", "type", "title", "actor", "occurred_at", "recorded_at", "corrects"])
def test_reserved_fields_cannot_be_overridden_by_custom_arrays(version, key):
    fields = f'{key}:\n  - "value"\n'
    text = f'---\n{fields}---\n' if key == "htmd" else source(fields, version)
    with pytest.raises(HTMDError) as exc:
        parse(text)
    assert exc.value.code == ("E_VERSION" if key == "htmd" else "E_FRONTMATTER")


@pytest.mark.parametrize("key", ["title", "tags", "x-tags", "htmd"])
def test_duplicate_key_location(key):
    text = source(f'{key}: "first"\n{key}: "second"\n')
    with pytest.raises(HTMDError) as exc:
        parse(text)
    assert (exc.value.code, exc.value.line, exc.value.column) == ("E_FRONTMATTER", 3 if key == "htmd" else 4, 1)


@pytest.mark.parametrize("fields,line", [
    ('tags:\n  - true\n', 4), ('tags:\n  - "ok"\n  - ["nested"]\n', 5),
    ('tags:\n  nested: "value"\n', 4), ('tags: "\\uD800"\n', 3),
    ('tags: &anchor "value"\n', 3), ('tags: *anchor\n', 3),
    ('tags: !!str "value"\n', 3), ('tags: |\n  value\n', 3),
    ('Tags: "value"\n', 3), ('tags: "a" "b"\n', 3),
])
def test_malformed_metadata_diagnostics(fields, line):
    with pytest.raises(HTMDError) as exc:
        parse(source(fields))
    assert (exc.value.code, exc.value.line, exc.value.column) == ("E_FRONTMATTER", line, 1)


def test_legacy_unknown_field_location_even_before_version():
    with pytest.raises(HTMDError) as exc:
        parse('---\npriority: "high"\nhtmd: "0.1"\n---\n')
    assert (exc.value.code, exc.value.line, exc.value.column) == ("E_FRONTMATTER", 2, 1)


def test_anonymous_version_unchanged():
    assert parse("# Note\n").to_ir() == {
        "htmd": "0.1", "metadata": {"htmd": "0.1", "type": "note"}, "references": [], "relations": []}


def test_custom_key_grammar_and_quoted_scalars():
    doc = parse(source('a: ""\ncustom_field-2: "true"\nnumber: "42"\nnull: "null"\n'))
    assert doc.metadata == {"htmd": "0.2", "type": "note", "a": "",
                            "custom_field-2": "true", "number": "42", "null": "null"}
    VALIDATOR.validate(doc.to_ir())


@pytest.mark.parametrize("version", ["0.3", "9.0", "", "0.2.0-draft"])
def test_unsupported_versions_in_parser_and_schema(version):
    with pytest.raises(HTMDError) as exc:
        parse(source('manufacturer: "Example"\n', version))
    assert (exc.value.code, exc.value.line, exc.value.column) == ("E_VERSION", 1, 1)
    projection = parse(source("")).to_ir()
    projection["htmd"] = projection["metadata"]["htmd"] = version
    assert not VALIDATOR.is_valid(projection)


@pytest.mark.parametrize("version", ["0.1", "0.2"])
@pytest.mark.parametrize("fields,code", [
    ('type: "unknown"\n', "E_TYPE"),
    ('type: "fact"\nid: "mem://facts/one"\n', "E_TYPE"),
    ('type: "event"\nid: "mem://events/one"\n', "E_TYPE"),
    ('type: "hypothesis"\n', "E_TYPE"), ('type: "thought"\n', "E_TYPE"),
    ('id: "tool://a/b"\n', "E_URI"), ('actor: "tool://a/b"\n', "E_URI"),
    ('corrects: "res://a/b"\n', "E_URI"),
    ('evidence:\n  - "https://["\n', "E_URI"),
    ('occurred_at: "2026-11-14T10:00:00+24:00"\n', "E_TYPE"),
])
def test_reserved_semantics_unchanged(version, fields, code):
    with pytest.raises(HTMDError) as exc:
        parse(source(fields, version))
    assert exc.value.code == code


@pytest.mark.parametrize("profile", ["core", "view"])
def test_custom_metadata_cannot_change_rendering_resolution_or_authorization(profile):
    fields = ('id: "res://devices/sensor"\ntitle: "Sensor"\n'
              'workspace: "private"\nproject:\n  - "admin"\n'
              'permissions:\n  - "allow-all"\nallowed: "true"\n'
              'html: "<script>alert(1)</script>"\nexpression: "${run()}"\n'
              'tool: "tool://browser/search"\ncontext: "mem://private/secret"\n'
              'src: "../../secret"\nprofile: "unsafe"\n'
              'link: "[[res://private/secret]]"\n')
    body = '# Sensor\n<relation type="part-of" to="res://devices/system" />\n'
    doc = parse(source(fields, body=body), profile=profile)
    baseline = parse(source('id: "res://devices/sensor"\ntitle: "Sensor"\n', body=body), profile=profile)
    assert doc.references == []
    assert len(doc.relations) == 1
    assert render_html(doc, full=True) == render_html(baseline, full=True)
    denied = Registry()
    denied.add(doc)
    assert denied.resolve("res://devices/sensor").status == "denied"
    assert denied.resolve("res://devices/unknown").status == "denied"
    assert denied.visible_relations() == []
    checks = []
    def allowed(identifier):
        checks.append(identifier)
        return identifier == "res://devices/sensor"
    registry = Registry(allowed=allowed)
    registry.add(doc)
    assert registry.resolve("res://devices/%73ensor").title == "Sensor"
    assert registry.resolve("res://private/secret").title is None
    assert registry.visible_relations() == []
    assert "res://devices/system" in checks
    assert not any("tool://" in identifier for identifier in checks)
    public = Registry(allowed=lambda _identifier: True)
    public.add(doc)
    assert public.resolve("res://devices/system").status == "unresolved"
    assert public.visible_relations()[0]["asserted_by"] == "res://devices/sensor"


@pytest.mark.parametrize("body,code", [
    ('<resource src="./../private" />', "E_SOURCE_PATH"),
    ('<context ref="tool://a/b" />', "E_URI"),
    ('<tool src="./script.py" />', "E_DIRECTIVE"),
    ('<view>\n<script>alert(1)</script>\n</view>', "E_VIEW"),
])
def test_metadata_cannot_relax_body_validation(body, code):
    with pytest.raises(HTMDError) as exc:
        parse(source('permissions: "admin"\nvalidate: "false"\n', body=body), profile="view")
    assert exc.value.code == code


def test_schema_definition_and_all_example_projections():
    Draft202012Validator.check_schema(SCHEMA)
    for path in sorted((ROOT / "examples").rglob("*.htmd")):
        VALIDATOR.validate(parse_file(path, profile="view").to_ir())


@pytest.mark.parametrize("version", ["0.1", "0.2"])
@pytest.mark.parametrize("key,value", [
    ("title", ["bad"]), ("evidence", "res://a/b"), ("type", "unknown"),
    ("x-value", True), ("x-value", 1), ("x-value", None), ("x-value", {}),
    ("x-value", [1]), ("x-value", [["nested"]]), ("x-value", []),
    ("Bad", "bad"), ("x-trailing\n", "bad"), ("x-😀", "bad"),
])
def test_schema_rejects_invalid_metadata(version, key, value):
    projection = parse(source("", version)).to_ir()
    projection["metadata"][key] = value
    assert not VALIDATOR.is_valid(projection)


@pytest.mark.parametrize("version", ["0.1", "0.2"])
def test_schema_versions_and_existing_graph_constraints(version):
    projection = parse(source("", version)).to_ir()
    other = "0.2" if version == "0.1" else "0.1"
    for field in ("htmd", "metadata"):
        bad = copy.deepcopy(projection)
        if field == "htmd": bad[field] = other
        else: bad[field]["htmd"] = other
        assert not VALIDATOR.is_valid(bad)
    for key, val in [("references", [{"kind": "unknown", "target": "res://a/b", "line": 1}]),
                     ("relations", [{"from": "res://a/b", "to": "res://a/c", "type": "uses", "status": "invalid", "line": 1}])]:
        bad = {**projection, key: val}
        assert not VALIDATOR.is_valid(bad)
    for key, value in [("manufacturer", "Example"), ("workspace", ["lab"]), ("project", ["inventory"])]:
        bad = copy.deepcopy(projection)
        bad["metadata"][key] = value
        assert VALIDATOR.is_valid(bad) == (version == "0.2")
