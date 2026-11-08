# Hacker News Technical Response: Can't the LLM just fetch file bodies on demand? (HN-QA-14)
**Author**: DevSuperSuite Systems Engineering (`engineering@devsupersuite.com`)  
**Compliance**: 100% Brand Anonymity Guaranteed  

### Cynical HN Comment:
> *"If the LLM only gets interfaces, what happens when it actually needs to edit a specific function implementation?"*

### Engineered Systems Response:
That is the optimal workflow! 
1. The repository context window is populated with distilled AST interfaces (-83% tokens), allowing the LLM to understand all cross-module types and architectural boundaries without context rot.
2. When the user instructs: 'Refactor the Stripe checkout webhook in `payment.ts`', the agent requests full file content for *only* that specific file.
3. Result: 1 file with full implementation + 49 files with pure AST interfaces. The agent accomplishes the task with 14,000 tokens instead of 90,000 tokens.

---
*DevSuperSuite Systems Engineering | Local-First Developer Tooling*
