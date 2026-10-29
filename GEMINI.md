# London Local video production

Use the `london-local-video` skill from the existing shared Antigravity skills registry in `.agents/skills.json` for article-to-video production or improvement. Canonical source: https://github.com/krshirkoohi/agent/tree/main/skills/anti-gravity/london-local-video . Sync that checkout through its normal workflow before use. Do not duplicate the skill here.

Keep the existing pipeline and approved baselines. Use `python3 scripts/build_demo.py --spec <candidate> --draft` for unapproved review renders. Drafts write under `build/drafts/` and skip master/demo updates. TTS can use the network; this is not an offline preview command.

Use optional scene `layout` values (`hook`, `receipt`, `key_points`, `facts_figures`, `outro`) to choose order and scene count. Existing specs without layout retain their legacy selection. Per-scene `keyPoints`, `keyPointsHeading` and `takeawayCard` override the global defaults.

Run `python3 -m unittest discover -s tests -v` before committing renderer changes. Check every visible and spoken claim, not just claim flags. Never set approval on behalf of an editor. The metadata render gate is not authenticated approval or proof of factual accuracy. Rendering approved masters can update tracked `demos/` files; publishing needs separate authorisation.
