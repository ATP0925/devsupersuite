# Charm VHS Terminal Recording Script for DevSuperSuite
# Run: vhs marketing/terminal_demo.tape

Output marketing/assets/terminal_demo.gif
Output marketing/assets/terminal_demo.mp4

Set FontSize 15
Set FontFamily "JetBrains Mono"
Set Width 1200
Set Height 675
Set WindowBar Colorful
Set Theme "Catppuccin Mocha"
Set Padding 24
Set TypingSpeed 35ms

# 1. Initialize offline SCIF mode
Type "devsupersuite --scif-mode --voice-duplex"
Sleep 500ms
Enter
Sleep 1200ms

# 2. Voice input simulation
Type "# [VOICE EVENT] \"Extract lock-free audio ring buffer struct into a standalone crate with tests.\""
Sleep 600ms
Enter
Sleep 1000ms

# 3. Execute AST slicing command
Type "devsupersuite ast-slice --file src/audio_core.rs --target LockFreeAudioRingBuffer"
Sleep 400ms
Enter
Sleep 1500ms

# 4. Run concurrency unit tests
Type "cargo test -p lockfree-audio-ringbuffer"
Sleep 500ms
Enter
Sleep 1800ms

# 5. Pre-commit Shannon entropy scan
Type "git commit -m \"feat(audio): extract zero-alloc ring buffer crate\""
Sleep 500ms
Enter
Sleep 2000ms

# Wrap up preview
Sleep 3000ms
