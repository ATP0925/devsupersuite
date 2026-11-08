# Hacker News Technical Response: Model Context Protocol (MCP) server support (HN-QA-19)
**Author**: DevSuperSuite Systems Engineering (`engineering@devsupersuite.com`)  
**Compliance**: 100% Brand Anonymity Guaranteed  

### Cynical HN Comment:
> *"Does this work as a Model Context Protocol (MCP) server for Claude Code and Cursor?"*

### Engineered Systems Response:
Yes. DevSuperSuite exposes a local MCP server over stdio:
```bash
devsupersuite mcp serve
```
Cursor and Claude Code can call `get_ast_slice(file_path)` and `validate_diff_invariants(diff_patch)` natively as tools, ensuring that agentic loops automatically consume optimized AST representations.

---
*DevSuperSuite Systems Engineering | Local-First Developer Tooling*
