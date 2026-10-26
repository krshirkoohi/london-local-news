# Stage 2: Generative B-Roll Prompt Library & Guardrails

To scale to **30+ stories per week** while maintaining zero-hallucination journalistic integrity, generative visual models (**Google Veo**, **Google Flow**, **Imagen 3**) are governed by a strict **Atmospheric B-Roll Protocol**.

---

## 🚫 Mandatory Negative Prompts (Anti-Slop & Anti-Deepfake Rules)

Every generative video or still prompt MUST append or enforce the following negative constraints:

> **Negative Prompt:**  
> `no readable signage text, no gibberish lettering, no speaking faces, no lip-syncing, no politicians, no council chamber interiors with fake debates, no protest placards with text, no neon cyberpunk lighting, no oversaturated HDR, no warped hands, no CGI cartoon textures.`

### Why This Matters
1. **No Fake Chamber Footage**: Never generate synthetic councillors voting inside a chamber—that crosses the line into deepfake territory. Use **exterior civic architecture** (stone steps, neoclassical columns, borough coats of arms) paired with a deterministic **Division Tally Figure (`vote_tally`)** overlaid in code.
2. **No Gibberish Text**: Diffusion models garble small street signs and protest banners. Keep camera focus at shallow-to-medium depth of field (`f/2.8–f/4.0`) where architectural stonework or moving London transit is the hero, and render 100% of typography deterministically in Python/PIL.

---

## 🎥 Canonical Camera & Lens Grammar

Every prompt follows a 5-part formula:
`[Shot Type & Camera Movement] + [Architectural / Street Subject] + [Lighting & Weather] + [Film Stock & Lens] + [Aspect Ratio & Frame Rate]`

### Template 1: Civic Authority & Council Steps (`civic_exterior`)
*Used for Scene 1 (The Hook) & Scene 4 (Architectural B-Cam)*
```text
Cinematic 35mm documentary medium-wide shot looking up the Portland stone steps and neoclassical columns of a grand British municipal town hall in Westminster, London. A carved stone British coat of arms above the heavy oak entrance doors. Civil servants and residents in dark tailored coats walking up the steps from behind, faces turned away from camera. Overcast London autumn morning daylight, soft diffused shadows, natural muted colour palette, 24fps, 9:16 vertical.
```

### Template 2: Borough Transit & Street Life (`borough_street_bus`)
*Used for Scene 3 (Demographics, Transport, or Local High Street Context)*
```text
Authentic 35mm street-level documentary footage of Victoria Street in Westminster, London. An iconic red London double-decker bus driving smoothly through the frame past Edwardian Portland stone buildings. Pedestrians in autumn coats walking along the pavement in soft motion blur. Overcast British daylight, Kodak Portra 400 editorial colour grade, realistic motion, 24fps, 9:16 vertical.
```

### Template 3: Monochrome Architectural Still (`monochrome_broadsheet_still`)
*Used for Scene 2 ("Paper-on-Glass" Document & Quote Backdrop)*
```text
High-contrast black and white 35mm street photography of Victoria Street and Westminster City Hall precinct, London. Wet pavement reflections after light rain, classic London streetlamps and neoclassical Portland stone facades in the background, dramatic overcast sky, Ilford HP5 Plus film grain, editorial newspaper photography aesthetic, 9:16 vertical.
```

### Template 4: Municipal Housing & Estates (`housing_retrofit_broll`)
*Used for Housing, Planning, and Retrofit Stories (e.g. Camden / Southwark)*
```text
Documentary 35mm wide-angle shot of a post-war red-brick council housing estate in Camden, London, surrounded by mature plane trees with autumn leaves. Scaffolding on one corner indicating refurbishment work, wet tarmac courtyard, overcast morning light, realistic British documentary cinematography, 24fps, 9:16 vertical.
```

### Template 5: Clean Air & School Streets (`transport_environment_broll`)
*Used for Transport, Cycling, and Clean Air Stories*
```text
Authentic 35mm documentary shot of a residential tree-lined Victorian street in Southwark, London, during morning commuting hours. Cyclists riding smoothly along a designated cycle lane, wet autumn leaves on the kerb, soft overcast daylight, shallow depth of field, realistic motion, 24fps, 9:16 vertical.
```

---

## 🔄 Single-Clip Multi-Angle Reuse ("B-Cam Punch-In")

To maximise credit efficiency (generating **1–2 clips per story** instead of 5), the assembly engine (`scripts/build_demo.py`) supports **declarative camera framing modes** on any video asset:

1. `"cropMode": "full"` (`trimStart: 0.0`): Full 9:16 frame showing street-level movement in the lower half and architecture above.
2. `"cropMode": "architectural_upper"` (`trimStart: 2.5`): Punches 1.35× into the upper neoclassical columns and carved stone coat of arms with a subtle warm-slate editorial grade, creating a distinct "B-Camera" angle from the same master clip without jump-cut repetition.
3. `"cropMode": "pan_zoom"` (on 35mm stills): Smooth 30fps Ken Burns drift (`1.00x → 1.05x`) for document-highlight scenes.
