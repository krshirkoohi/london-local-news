# Agent guidance: London Local News

Read [OCN video improvement system](docs/ocn-video-improvement-plan.md) before planning work on video quality, multimodal review, corrective editing, or the editorial GUI.

- Inspect the current V9 pipeline (`scripts/build_demo.py`, `scripts/reusable_templates.py`, `scripts/production_contract.py`) and existing GitHub issues before modifying anything.
- Preserve factual source attribution, labels for illustrative AI footage (`AI-GENERATED MEDIA`), and human editorial approval.
- Prefer reuse, selective regeneration, structured correction plans, and batched review.

## Broadcast Production & Anti-Slop Standards (Enforced)

1. **British English (`en-GB`) TTS Only:**
   - Primary voice engine: `models/gemini-3.8-flash-tts` using prebuilt British voice `en-gb-advisor-1` (Winchester English) via `client.models.generate_content(..., response_modalities=["AUDIO"])`. Do not pass `system_instruction` to `gemini-3.8-flash-tts` (unsupported by endpoint).
   - Fallback voice engine: `edge-tts` with `en-GB-SoniaNeural` (`--rate=+18%`).
   - **Never** use American voices (`Aoede`, `Puck`, etc.).
2. **Zero Burned-In Captions (`showCaptions: false`):**
   - Keep `"showCaptions": false` across all story specs. Social platforms (TikTok, Reels, Shorts) provide native captions; burned-in subtitles clutter the lower third and collide with source citations.
3. **Phonetic Voiceover Hygiene:**
   - Never feed raw domain strings or URLs (`haveyoursay.tfl.gov.uk`, `londonlocal.news/stories/10441`) directly into `voiceoverText`. Write natural spoken phrases (`"TfL's Have Your Say consultation"`, `"London Local dot news"`) while keeping the visual URL on the card.
4. **Factual Duty-Holder & Outcome Attribution:**
   - Hooks must name the actual duty-holder accurately (e.g., `"Camden Council gets 24 hours to make emergency mould safe"` under Awaab's Law — never imply tenants have 24 hours to fix mould).
   - Match procedural outcomes to the printed minutes (e.g., `"Carried on a show of hands"` when no roll-call division was taken; `"commits to refreshing"` rather than `"has launched"`).
   - Avoid evaluative or sensationalist verbs (`"oppose withdrawing"` rather than `"fight back"`, `"historic transport link"` rather than `"lifeline"`).
5. **100% Real Moving Video B-Roll (`models/gemini-omni-1.1-flash`):**
   - Every scene in `timeline` (Scenes 1–4) must use `visualAsset.type = "video"` pointing to an `.mp4` clip in `assets/generative/`. Static `.png`/`.jpg` plates are prohibited.
   - Generate missing atmospheric or human-impact 9:16 B-roll using `models/gemini-omni-1.1-flash` via the Interactions API (`client.interactions.create(model="gemini-omni-1.1-flash", input=prompt, response_modalities=["video"])`).
   - **Strict Anti-Slop Prompt Guardrails:** Documentary 35mm realism, overcast London daylight, subjects seen from behind or side profile (no speaking faces, no lip-sync, no synthetic politicians, no readable/gibberish signage text).
6. **Outro Geometry & Transition:**
   - The Scene 5 enamel street sign (`render_outro_card` in `scripts/reusable_templates.py`, width `820px`) must be horizontally centred at `x = (1080 - sign_w) // 2` (`130px`) on the `1080x1920` canvas.
   - Scene 5 transitions between the Selling Point slide and the Street Sign slide by dipping through the dark borough map backdrop (`bg_backdrop`) rather than crossfading white text over white text.
