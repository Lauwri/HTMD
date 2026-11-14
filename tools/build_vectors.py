"""Build HTMD draft semantic conformance vectors. Repository maintenance only."""
import json
from pathlib import Path

CASES = []

def good(case_id, description, source, metadata, references=None, relations=None, profile="core"):
    CASES.append({"id":case_id,"profile":profile,"description":description,"source":source,
                  "valid":True,"expected":{"metadata":{"htmd":"0.1","type":"note",**metadata},
                    "references":references or [],"relations":relations or []}})

def bad(case_id, description, source, code, profile="core"):
    CASES.append({"id":case_id,"profile":profile,"description":description,"source":source,
                  "valid":False,"error":code})

good("core-anonymous", "Anonymous Markdown has defaults", "# Hello\n\nPlain *Markdown*.\n", {})
good("core-relation", "A document owns its outbound relation", "---\nhtmd: \"0.1\"\nid: \"res://examples/device\"\ntype: \"component\"\n---\n\n# Device\n\n<relation type=\"contains\" to=\"res://examples/sensor\" />\n",
     {"id":"res://examples/device","type":"component"},relations=[{"from":"res://examples/device","type":"contains","to":"res://examples/sensor","status":"asserted","line":9}])
good("core-inline-link", "Labeled inline graph link", "See [[res://examples/sensor|sensor]].\n", {},
     references=[{"kind":"link","target":"res://examples/sensor","label":"sensor","line":1}])
good("core-dependencies", "Context, skill and tool are inert references", '<context ref="mem://user/preferences" mode="summary" />\n<skill ref="skill://research/core" />\n<tool ref="tool://browser/search" name="Search" />\n', {},
     references=[{"kind":"context","target":"mem://user/preferences","mode":"summary","line":1},{"kind":"skill","target":"skill://research/core","line":2},{"kind":"tool","target":"tool://browser/search","name":"Search","line":3}])
good("core-local-file", "Local source reference is permitted", '<resource src="./assets/device.svg" name="Diagram" />\n', {},
     references=[{"kind":"resource","target":"./assets/device.svg","name":"Diagram","line":1}])
good("core-multiline", "Multiline directive attributes", '---\nhtmd: "0.1"\nid: "res://examples/controller"\n---\n\n<relation\n  type="reports-to"\n  to="res://examples/sensor"\n  status="inferred"\n/>\n', {"id":"res://examples/controller"},
     relations=[{"from":"res://examples/controller","type":"reports-to","to":"res://examples/sensor","status":"inferred","line":6}])
good("core-code-is-inert", "Code fence does not create a directive", '```htmd\n<tool ref="tool://browser/search" />\n```\n', {})
good("core-fact", "Facts need evidence", '---\nhtmd: "0.1"\nid: "mem://facts/one"\ntype: "fact"\nevidence:\n  - "res://documents/report"\n---\n\nA sourced assertion.\n',
     {"id":"mem://facts/one","type":"fact","evidence":["res://documents/report"]})
good("core-event", "Historical event with timestamps", '---\nhtmd: "0.1"\nid: "mem://events/one"\ntype: "event"\nactor: "res://actors/owner"\noccurred_at: "2026-11-14T08:00:00Z"\nrecorded_at: "2026-11-14T08:01:00Z"\n---\n\nAn event.\n',
     {"id":"mem://events/one","type":"event","actor":"res://actors/owner","occurred_at":"2026-11-14T08:00:00Z","recorded_at":"2026-11-14T08:01:00Z"})
good("core-correction", "Correction points to prior event", '---\nhtmd: "0.1"\nid: "mem://events/two"\ntype: "event"\nactor: "res://actors/owner"\noccurred_at: "2026-11-14T09:00:00Z"\nrecorded_at: "2026-11-14T09:00:05Z"\ncorrects: "mem://events/one"\n---\n\nCorrection.\n',
     {"id":"mem://events/two","type":"event","actor":"res://actors/owner","occurred_at":"2026-11-14T09:00:00Z","recorded_at":"2026-11-14T09:00:05Z","corrects":"mem://events/one"})
good("core-unknown-relation", "Unknown relation predicate is preserved", '---\nhtmd: "0.1"\nid: "res://examples/device"\n---\n<relation type="mounted-next-to" to="res://examples/controller" />\n',
     {"id":"res://examples/device"},relations=[{"from":"res://examples/device","type":"mounted-next-to","to":"res://examples/controller","status":"asserted","line":5}])
good("view-valid", "Safe view with open navigation", '<view id="device-panel">\n  <section><button data-action="open" data-ref="res://examples/device">Open</button></section>\n</view>\n', {}, profile="view")

bad("core-bad-version", "Unsupported source language version", '---\nhtmd: "9.0"\n---\n# Title\n', "E_VERSION")
bad("core-duplicate-key", "Repeated frontmatter key", '---\nhtmd: "0.1"\nid: "res://examples/device"\nid: "res://examples/sensor"\n---\n', "E_FRONTMATTER")
bad("core-implicit-yaml-scalar", "Unquoted scalar is forbidden", '---\nhtmd: "0.1"\ntype: fact\n---\n', "E_FRONTMATTER")
bad("core-bad-type", "Fact without source evidence", '---\nhtmd: "0.1"\nid: "mem://facts/one"\ntype: "fact"\n---\n', "E_TYPE")
bad("core-event-fields", "Event requires actor and both timestamps", '---\nhtmd: "0.1"\nid: "mem://events/one"\ntype: "event"\n---\n', "E_TYPE")
bad("core-incorrect-scheme", "Context needs a memory or resource ID", '<context ref="tool://browser/search" />\n', "E_URI")
bad("core-tool-source", "Tool script paths are invalid", '<tool src="./browser.py" />\n', "E_DIRECTIVE")
bad("core-relation-source", "Anonymous document cannot implicitly originate a relation", '<relation type="contains" to="res://examples/sensor" />\n', "E_RELATION_SOURCE")
bad("core-path-traversal", "Source path cannot escape root", '<resource src="./assets/../secrets.txt" />\n', "E_SOURCE_PATH")
bad("core-malformed-attr", "Semantic attributes must be quoted", '<resource ref=res://examples/device />\n', "E_DIRECTIVE")
bad("core-malformed-link", "Graph links need logical URIs", 'Read [[examples/device]].\n', "E_LINK")
bad("core-invalid-uri", "Logical ID path cannot contain ..", '<resource ref="res://examples/../secrets" />\n', "E_URI")
bad("core-unknown-attribute", "Known directive rejects unknown attributes", '<context ref="mem://user/preferences" execute="yes" />\n', "E_DIRECTIVE")
bad("view-script", "Scripts in a view are invalid", '<view>\n  <script>alert(1)</script>\n</view>\n', "E_VIEW", "view")
bad("view-handler", "Event handlers in views are invalid", '<view>\n  <button onclick="steal()">Go</button>\n</view>\n', "E_VIEW", "view")
bad("view-tool-action", "Only open navigation is allowed", '<view>\n  <button data-action="execute" data-ref="tool://browser/search">Run</button>\n</view>\n', "E_VIEW", "view")
bad("view-unsafe-href", "Javascript URLs forbidden", '<view>\n  <a href="javascript:alert(1)">Bad</a>\n</view>\n', "E_VIEW", "view")

p=Path(__file__).resolve().parent.parent / 'conformance/cases.json'
p.write_text(json.dumps(CASES,indent=2,ensure_ascii=False) + '\n', encoding='utf-8')
print(f'Wrote {len(CASES)} conformance cases to {p}')
