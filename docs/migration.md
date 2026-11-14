# Migration from HTMD 0.1, Markdown and HTML

## HTMD 0.1 to 0.2

Existing valid 0.1 documents remain supported with their original validation. To use custom keys such as `manufacturer` or `tags`, declare `htmd: "0.2"`. No metadata renaming is required: existing `x-*` keys remain valid, and `workspace`/`project` strings remain valid custom values. In 0.2 those two fields can also contain string arrays.

Do not automatically strip `x-` prefixes: an application may rely on those exact names, and renaming could collide with another field or a reserved name. Reserved-field types, required evidence/event fields, identifiers, body syntax, and trust boundaries are unchanged. See [the normative metadata rules](../SPECIFICATION.md#31-metadata-grammar-and-constraints).

A 0.1-only reader cannot read an explicitly declared 0.2 file and should report `E_VERSION`. Downgrading requires validating every custom name and value against 0.1 rules; merely changing the version can make the file invalid. Missing frontmatter continues to imply 0.1, and invalid 0.1 input is never upgraded implicitly.

Do not rewrite immutable event records to change their language version; preserve the original bytes and use the store’s correction/revision policy. This release adds no executable expressions, implicit scalar coercion, or nested metadata objects.

## Markdown to HTMD

Most CommonMark files that avoid HTMD-reserved semantic syntax can be used as anonymous HTMD `note` documents. A first-line standalone `---` is reserved as frontmatter opening and needs migration if it was intended as a thematic break. Give documents a stable ID only when they become graph nodes.

**Before (`notes.md`):**

```md
# Device
See the sensor documentation.
```

**After (`device.htmd`):**

```htmd
---
htmd: "0.2"
id: "res://examples/device"
type: "component"
---

# Device
See [[res://examples/sensor|the sensor]].

<relation type="contains" to="res://examples/sensor" />
```

Do not rewrite every Markdown document automatically. Use semantic references only for content that needs identity or graph connections.

## HTML to HTMD

Existing HTML pages cannot be renamed to `.htmd` with guaranteed preservation of behavior. Scripts, forms, iframes, CSS, and free-form JS events are not allowed in HTMD-View. Convert narrative to Markdown and simple visual sections to a safe `<view>` fragment. Keep complex web applications as independently trusted, permission-controlled application components rather than embedding code inside HTMD knowledge.

## Existing notes to typed records

- Observations with evidence → `fact` (retain citations and uncertainty in body).
- Unverified guesses → `hypothesis`.
- Authored interpretation or an automated system’s opinion → `thought`.
- Historical occurrences → `event` with explicit actor and timestamps.
- Mutable project descriptions → `object`, `component`, or `note`.

A correction to an `event` should be a new linked event, not an edit that erases the original. For old sources with missing provenance, **do not fabricate it**; keep them as `note` or an explicitly unverified hypothesis until sourced.

## Compatibility notes

- HTMD-View is not standard HTML rendered directly in browsers.
- Core supports CommonMark 0.31.2; GitHub extensions such as tables are optional.
- URI schemes are application-private conventions, not routable network endpoints.
- Markdown embedded inside a `<view>` fragment is treated as text, not processed as Markdown.
