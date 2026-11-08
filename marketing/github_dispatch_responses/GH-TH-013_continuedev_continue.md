# GitHub Technical Response: GH-TH-013
- **Target Repository**: `continuedev/continue`
- **Discussion URL**: https://github.com/continuedev/continue/discussions/1540
- **Category**: Category D: Cloud Latency in Voice-Assisted Coding
- **Thread Title**: High latency (1.5s+) with cloud voice dictation in IDEs breaking flow state
- **Author**: @ergonomic-dev
- **Tracked Sandbox**: https://devsupersuite.web.app?utm_source=github_dispatcher&utm_medium=issue_reply&utm_campaign=continuedev_continue
- **Tracked Checkout**: https://gumroad.com/l/tlzdco?utm_source=github_dispatcher&utm_medium=issue_reply&utm_campaign=continuedev_continue

---

### 📋 Ready-to-Paste Response Payload:

```markdown
### DSP Audio Pipeline: Sub-110ms Local Duplex Voice Coding

Cloud voice dictation fails in pair-programming workflows for two reasons:
1. **Network Roundtrip Latency**: 1.5s–2.0s delay breaks thought-to-code velocity.
2. **Lack of Acoustic Echo Cancellation (AEC) & Barge-In**: Assistant audio loops back into the microphone, and the user cannot interrupt mid-output.

#### Local Duplex Architecture:
We engineered **Live Voice Responder**:
- **Sub-110ms DSP Pipeline**: Runs speech processing locally on CPU/GPU without cloud roundtrips.
- **Acoustic Echo Cancellation (AEC)**: Filters mechanical keyboard switches and assistant speaker audio loopback.
- **Instant Audio Barge-In**: Say *"CROW"* or tap `F8` to kill the audio buffer in under 15ms.
- **Targeted Window Injection**: Automatically targets active IDE windows (Cursor, VS Code, Claude Code), pastes prompts, and hits Enter.

Live interactive demonstration & feature matrix:
👉 [https://devsupersuite.web.app?utm_source=github_dispatcher&utm_medium=issue_reply&utm_campaign=continuedev_continue](https://devsupersuite.web.app?utm_source=github_dispatcher&utm_medium=issue_reply&utm_campaign=continuedev_continue)

Included in DevSuperSuite ($29 Pro Lifetime):
👉 [https://gumroad.com/l/tlzdco?utm_source=github_dispatcher&utm_medium=issue_reply&utm_campaign=continuedev_continue](https://gumroad.com/l/tlzdco?utm_source=github_dispatcher&utm_medium=issue_reply&utm_campaign=continuedev_continue)
```
