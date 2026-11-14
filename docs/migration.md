# Migration from Markdown and HTML

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
htmd: "0.1"
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
