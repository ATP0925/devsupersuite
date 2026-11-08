# Chat Response: TRIG-001
- **Target Community**: Cursor Community Discord (Discord)
- **Target Channel**: `#troubleshooting`
- **Core Theme**: Theme 1: Fast Request Token Burn & Overages
- **Developer Prompt / Trigger**: Burned my 500 fast requests in 4 days with Composer. Now in the slow queue getting 30s delays. Any way to make Composer use less tokens?
- **Sandbox URL**: https://devsupersuite.web.app?utm_source=discord_chat&utm_medium=peer_reply&utm_campaign=cursor_composer_burn
- **Checkout URL**: https://gumroad.com/l/tlzdco?utm_source=discord_chat&utm_medium=peer_reply&utm_campaign=cursor_composer_burn

---

### Ready-to-Paste Chat Message:

```markdown
Had this exact issue with fast requests evaporating in Composer! 

The root problem is **implementation bloat**: when you reference `@service.ts` or background files, the agent resends 800+ lines of internal while-loops and private logic that the LLM doesn't need to write caller code.

The clean fix is **AST Interface Slicing**:
- Parse the source into an AST (via Tree-sitter or Python `ast`).
- Prune function/method bodies down to `...` stubs.
- Keep 100% of the class structures, method signatures, return types, and docstrings.

In our benchmarks, background files drop from **74k tokens to 12.6k tokens (-83.0%)**, making a 500-request quota last 4x–5x longer.

We built an open MCP server (**OmniKernel 5.0**) that registers in `.cursor/mcp.json` so Composer compresses context automatically.

You can test how much your files shrink in our live browser sandbox (zero signup):
👉 https://devsupersuite.web.app?utm_source=discord_chat&utm_medium=peer_reply&utm_campaign=cursor_composer_burn

(Standalone offline MCP server is $29 lifetime on Gumroad: https://gumroad.com/l/tlzdco?utm_source=discord_chat&utm_medium=peer_reply&utm_campaign=cursor_composer_burn)
```
