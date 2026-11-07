from PIL import Image, ImageDraw, ImageFont

w, h = 1200, 630
img = Image.new('RGB', (w, h), color=(0, 0, 0)) # Pure pitch black
draw = ImageDraw.Draw(img)

# Technical high-contrast grid lines
for x in range(0, w, 50):
    draw.line([(x, 0), (x, h)], fill=(20, 20, 20), width=1)
for y in range(0, h, 50):
    draw.line([(0, y), (w, y)], fill=(20, 20, 20), width=1)

# Outer industrial orange frame
draw.rectangle([20, 20, w-20, h-20], outline=(255, 85, 0), width=2)
draw.rectangle([24, 24, w-24, h-24], outline=(35, 35, 35), width=1)

# Corner markers
for cx, cy in [(20, 20), (w-20, 20), (20, h-20), (w-20, h-20)]:
    draw.rectangle([cx-8, cy-8, cx+8, cy+8], fill=(255, 85, 0))

# Fonts
font_title = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 58)
font_subtitle = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 24)
font_card_head = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 24)
font_card_body = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 17)
font_mono = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 16)
font_badge = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 14)

# Top Badge: [ DEV_SUITE // SYSTEM_V1.0_PROD ]
draw.rectangle([60, 50, 430, 85], fill=(15, 15, 15), outline=(255, 85, 0), width=1)
draw.text((75, 58), '⚡ DEV_SUITE // SYSTEM_V1.0_PROD', fill=(255, 85, 0), font=font_badge)

# Title: DevSuperSuite in Stark White + Electric Orange
draw.text((60, 105), 'DEVSUPERSUITE', fill=(255, 255, 255), font=font_title)
draw.rectangle([515, 115, 680, 155], fill=(255, 85, 0))
draw.text((530, 120), 'OFFICIAL', fill=(0, 0, 0), font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 28))

# Subtitle
draw.text((60, 178), 'Zero-Latency Hands-Free Voice Coding + Pre-Commit API Key Entropy Guard', fill=(220, 220, 220), font=font_subtitle)
draw.text((60, 212), 'Direct hardware-grade acceleration for Cursor, Claude Code, and VS Code.', fill=(130, 130, 130), font=font_card_body)

# Two High-Contrast Cards
# Card 1: Voice Engine
draw.rectangle([60, 260, 560, 510], fill=(10, 10, 10), outline=(50, 50, 50), width=2)
draw.rectangle([60, 260, 560, 305], fill=(20, 20, 20), outline=(50, 50, 50), width=1)
draw.text((80, 273), '01 // LIVE VOICE RESPONDER', fill=(255, 85, 0), font=font_card_head)
draw.text((80, 330), '• WebRTC Full-Duplex Acoustic Cancellation (-44dB)', fill=(240, 240, 240), font=font_card_body)
draw.text((80, 365), '• 110ms Ultra-Low Neural Latency Voice Pipeline', fill=(240, 240, 240), font=font_card_body)
draw.text((80, 400), '• Deterministic Voice Barge-In ("CROW" / F8 Cutoff)', fill=(240, 240, 240), font=font_card_body)
draw.rectangle([80, 450, 480, 485], fill=(0, 0, 0), outline=(255, 85, 0), width=1)
draw.text((95, 458), 'AUDIO PIPELINE: ACTIVE // FULL-DUPLEX', fill=(255, 85, 0), font=font_mono)

# Card 2: AgentShield Guard
draw.rectangle([600, 260, 1100, 510], fill=(10, 10, 10), outline=(50, 50, 50), width=2)
draw.rectangle([600, 260, 1100, 305], fill=(20, 20, 20), outline=(50, 50, 50), width=1)
draw.text((620, 273), '02 // AGENTSHIELD ENTROPY GUARD', fill=(255, 255, 255), font=font_card_head)
draw.text((620, 330), '• Real-Time Shannon Information Density Filter', fill=(240, 240, 240), font=font_card_body)
draw.text((620, 365), '• Pre-Commit Hook Intercepts OpenAI/Stripe/AWS Keys', fill=(240, 240, 240), font=font_card_body)
draw.text((620, 400), '• 100% Offline Zero-Knowledge Local Scan', fill=(240, 240, 240), font=font_card_body)
draw.rectangle([620, 450, 1020, 485], fill=(0, 0, 0), outline=(255, 255, 255), width=1)
draw.text((635, 458), 'SHANNON ENTROPY: H(X) > 3.8 BITS [BLOCKED]', fill=(255, 255, 255), font=font_mono)

# Footer bar
draw.line([(60, 545), (1100, 545)], fill=(40, 40, 40), width=1)
draw.text((60, 565), 'URL: https://atp0925.github.io/devsupersuite/', fill=(255, 85, 0), font=font_mono)
draw.text((680, 565), 'LIFETIME ACCESS: $29 // UPI: ₹1,499', fill=(255, 255, 255), font=font_mono)

img.save('C:/Users/atpad/.gemini/antigravity/scratch/agent-commerce/og-image.png')
img.save('C:/Users/atpad/.gemini/antigravity/scratch/agent-commerce/landing_page/og-image.png')
print('High-contrast Black/White/Orange og-image.png generated.')

