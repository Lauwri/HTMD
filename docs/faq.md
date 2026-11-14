# FAQ

### Is HTMD HTML, Markdown, or XML?

It is a **new hybrid format**. The content default is CommonMark, semantic tags use an intentionally limited XML-like syntax, and views contain a restricted HTML fragment. It is **not** parsed as ordinary HTML or XML.

### Can a browser open `.htmd` directly?

Not as a complete interactive HTMD document. It requires conversion by an HTMD-aware renderer. A direct browser load cannot be relied upon for metadata, semantic references, or safe views.

### Do `tool://` and `mem://` access a network service?

No. These are private logical identifiers resolved by an application registry, if supported and authorized. Their names do not identify public network protocols.

### Does `<tool />` invoke a tool?

Never. HTMD's representation layer cannot confer runtime permissions or actions.

### Can a Core reader display views?

It can preserve them as inert content or show an escaped source preview. Only a View-capable renderer can interpret the safe UI subset.

### Why is frontmatter restricted?

Unrestricted YAML includes implicit types, nested structures and alias behavior that add interoperability and security complexity. A narrow string-only subset is easier to implement deterministically.

### Can an application revise stored records?

Mutable knowledge can be revised according to store policy. Historical `event` records must be append-only under an event-integrity store; corrections become new linked records. HTMD syntax alone cannot enforce disk immutability.

### Is this efficient for language models?

It avoids copying large context by using references and leaves ordinary prose in concise Markdown. Actual token savings and retrieval quality are hypotheses to benchmark, not measured performance claims.

### Can it replace a complete application framework?

No. HTMD describes documents and small safe views. Complex web app interaction, workflow planning, authorization, synchronization, and user interfaces belong to the host application and its runtime.
