# Quick start

HTMD is plain UTF-8 text with a `.htmd` extension. It is intended to be read by people and an HTMD-aware program, not directly by a browser.

## 1. Write a note

Create `notes.htmd`:

```htmd
# Weekly notes

- A Markdown heading and list work normally.
- Knowledge can refer to [[res://examples/device|the device assembly]].
```

Without frontmatter, this is an anonymous document of type `note`.

## 2. Give an entity an identity

Create `device.htmd`:

```htmd
---
htmd: "0.1"
id: "res://examples/device"
type: "component"
title: "Device assembly"
---

# Device assembly

A device containing a replaceable sensor module.

<relation type="contains" to="res://examples/sensor" />
```

The document can now be relocated without changing the graph identity `res://examples/device`. The `contains` relation points **outward** from that ID; it does not infer an inverse relation.

## 3. Reference memory and capabilities

```htmd
<context ref="mem://examples/requirements" mode="summary" />
<skill ref="skill://research/core" />
<tool ref="tool://browser/search" />
```

An authorized resolver may choose to fetch approved context. The `summary` mode is a retrieval hint, not guaranteed inclusion. Skills and tools are references to registered capabilities; these lines never execute anything.

## 4. Add a small view

```htmd
<view id="device" name="Device details">
  <section>
    <h2>Device details</h2>
    <button data-action="open" data-ref="res://examples/device">Open device</button>
  </section>
</view>
```

The HTMD-View profile enables only `open` navigation; tool calls and scripting are outside this syntax.

## 5. Record history without overwriting it

Create an `event` document with an immutable ID and explicit timestamps:

```htmd
---
htmd: "0.1"
id: "mem://events/2026-11-14-device-test"
type: "event"
actor: "res://actors/operator"
occurred_at: "2026-11-14T08:00:00Z"
recorded_at: "2026-11-14T08:03:00Z"
---

# Device test

The operator started a test.
```

If the event description turns out to contain an error, create **another** event with a `corrects` pointer. The storage implementation, not the parser, is responsible for protecting the old bytes.

## 6. Examine examples and draft checker

- [`examples/concepts/device.htmd`](../examples/concepts/device.htmd)
- [`examples/knowledge/observation.htmd`](../examples/knowledge/observation.htmd)
- [`examples/knowledge/correction.htmd`](../examples/knowledge/correction.htmd)
- [`examples/ui/device-panel.htmd`](../examples/ui/device-panel.htmd)

Run `python3 tools/check_repository.py`. It validates repository fixtures and simple source conventions; a production implementation must follow the full [specification](../SPECIFICATION.md).
