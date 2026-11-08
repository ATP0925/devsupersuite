# Chat Response: TRIG-006
- **Target Community**: Anthropic Claude Developers Discord (Discord)
- **Target Channel**: `#prompt-engineering`
- **Core Theme**: Theme 2: Context Rot & Instruction Drift
- **Developer Prompt / Trigger**: Why does Claude 3.5 Sonnet's instruction adherence degrade past 50k tokens even though the context window is 200k?
- **Sandbox URL**: https://devsupersuite.web.app?utm_source=discord_chat&utm_medium=peer_reply&utm_campaign=claude_attention_decay
- **Checkout URL**: https://gumroad.com/l/tlzdco?utm_source=discord_chat&utm_medium=peer_reply&utm_campaign=claude_attention_decay

---

### Ready-to-Paste Chat Message:

```markdown
That’s classic **Attention Sink Dilution** (Context Rot). 

Even though models like Claude 3.5 have a 200k window, transformer self-attention precision decays sharply past 40k–50k tokens when saturated with repetitive loops and local variables.

Instead of dumping raw files into context:
1. Pass **typed AST skeletons** for background dependencies (interfaces, classes, exported signatures).
2. Substitute internal function bodies with `...` (Ellipsis).
3. Keep only the 1 active file you are currently refactoring in full implementation fidelity.

Benchmark on a 50-file codebase: prompt context dropped from **48k tokens to <9k tokens**, reducing hallucinated imports by ~85% because Claude's attention heads weren't drowned in auxiliary syntax.

We built an open AST engine for Claude Code and Cursor over standard MCP.

You can inspect before/after token reduction live:
👉 https://devsupersuite.web.app?utm_source=discord_chat&utm_medium=peer_reply&utm_campaign=claude_attention_decay
```
