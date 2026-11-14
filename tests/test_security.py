import pytest
from htmd import HTMDError, Registry, parse, render_html
from htmd.parser import validate_uri, validate_src


@pytest.mark.parametrize("uri", [
    "res://a/..", "res://a/%2Fsecret", "res://a/%5Cevil", "res://a/%00",
    "res://a/%GG", "res://a/%FF", "res://a//b", "res://a/path?q=1",
    "res://a/path#x", "res://a:8080/p", "Res://a/p", "res://A/p", "res://a/%2e%2e",
    "file:///etc/passwd", "http://example.com", "res://a/path/",
])
def test_uris_reject_unsafe(uri):
    with pytest.raises(ValueError): validate_uri(uri)


@pytest.mark.parametrize("path", ["../secret", "./x/../secret", "./x//a", "./a\\b", "./%2e%2e/a", "/etc/passwd"])
def test_source_paths_reject_traversal(path):
    with pytest.raises(ValueError): validate_src(path)


def test_source_file_not_loaded():
    d = parse('<resource src="./missing.txt" />\n')
    assert d.references[0]["target"] == "./missing.txt"


def test_code_fence_and_inline_code_are_inert():
    d = parse('`[[res://a/b]]`\n\n```htmd\n<tool ref="tool://bad/execute" />\n```\n')
    assert d.references == []


def test_list_and_quote_directives_are_inert():
    d = parse('- item\n  <tool ref="tool://a/x" />\n\n> <tool ref="tool://a/y" />\n')
    assert d.references == []


def test_html_comment_directives_are_inert():
    d = parse('<!--\n<tool ref="tool://a/x" />\n-->\n')
    assert d.references == []


def test_consecutive_directives():
    d = parse('<tool ref="tool://a/x" />\n<skill ref="skill://a/y" />\n')
    assert [r["kind"] for r in d.references] == ["tool", "skill"]


def test_safe_rendering_of_raw_markdown_html():
    doc = parse('<script>alert(1)</script>\n\n[[res://a/b|label]]\n')
    html = render_html(doc)
    assert '<script>' not in html
    assert '&lt;script&gt;' in html
    assert 'data-ref="res://a/b"' in html


@pytest.mark.parametrize("fragment", [
    '<img src=x onerror=alert(1)>', '<script>alert(1)</script>',
    '<a href="javascript:alert(1)">x</a>', '<a href="data:text/html,hi">x</a>',
    '<button data-action="execute" data-ref="tool://a/b">Run</button>',
    '<button onclick="alert(1)">x</button>',
    '<a href="//attacker.example">bad</a>', '<a href="../admin">bad</a>',
    '<svg onload="alert(1)"></svg>', '<div><span>broken</div>',
])
def test_unsafe_view_rejected(fragment):
    with pytest.raises(HTMDError) as exc:
        parse(f'<view>\n{fragment}\n</view>\n', profile="view")
    assert exc.value.code == "E_VIEW"


def test_core_keeps_unsafe_view_inert():
    doc = parse('<view>\n<script>alert(1)</script>\n</view>\n', profile="core")
    assert "<script>" not in render_html(doc)
    assert "View requires" in render_html(doc)


def test_safe_view_and_no_execution():
    d = parse('<view>\n<section><button data-action="open" data-ref="res://a/b">Open</button></section>\n</view>', profile="view")
    rendered = render_html(d)
    assert 'data-action="open"' in rendered
    assert '<script' not in rendered


def test_registry_denied_by_default_even_for_known():
    d = parse('---\nhtmd: "0.1"\nid: "res://a/b"\n---\n')
    reg = Registry()
    reg.add(d)
    assert reg.resolve("res://a/b").status == "denied"
    assert reg.resolve("res://a/unknown").status == "denied"


def test_registry_allowed_and_unresolved():
    d = parse('---\nhtmd: "0.1"\nid: "res://a/b"\ntitle: "B"\n---\n')
    reg = Registry(allowed=lambda _id: True)
    reg.add(d)
    assert reg.resolve("res://a/b").title == "B"
    assert reg.resolve("res://a/c").status == "unresolved"
    with pytest.raises(ValueError): reg.add(d)


def test_invalid_utf8():
    with pytest.raises(HTMDError) as exc: parse(b"\xff")
    assert exc.value.code == "E_ENCODING"


def test_strict_metadata_rejects_unquoted():
    with pytest.raises(HTMDError): parse('---\nhtmd: "0.1"\ntitle: plain\n---\n')


def test_registry_canonical_percent_uri():
    doc = parse('---\nhtmd: "0.1"\nid: "res://a/%64evice"\n---\n')
    reg = Registry(allowed=lambda _id: True)
    reg.add(doc)
    assert reg.resolve("res://a/device").status == "resolved"


def test_escaped_graph_link_is_not_semantic():
    doc = parse(r'\[[res://a/b]]' + "\n")
    assert doc.references == []


def test_markdown_html_block_directives_are_inert():
    d = parse('<div>\n<tool ref="tool://a/unsafe" />\n</div>\n')
    assert d.references == []


def test_view_html_link_html_entity_scheme_obfuscation_rejected():
    with pytest.raises(HTMDError) as exc:
        parse('<view>\n<a href="java&#115;cript:alert(1)">x</a>\n</view>\n', profile="view")
    assert exc.value.code == "E_VIEW"


def test_unescaped_second_label_pipe_rejected():
    with pytest.raises(HTMDError) as exc:
        parse('[[res://a/x|two|pipes]]')
    assert exc.value.code == "E_LINK"


def test_escaped_label_pipe_preserved():
    doc = parse(r'[[res://a/x|two\|pipes]]')
    assert doc.references[0]["label"] == "two|pipes"


def test_comment_in_code_fence_does_not_shadow_later_directive():
    doc = parse('```\n<!--\n```\n\n<tool ref="tool://a/b" />\n')
    assert len(doc.references) == 1


def test_registry_authorizes_canonical_identifiers():
    doc = parse('---\nhtmd: "0.1"\nid: "res://a/private"\ntitle: "Secret"\n---')
    reg = Registry(allowed=lambda identifier: identifier != 'res://a/private')
    reg.add(doc)
    result = reg.resolve('res://a/%70rivate')
    assert result.status == 'denied'
    assert result.title is None


@pytest.mark.parametrize('denied', ['res://a/private', 'res://a/source', 'res://a/target'])
def test_registry_relations_authorize_canonical_identifiers(denied):
    doc = parse('---\nhtmd: "0.1"\nid: "res://a/%70rivate"\n---\n'
                '<relation from="res://a/%73ource" type="contains" to="res://a/%74arget" />')
    reg = Registry(allowed=lambda identifier: identifier != denied)
    reg.add(doc)
    assert reg.visible_relations() == []


def test_malformed_view_url_is_view_diagnostic():
    with pytest.raises(HTMDError) as exc:
        parse('<view>\n<a href="https://[">x</a>\n</view>', profile='view')
    assert exc.value.code == 'E_VIEW'
