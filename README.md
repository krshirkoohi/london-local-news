# London Local: Automated News Video Pipeline

[![Build News Video Demo](https://github.com/krshirkoohi/london-local-news/actions/workflows/render.yml/badge.svg)](https://github.com/krshirkoohi/london-local-news/actions/workflows/render.yml)
[![DAG Tracking](https://img.shields.io/badge/DAG_Board-Project_%2311-blue?logo=github)](https://github.com/users/krshirkoohi/projects/11)
[![Platform](https://img.shields.io/badge/Format-9%3A16_Vertical-purple)](#)
[![Identity](https://img.shields.io/badge/Brand-London_Local.-FF5238)](#)

An industrial, semi-automated short-form news video generation engine built for [London Local](https://londonlocal.news/) (covering civic decisions across Greater London's 33 councils).

Engineered to scale newsroom throughput to **30+ verified stories per week with a single human editor**, while enforcing strict factual traceability and eliminating synthetic hallucinations.

---

## 🏛️ Core Engineering Principle

> **AI makes creative decisions within strict constraints; deterministic code handles assembly, compliance, and rendering.**

Local civic journalism cannot tolerate hallucinations. Fabricating council debates, inventing quotes, or generating plastic "deepfake" talking heads destroys editorial credibility.

* **Zero-Hallucination Extraction:** Every voiceover sentence and caption is extracted from verified council agendas, minutes, or London Local reports with sentence-level citations.
* **Deterministic Layout & Typography:** All headlines, vote statistics, and document excerpts are rendered in code using crisp vector typography, guaranteeing zero garbled text.
* **Restrained Generative Footage:** AI video models (Google Veo / Flow) are used **strictly for atmospheric, environmental B-roll** (e.g. wet streetscapes, London transit) and are hard-watermarked with `"AI Illustrative B-Roll"`.
* **White-Label Partner Slot:** Top banner features a configurable `[ YOUR LOGO HERE ]` slot, easily swappable with official verified publication wordmarks.

---

## 📐 Architecture & Pipeline Flow

```
[London Local Article + Council Record]
  (Borough, Meeting Date, Source Agenda Frontsheet, Motions)
                     │
                     ▼
  [Stage 1: Grounded Storyboard Extraction]
  • Model: Gemini 2.5 Flash (Temperature = 0.0)
  • Output: Validated JSON Storyboard Spec (`specs/*.json`)
  • Every claim mapped to exact source sentence IDs
                     │
                     ▼
  [Stage 2: Dual-Track Asset Routing]
   ├── Track A (Real / Deterministic):
   │   • Cartographic Thames & borough boundary vector textures
   │   • Official council agenda excerpts with yellow highlighter motion
   │   • Cross-community infographic cards & vote tallies
   └── Track B (Atmospheric Diffusion):
       • 35mm monochrome documentary B-roll (Victoria Street / City Hall)
       • High-contrast ambient weather & transit
       • Hardcoded amber "AI Illustrative B-Roll" badge
                     │
                     ▼
  [Stage 3: British Neural Audio Synthesis]
  • Engine: `edge-tts` / Google Cloud TTS (`en-GB-RyanNeural`)
  • Exact scene audio durations computed via `ffprobe`
  • Sub-second cadence alignment
                     │
                     ▼
  [Stage 4: Headless Broadsheet Assembly]
  • Engine: Headless FFmpeg Pipeline
  • Cuts timed to exact audio timestamps with safe-zone margins
  • Resolution: 1080×1920 (9:16 Vertical for TikTok, Reels, Reddit)
                     │
                     ▼
  [Output: 40s Broadcast-Grade News Reel]
  (`output/sample_video_4178_editorial.mp4`)
```

---

## 🎨 Visual Identity & Design System

The visual language reflects London Local's authentic black-and-white broadsheet print heritage:

| Element | Specification | Visual Purpose |
| :--- | :--- | :--- |
| **Colour Palette** | `#0A0A0A` (Deep Black), `#FFFFFF` (Crisp Broadsheet), `#FF5238` (Signature Coral Red) | Authoritative civic newspaper aesthetic with high contrast |
| **Cartographic Texture** | Subtle coordinate grid, Thames River curve, and Westminster boundary contour lines | Recognisably local context without visual clutter |
| **Typography** | **Georgia Bold** (Headline Serif), **Arial** (Clean Metadata Sans) | Traditional editorial gravitas paired with mobile readability |
| **Branding Slot** | Header rule with `London Local.` wordmark or `[ YOUR LOGO HERE ]` container | Direct support for syndication and partner newsrooms |
| **Provenance Label** | Amber badge: `"AI ILLUSTRATIVE B-ROLL"` on Scene 3 | Absolute transparency for regulatory & editorial compliance |

---

## 📂 Repository Layout

```text
london-local-news/
├── specs/
│   └── 4178-westminster-extremism.json      # Machine-readable storyboard contract
├── assets/
│   ├── branding/
│   │   ├── london-local-wordmark.png        # Official masthead with coral red dot
│   │   ├── london-local-icon.png            # Rounded L. square icon
│   │   └── scene5_outro.png                 # Verified source document endplate
│   ├── real/
│   │   ├── scene1_westminster_vote.png      # Unanimous vote headline card
│   │   ├── scene2_equality_strategy.png     # Agenda extract with motion highlight
│   │   └── scene4_working_group.png         # 4-pillar community action infographic
│   └── generative/
│       ├── westminster_street_bg.jpg        # 35mm monochrome Victoria Street B-roll
│       └── scene3_victoria_street.png       # Layered demographic card with amber badge
├── build/
│   ├── audio/
│   │   ├── scene_1.mp3 ... scene_5.mp3      # Synthesised British news audio clips
│   │   └── concat_list.txt                  # Deterministic FFmpeg concatenation spec
├── output/
│   └── sample_video_4178_editorial.mp4      # Final 41.08s 1080x1920 MP4 news reel
├── scripts/
│   └── build_demo.py                        # Automated Python assembly pipeline
└── .github/
    └── workflows/
        └── render.yml                       # GitHub Actions CI/CD cloud renderer
```

---

## 🚀 Quickstart & Local Execution

### 1. Prerequisites
* Python 3.10+
* `ffmpeg` and `ffprobe` (`brew install ffmpeg`)

### 2. Install Dependencies
```bash
pip install pillow edge-tts
```

### 3. Run the Assembly Pipeline
To generate all broadsheet graphic cards, synthesise the neural voiceover, and render the master 41s video:

```bash
python3 scripts/build_demo.py
```

*To render with a placeholder `[ YOUR LOGO HERE ]` box instead of the official logo:*
```bash
python3 scripts/build_demo.py --show-authorised-logo=False
```

### 4. Review the Output
```bash
open output/sample_video_4178_editorial.mp4
```

---

## 🤖 CI/CD & Production DAG Board

This project operates strictly under a Directed Acyclic Graph (DAG) workflow:

* **GitHub Project Board:** [`london-local-news-dag` (#11)](https://github.com/users/krshirkoohi/projects/11)
* **Automated Cloud Rendering:** [`.github/workflows/render.yml`](https://github.com/krshirkoohi/london-local-news/blob/main/.github/workflows/render.yml) runs on every push and compiles the news video in GitHub Actions, uploading the resulting `.mp4` as a 7-day downloadable artifact.
* **Evidence Logging:** Every iteration records an append-only run log comment directly on the active GitHub issue summarizing:
  `(Stage, Outcome, Model, Commit Hash)`.

---

## 📄 Licence & Attribution

Operated under the editorial standards of **London Local** (OCN Technology Ltd). Public council records cited from Westminster City Council (Meeting of 12 November 2025).
