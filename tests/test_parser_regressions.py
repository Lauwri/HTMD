import pytest

from htmd import HTMDError, parse, render_html


def test_multiline_code_span_keeps_directive_inert():
    doc = parse('`code\n<tool ref="tool://a/b" />\ncode`')
    assert doc.references == []
    assert '<code>' in render_html(doc)


def test_inline_code_comment_does_not_hide_directive():
    doc = parse('`<!--`\n\n<tool ref="tool://a/b" />')
    assert [r['target'] for r in doc.references] == ['tool://a/b']


def test_directive_can_follow_paragraph_text():
    doc = parse('text\n<tool ref="tool://a/b" />')
    assert [r['target'] for r in doc.references] == ['tool://a/b']


@pytest.mark.parametrize('prefix', ['', 'text\n'])
def test_view_contents_do_not_change_following_markdown(prefix):
    doc = parse(prefix + '<view>\n\n```\n</view>\n\n<tool ref="tool://a/b" />')
    assert [r['target'] for r in doc.references] == ['tool://a/b']


def test_html_block_after_directive_keeps_nested_directive_inert():
    doc = parse('<tool ref="tool://a/b" />\n<div>\n<tool ref="tool://a/c" />\n</div>')
    assert [r['target'] for r in doc.references] == ['tool://a/b']


@pytest.mark.parametrize('tag', ['tool', 'skill', 'resource', 'context', 'relation', 'view'])
def test_unmatched_closing_tag_is_diagnostic(tag):
    with pytest.raises(HTMDError) as exc:
        parse(f'</{tag}>\n')
    assert exc.value.code == ('E_VIEW' if tag == 'view' else 'E_DIRECTIVE')


def test_graph_label_can_end_with_escaped_backslash():
    doc = parse(r'[[res://a/b|slash\\]]')
    assert doc.references[0]['label'] == 'slash\\'


def test_even_backslashes_do_not_escape_label_separator():
    with pytest.raises(HTMDError) as exc:
        parse(r'[[res://a/b|slash\\|pipe]]')
    assert exc.value.code == 'E_LINK'


@pytest.mark.parametrize('separator', ['\u2028', '\u2029', '\x85', '\v', '\f'])
def test_unicode_separators_do_not_create_directive_lines(separator):
    doc = parse('paragraph' + separator + '<tool ref="tool://a/b" />')
    assert doc.references == []


def test_invalid_unicode_string_is_encoding_diagnostic():
    with pytest.raises(HTMDError) as exc:
        parse('\ud800')
    assert exc.value.code == 'E_ENCODING'


def test_malformed_evidence_url_is_uri_diagnostic():
    with pytest.raises(HTMDError) as exc:
        parse('---\nhtmd: "0.1"\nevidence:\n  - "https://["\n---')
    assert exc.value.code == 'E_URI'


def test_invalid_unicode_escape_in_metadata_is_diagnostic():
    with pytest.raises(HTMDError) as exc:
        parse('---\nhtmd: "0.1"\ntitle: "\\uD800"\n---')
    assert exc.value.code == 'E_FRONTMATTER'


@pytest.mark.parametrize('offset', ['+01:99', '-01:60', '+24:00'])
def test_timestamp_rejects_invalid_offset_components(offset):
    with pytest.raises(HTMDError) as exc:
        parse(f'---\nhtmd: "0.1"\noccurred_at: "2026-11-14T10:00:00{offset}"\n---')
    assert exc.value.code == 'E_TYPE'


def test_invalid_graph_link_reports_source_line_and_column():
    with pytest.raises(HTMDError) as exc:
        parse('---\nhtmd: "0.1"\n---\n# title\n\ntext\nprefix [[broken]]')
    assert exc.value.code == 'E_LINK'
    assert (exc.value.line, exc.value.column) == (7, 8)


def test_graph_link_in_image_alt_is_extracted_and_rendered():
    doc = parse('text\n\n![see\n[[res://a/b|label]]](a.png)')
    assert doc.references == [{'kind': 'link', 'target': 'res://a/b', 'label': 'label', 'line': 4}]
    assert 'alt="see\nlabel"' in render_html(doc)
