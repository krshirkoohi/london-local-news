# London Local: Modular Multi-Story News Video Pipeline (V9)

[![Build News Video Demo](https://github.com/krshirkoohi/london-local-news/actions/workflows/render.yml/badge.svg)](https://github.com/krshirkoohi/london-local-news/actions/workflows/render.yml)
[![DAG Tracking](https://img.shields.io/badge/DAG_Board-Project_%2311-blue?logo=github)](https://github.com/users/krshirkoohi/projects/11)
[![Format](https://img.shields.io/badge/Format-1080x1920_30fps_9%3A16-purple)](#)
[![Identity](https://img.shields.io/badge/Brand-London_Local.-FF5238)](#)

An industrial, declarative short-form news video generation engine built for [London Local](https://londonlocal.news/) (covering civic decisions across Greater London's 33 councils).

Engineered to scale newsroom throughput to **30+ verified stories per week with a single human editor**, while enforcing strict factual traceability, zero synthetic deepfakes, and 100% declarative multi-story rendering.

---

## 📺 Live Broadcast Video Demos (Click to Watch in Browser)

| Borough & Story | Council Focus | Direct In-Repo Player (1080×1920 @ 30fps) | Direct Download |
| :--- | :--- | :--- | :--- |
| **Westminster City Council (#4178)** | 54–0 Unanimous Motion Against Far-Right Extremism | [▶️ **Watch Westminster Reel**](https://github.com/krshirkoohi/london-local-news/blob/main/demos/westminster_4178_broadcast.mp4) | [Download MP4](https://github.com/krshirkoohi/london-local-news/releases/download/v1.0.0/westminster_4178_broadcast.mp4) |
| **London Borough of Camden (#4182)** | £4.2M Warm Homes Council Estate Retrofit Programme | [▶️ **Watch Camden Reel**](https://github.com/krshirkoohi/london-local-news/blob/main/demos/camden_4182_broadcast.mp4) | [Download MP4](https://github.com/krshirkoohi/london-local-news/releases/download/v1.0.0/camden_4182_broadcast.mp4) |
| **London Borough of Southwark (#4185)** | 18 New Clean Air School Streets Approved 51–4 | [▶️ **Watch Southwark Reel**](https://github.com/krshirkoohi/london-local-news/blob/main/demos/southwark_4185_broadcast.mp4) | [Download MP4](https://github.com/krshirkoohi/london-local-news/releases/download/v1.0.0/southwark_4185_broadcast.mp4) |

> 💡 **Tip:** Clicking any **"Watch"** link opens GitHub's native video player with sound directly in your web browser. No download required.

---

## 🏛️ Core Engineering Principle

> **AI makes creative decisions within strict constraints (`temperature=0.0`); deterministic code handles typography, figure layout, compliance, and 30fps broadcast assembly.**

Local civic journalism cannot tolerate hallucinations. Fabricating council debates, inventing quotes, or generating synthetic talking heads destroys editorial credibility.

* **Zero-Hallucination Storyboard Extraction:** Every voiceover sentence, caption, and numeric figure is extracted from verified council agendas, minutes, or London Local articles with sentence-level citations (`prompts/stage1_storyboard_extraction.md`).
* **100% Declarative Multi-Story Engine:** Zero story text is hardcoded in Python. Every video is driven by a self-contained JSON specification (`specs/*.json`) and rendered via reusable broadcast figure components.
* **5 Modular Broadcast Figures:** Each scene pairs full-screen `1080×1920` cinema B-roll or archival stills with a structured, glassmorphic data visualization (`vote_tally`, `motion_document`, `stat_comparison`, `action_matrix`, `outro_archive`).
* **Restrained Generative B-Roll & Multi-Angle Crop Reuse:** AI video models (Google Veo / Flow) are used **strictly for atmospheric civic architecture and London streetscapes** (`prompts/stage2_generative_broll_library.md`), hard-watermarked with `"AI ILLUSTRATIVE B-ROLL"`, and reused across scenes via distinct camera crop profiles (`full`, `architectural_upper` B-cam punch-in, and `pan_zoom`) to prevent jump-cut repetition while halving token cost.

---

## 📐 Architecture & 4-Stage Pipeline Flow

```text
[London Local Article + Official Council Minutes]
  (Borough, Meeting Date, Source Agenda Frontsheet, Motions, Division Tally)
                     │
                     ▼
  [Stage 1: Grounded Storyboard & Figure Extraction]
  • Prompt: `prompts/stage1_storyboard_extraction.md`
  • Model: Gemini 2.5 Flash (Temperature = 0.0, JSON Schema Mode)
  • Output: Validated Declarative Storyboard Spec (`specs/<id>-<slug>.json`)
  • Every claim and figure number mapped to exact source sentence IDs
                     │
                     ▼
  [Stage 2: Dual-Track Visual & Figure Routing]
   ├── Track A (Declarative Broadcast Figure Overlay — 1080×1920 RGBA):
   │   • `vote_tally`      → Parliamentary division bar + dual party cards
   │   • `motion_document` → Paper-on-Glass (`#F8F6F0`) order paper + yellow highlight
   │   • `stat_comparison` → Dual glassmorphic metric cards + benchmark progress bars
   │   • `action_matrix`   → 2×2 connected civic governance grid with numbered badges
   │   • `outro_archive`   → 3-row Public Record Audit Trail table + centered CTA pill
   └── Track B (Atmospheric B-Roll & Camera Crop Modes):
       • `full`                → Wide establishing 35mm cinema B-roll
       • `architectural_upper` → Tight B-cam upper facade punch-in (`trimStart` offset)
       • `pan_zoom`            → 35mm monochrome documentary still with Ken Burns pan
                     │
                     ▼
  [Stage 3: British Neural Broadcast Audio (`en-GB-SoniaNeural`)]
  • Engine: `edge-tts` (`en-GB-SoniaNeural`, `+2%` cadence)
  • Cached per story (`assets/audio/scene_<storyId>_<sceneId>.mp3`) for deterministic CI
  • Exact scene audio durations measured via `ffprobe`
                     │
                     ▼
  [Stage 4: Constant-Frame-Rate (30fps CFR) Broadcast Assembly]
  • Engine: Headless FFmpeg (`libx264`, `-r 30`, `yuv420p`, `aac 24kHz`)
  • Top 5px coral progress bar + `SCENE 0X / 05` counter pill
  • Seamless `-f concat -c copy` across normalized 30fps timebases
```

---

## 📊 The 5 Modular Broadcast Figure Types

Every story specification in `specs/*.json` declaratively configures five scene figures in the safe middle viewport (`y=430..1360`):

| Scene | Figure Type | Visual Structure | Default B-Roll Camera Mode |
| :--- | :--- | :--- | :--- |
| **Scene 1** | `vote_tally` | Proportional parliamentary vote bar + Majority vs Opposition party tally cards + unanimous status badge | `full` (Establishing municipal steps) |
| **Scene 2** | `motion_document` | Authentic **Paper-on-Glass** (`#F8F6F0`) Council Order Paper with double parliamentary rule, serif motion excerpt, warm yellow highlighter (`#FDE047`), and Mover/Seconder footer | `pan_zoom` (35mm monochrome archival still) |
| **Scene 3** | `stat_comparison` | Dual glassmorphic metric cards with coral/amber top accent bars, hero figures (`37%`, `180+`), and comparative benchmark progress bars | `full` (Red London double-decker bus streetscape) |
| **Scene 4** | `action_matrix` | Connected `2×2` civic action grid with coral numbered badges (`01`–`04`), horizontal/vertical governance connectors, and pillar sub-captions | `architectural_upper` (Tight B-cam upper stone facade crop) |
| **Scene 5** | `outro_archive` | **Public Record Audit Trail** table with `[ ✓ VERIFIED ]` / `[ ✓ ON RECORD ]` status pills and a centered two-tier URL call-to-action pill | `pan_zoom` (Dark broadsheet endplate) |

---

## 🗂️ Multi-Story Specifications & Prompt Library

### Prompt Engineering Library (`prompts/`)
* [`prompts/stage1_storyboard_extraction.md`](prompts/stage1_storyboard_extraction.md): Production system prompt, anti-hallucination rules, figure selection logic, and strict JSON schema for converting any London Local article into a 5-scene declarative spec.
* [`prompts/stage2_generative_broll_library.md`](prompts/stage2_generative_broll_library.md): Reusable Veo / Flow / Imagen 3 prompt templates across 5 civic categories, mandatory negative prompts (banning deepfakes and readable signage), and multi-angle crop reuse documentation.

### Ready-to-Deploy Story Specs (`specs/`)
1. [`specs/4178-westminster-extremism.json`](specs/4178-westminster-extremism.json) — **Westminster City Council** (*12 Nov 2025*): Unanimous 54–0 Cross-Party Motion Against Far-Right Extremism (`output/sample_video_4178_editorial.mp4`).
2. [`specs/4182-camden-housing-retrofit.json`](specs/4182-camden-housing-retrofit.json) — **London Borough of Camden** (*18 Nov 2025*): £4.2M Warm Homes Estate Retrofit Programme Approved 49–0 (`output/camden-housing-retrofit-4182.mp4`).
3. [`specs/4185-southwark-clean-air-schools.json`](specs/4185-southwark-clean-air-schools.json) — **London Borough of Southwark** (*20 Nov 2025*): 18 New Clean Air School Streets Approved 51–4 (`output/southwark-clean-air-schools-4185.mp4`).

---

## 📂 Repository Layout

```text
london-local-news/
├── prompts/
│   ├── stage1_storyboard_extraction.md       # LLM system prompt & JSON schema (Stage 1)
│   └── stage2_generative_broll_library.md    # Veo/Flow B-roll prompt library & crop modes (Stage 2)
├── specs/
│   ├── 4178-westminster-extremism.json       # Flagship Story #4178 (Westminster City Council)
│   ├── 4182-camden-housing-retrofit.json     # Batch Story #4182 (Camden Housing Retrofit)
│   └── 4185-southwark-clean-air-schools.json # Batch Story #4185 (Southwark School Streets)
├── assets/
│   ├── audio/                                # Cached British neural voiceovers (en-GB-SoniaNeural)
│   ├── branding/
│   │   ├── london-local-wordmark.png         # Official masthead (auto alpha-keyed in pipeline)
│   │   └── london-local-icon.png             # Rounded L. square icon
│   └── generative/
│       ├── gemini_generated_video_535e3482.mp4 # 35mm civic steps & neoclassical facade B-roll
│       ├── gemini_generated_video_d308c8b8.mp4 # 35mm Victoria Street & red London bus B-roll
│       └── westminster_street_bg.jpg         # 35mm monochrome Victoria Street documentary still
├── output/
│   ├── sample_video_4178_editorial.mp4       # Flagship 42.2s 1080x1920@30fps broadcast reel
│   ├── camden-housing-retrofit-4182.mp4      # Story #4182 output (43.1s @ 30fps)
│   └── southwark-clean-air-schools-4185.mp4  # Story #4185 output (45.6s @ 30fps)
├── scripts/
│   └── build_demo.py                         # Declarative V9 Multi-Story Broadcast Engine
└── .github/
    └── workflows/
        └── render.yml                        # GitHub Actions CI/CD cloud renderer
```

---

## 🚀 Quickstart & CLI Usage

### 1. Prerequisites
* Python 3.10+
* `ffmpeg` and `ffprobe` (`brew install ffmpeg`)
* `pip install pillow edge-tts`

### 2. Render the Flagship Westminster Story (`#4178`)
```bash
python3 scripts/build_demo.py
```

### 3. Render Any Single Story Spec
```bash
python3 scripts/build_demo.py --spec specs/4182-camden-housing-retrofit.json
```

### 4. Simultaneous Multi-Story Batch Deployment
Render every story in `specs/*.json` in a single batch run:
```bash
python3 scripts/build_demo.py --batch
```

---

## 🤖 CI/CD & Production DAG Board

* **GitHub Project Board:** [`london-local-news-dag` (#11)](https://github.com/users/krshirkoohi/projects/11)
* **Automated Cloud Rendering:** [`.github/workflows/render.yml`](https://github.com/krshirkoohi/london-local-news/blob/main/.github/workflows/render.yml) runs on every push to `main`, compiles the video headlessly in GitHub Actions, and uploads the resulting `.mp4` artifact.

---

## 📄 Licence & Attribution

Operated under the editorial standards of **London Local** (OCN Technology Ltd). Public council records cited from Westminster City Council, London Borough of Camden, and London Borough of Southwark.
