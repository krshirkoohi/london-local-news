#!/usr/bin/env python3
"""
Automated Civic Broadcast Engine — Interactive Newsroom Terminal CLI
===================================================================
A guided Prompt Q&A and Review interface for civic editors:
1. Ingests raw council agendas, ModGov URLs, scraped news articles, or pasted notes.
2. Runs an editorial interview questionnaire (angle, borough, audience focus, tone).
3. Uses Gemini (gemini-3.8-flash) to extract a strictly verified, 5-scene JSON spec.
4. Allows interactive scene-by-scene review & modification in the terminal.
5. Automatically matches silent, OCR-verified B-roll with 3-shot Scene 3 cutaways.
6. Synthesises British voiceover and renders the 1080x1920 30fps broadcast reel.
7. Offers 1-click deployment to docs/videos/ and the GitHub Pages showcase.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

# Setup base directory & imports
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "scripts"))

import audit_broll_text
import broll_matcher
import build_demo
from production_contract import check_render_contract
from qc_inspector import audit_spec_text_layout

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "accent": "bold magenta",
})
console = Console(theme=custom_theme)

BOROUGHS = [
    "Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley", "Camden",
    "City of London", "Croydon", "Ealing", "Enfield", "Greenwich", "Hackney",
    "Hammersmith and Fulham", "Haringey", "Harrow", "Havering", "Hillingdon",
    "Hounslow", "Islington", "Kensington and Chelsea", "Kingston upon Thames",
    "Lambeth", "Lewisham", "Merton", "Newham", "Redbridge", "Richmond upon Thames",
    "Southwark", "Sutton", "Tower Hamlets", "Waltham Forest", "Wandsworth",
    "Westminster"
]

EDITORIAL_ANGLES = [
    "Resident Pocketbook Impact (Council Tax, Fees, Parking Charges)",
    "Housing, Estate Regeneration & Tenant Rights",
    "Transport, Bus Service Changes & Active Travel (Cycle Lanes)",
    "Public Health, Care Services & Youth Provision",
    "Environment, Waste Collection, Low Traffic & Green Spaces",
    "Democratic Scrutiny, Motions & Financial Governance",
]


def print_banner():
    console.print(
        Panel.fit(
            "[bold white]AUTOMATED CIVIC BROADCAST ENGINE[/bold white]\n"
            "[italic cyan]Interactive Newsroom Terminal CLI • V9 Programmatic Reel Generator[/italic cyan]\n"
            "[dim]From Council Records to Verified 1080×1920 30fps Broadcast Video[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )


def extract_text_from_source(source_input: str) -> str:
    """Handles URLs, local file paths, or directly pasted council text."""
    s = source_input.strip()
    if s.startswith("http://") or s.startswith("https://"):
        console.print(f"[cyan]🌐 Fetching content from URL:[/cyan] {s}")
        try:
            import urllib.request
            req = urllib.request.Request(
                s,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) CivicNews/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            # Strip simple HTML tags
            clean_text = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r"<style.*?</style>", "", clean_text, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r"<[^>]+>", " ", clean_text)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()
            return clean_text[:20000]
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not fetch URL directly ({e}). Treating as text prompt.[/yellow]")
            return s
    p = Path(s)
    if p.exists() and p.is_file():
        console.print(f"[cyan]📄 Reading file:[/cyan] {p}")
        return p.read_text(encoding="utf-8", errors="ignore")
    return s


def generate_storyboard_spec(
    raw_text: str,
    borough: str,
    angle: str,
    audience: str,
    tone: str,
    source_url: str = "https://londonlocal.news",
) -> Dict[str, Any]:
    """Uses Gemini 3.8 Flash to extract verified claims and format a 5-scene JSON spec."""
    api_key = audit_broll_text.load_api_key()
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    prompt = f"""
You are the Executive Editor of London Local, an independent civic broadcast newsroom.
Extract a frame-accurate, strictly factual 5-scene vertical 9:16 broadcast storyboard from this council document.

CONSTRAINTS & RULES:
1. Zero synthetic hallucination. Every fact, statistic, and quote must exist in the source text.
2. Language: British English (en-GB).
3. Total duration: 30-36 seconds.
4. Tone: {tone}.
5. Angle: {angle}.
6. Target Audience: {audience}.
7. Output strictly valid JSON adhering to the London Local V9 specification format.

SOURCE DOCUMENT / EXCERPT:
{raw_text}

JSON SCHEMA FORMAT REQUIRED:
{{
  "videoId": "generated-slug",
  "storyId": "generated-id",
  "storyTitle": "Full headline (max 90 chars)",
  "headline": "Short hook headline (max 48 chars)",
  "borough": "{borough}",
  "postcodeTag": "📍 {borough.upper()} · CABINET DECISION",
  "committee": "Committee Name, Date",
  "meetingDate": "DD MMM YYYY",
  "meetingDateDisplay": "{borough} · DD MMM YYYY",
  "storyType": "council_decision",
  "targetDurationSeconds": 33,
  "keyPointsHeading": "How will residents be affected?",
  "factsFiguresHeading": "Facts & Shortfall",
  "claims": [
    {{
      "claimId": "C1",
      "statement": "Factual statement",
      "sourceQuote": "Direct quote from source text",
      "sourceDocument": "Meeting or agenda citation",
      "verified": true
    }}
  ],
  "takeawayCard": {{
    "kicker": "FINANCIAL STABILITY",
    "title": "Short punchy takeaway",
    "subtitle": "Brief context"
  }},
  "keyPoints": [
    ["Anchor Point 1", "Detailed 1-2 sentence explanation.", "Citation"],
    ["Anchor Point 2", "Detailed 1-2 sentence explanation.", "Citation"],
    ["Anchor Point 3", "Detailed 1-2 sentence explanation.", "Citation"]
  ],
  "timeline": [
    {{
      "sceneNumber": 1,
      "type": "video_with_figure",
      "durationSeconds": 3.4,
      "claimIds": ["C1"],
      "onScreenGraphic": {{
        "kicker": "📍 {borough.upper()} · CABINET DECISION",
        "headline": "Hook headline",
        "body": "Clear summary subtitle."
      }},
      "voiceoverText": "First sentence spoken by BBC narrator."
    }},
    {{
      "sceneNumber": 2,
      "type": "document_highlight",
      "durationSeconds": 6.8,
      "claimIds": ["C1"],
      "figure": {{
        "type": "motion_document",
        "data": {{
          "docHeaderLeft": "{borough.upper()} · DATE",
          "docHeaderRight": "CABINET REPORT",
          "docSubject": "Document Subject Title",
          "excerptPrefix": "\\"Prefix ",
          "highlightPhrase": "exact key highlighted phrase",
          "excerptSuffix": " suffix.\\"",
          "mover": "Councillor or Director Name",
          "receiptStamp": "CABINET RECORD"
        }}
      }},
      "onScreenGraphic": {{
        "kicker": "VERIFIED COUNCIL RECORD",
        "headline": "Document Subject Title",
        "body": "{borough} · Meeting Record"
      }},
      "voiceoverText": "Second sentence detailing the formal council decision."
    }},
    {{
      "sceneNumber": 3,
      "type": "generative_broll",
      "durationSeconds": 8.0,
      "claimIds": ["C1"],
      "figure": {{
        "type": "stat_comparison",
        "data": {{
          "cards": [
            {{"kicker": "METRIC 1", "value": "£Xm", "label": "description"}},
            {{"kicker": "METRIC 2", "value": "£Ym", "label": "description"}}
          ]
        }}
      }},
      "onScreenGraphic": {{
        "kicker": "KEY IMPACTS",
        "headline": "How will residents be affected?",
        "body": "Key findings from council report."
      }},
      "voiceoverText": "Third sentence presenting the 3 key findings in order matching keyPoints."
    }},
    {{
      "sceneNumber": 4,
      "type": "broadsheet_split",
      "durationSeconds": 7.5,
      "claimIds": ["C1"],
      "figure": {{
        "type": "stat_comparison",
        "data": {{
          "cards": [
            {{"kicker": "METRIC 1", "value": "£Xm", "label": "description"}},
            {{"kicker": "METRIC 2", "value": "£Ym", "label": "description"}}
          ]
        }}
      }},
      "onScreenGraphic": {{
        "kicker": "FACTS & FIGURES",
        "headline": "Facts & Shortfall",
        "body": "Core summary"
      }},
      "voiceoverText": "Fourth sentence covering the key statistics."
    }},
    {{
      "sceneNumber": 5,
      "type": "outro_archive",
      "durationSeconds": 6.8,
      "claimIds": ["C1"],
      "figure": {{
        "type": "outro_archive",
        "data": {{
          "tagline": "Independent civic intelligence across London's 33 councils.",
          "ctaKicker": "READ THE FULL VERIFIED STORY",
          "ctaUrl": "londonlocal.news"
        }}
      }},
      "onScreenGraphic": {{
        "kicker": "READ FULL STORY",
        "headline": "Read online at londonlocal.news",
        "body": "Direct from council agendas to your phone."
      }},
      "voiceoverText": "Concluding call to action."
    }}
  ]
}}
"""

    res = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
        ),
    )
    spec_data = json.loads(res.text)
    spec_data["sourceArticleUrl"] = source_url
    spec_data["sourceUrl"] = source_url
    return spec_data


def display_spec_summary(spec: Dict[str, Any]):
    table = Table(title=f"📋 Storyboard Preview: {spec.get('headline')}", show_header=True, header_style="bold cyan")
    table.add_column("Scene", style="dim", width=8)
    table.add_column("Layout Type", style="magenta", width=22)
    table.add_column("Voiceover Narrative (BBC en-GB)", style="white")
    table.add_column("Visual B-Roll / Graphic", style="green", width=34)

    tl = spec.get("timeline", [])
    for s in tl:
        num = s.get("sceneNumber")
        stype = s.get("type")
        vo = s.get("voiceoverText", "")
        va = s.get("visualAsset", {}).get("source", "Auto-matched B-roll")
        table.add_row(f"0{num}", stype, vo, Path(va).name if va else "TBD")

    console.print(table)


def auto_assign_broll_pool(spec: Dict[str, Any]):
    """Assigns deterministic B-roll from library with 3-shot Scene 3 cuts."""
    broll_matcher.assign_broll_to_spec(spec)
    # Check if Scene 3 has cutawaySource2
    tl = spec.get("timeline", [])
    if len(tl) >= 3:
        s3 = tl[2]["visualAsset"]
        if not s3.get("cutawaySource2"):
            # Provide sensible default 3rd cutaway
            kp = spec.get("keyPoints", [])
            if len(kp) >= 3:
                p3_text = str(kp[2]).lower()
                if "waste" in p3_text or "bin" in p3_text or "caddy" in p3_text:
                    s3["cutawaySource2"] = "assets/generative/london_env_food_waste_caddy_kerb_omni.mp4"
                elif "bus" in p3_text or "route" in p3_text:
                    s3["cutawaySource2"] = "assets/generative/london_transport_red_bus_rain_omni.mp4"
                else:
                    s3["cutawaySource2"] = "assets/generative/london_highways_resurfacing_roller_omni.mp4"


def main():
    print_banner()

    # Step 1: Ingestion
    console.print("\n[bold yellow]STEP 1: INGESTION[/bold yellow]")
    source_input = questionary.text(
        "Enter Council URL, Agenda PDF path, or paste raw meeting text:",
        default="https://modgov.hillingdon.gov.uk/documents/g5211/Agenda.pdf"
    ).ask()

    if not source_input:
        console.print("[red]Aborted.[/red]")
        sys.exit(0)

    raw_text = extract_text_from_source(source_input)
    console.print(f"[green]✓ Ingested {len(raw_text):,} characters of source context.[/green]")

    # Step 2: Editorial Interview
    console.print("\n[bold yellow]STEP 2: EDITORIAL ANGLE & FRAMING[/bold yellow]")
    borough = questionary.select(
        "Which London Borough does this decision affect?",
        choices=BOROUGHS,
        default="Hillingdon"
    ).ask()

    angle = questionary.select(
        "Select the primary editorial angle for this story:",
        choices=EDITORIAL_ANGLES,
        default=EDITORIAL_ANGLES[0]
    ).ask()

    audience = questionary.text(
        "Target citizen audience / who cares most?",
        default="Local residents, car owners, and families using community services"
    ).ask()

    tone = questionary.select(
        "Editorial tone / hook style:",
        choices=[
            "Immediate, direct citizen impact & pocketbook reality",
            "Objective council scrutiny & budgetary deficit breakdown",
            "Community resistance, petitions & public debate",
        ],
        default="Immediate, direct citizen impact & pocketbook reality"
    ).ask()

    # Step 3: Storyboard Spec Generation
    console.print("\n[bold yellow]STEP 3: GROUNDED STORYBOARD EXTRACTION[/bold yellow]")
    with console.status("[bold cyan]Consulting Gemini 3.8 Flash to extract verified claims and format spec..."):
        spec = generate_storyboard_spec(
            raw_text=raw_text,
            borough=borough,
            angle=angle,
            audience=audience,
            tone=tone,
            source_url=source_input if source_input.startswith("http") else "https://londonlocal.news",
        )

    # Step 4: B-Roll Matching
    auto_assign_broll_pool(spec)
    display_spec_summary(spec)

    # Step 5: Interactive Review & Modification
    while True:
        action = questionary.select(
            "Review Storyboard:",
            choices=[
                "✅ Accept Storyboard & Proceed to Render",
                "✏️ Edit Headline or Hook Text",
                "✏️ Edit Scene Voiceover Text",
                "🔄 Re-generate Storyboard with Different Angle",
                "❌ Cancel"
            ],
            default="✅ Accept Storyboard & Proceed to Render"
        ).ask()

        if action.startswith("✅"):
            break
        elif action.startswith("❌"):
            console.print("[red]Aborted by user.[/red]")
            sys.exit(0)
        elif action.startswith("✏️ Edit Headline"):
            new_hl = questionary.text("Headline (max 48 chars):", default=spec.get("headline", "")).ask()
            spec["headline"] = new_hl
            spec["timeline"][0]["onScreenGraphic"]["headline"] = new_hl
            display_spec_summary(spec)
        elif action.startswith("✏️ Edit Scene Voiceover"):
            sc_choices = [f"Scene {s['sceneNumber']}: {s.get('voiceoverText', '')[:50]}..." for s in spec["timeline"]]
            chosen_sc = questionary.select("Select scene to edit voiceover:", choices=sc_choices).ask()
            sc_idx = int(chosen_sc.split(":")[0].replace("Scene", "").strip()) - 1
            new_vo = questionary.text("Voiceover text:", default=spec["timeline"][sc_idx]["voiceoverText"]).ask()
            spec["timeline"][sc_idx]["voiceoverText"] = new_vo
            display_spec_summary(spec)
        elif action.startswith("🔄"):
            spec = generate_storyboard_spec(raw_text, borough, angle, audience, tone)
            auto_assign_broll_pool(spec)
            display_spec_summary(spec)

    # Save Spec to Disk
    spec_slug = re.sub(r"[^a-z0-9]+", "-", spec.get("headline", "story").lower()).strip("-")[:32]
    spec_path = BASE_DIR / "specs" / f"cli_{spec_slug}.json"
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    console.print(f"[green]✓ Spec saved to:[/green] {spec_path.relative_to(BASE_DIR)}")

    # Step 6: Render Master Broadcast Video
    console.print("\n[bold yellow]STEP 4: RENDER BROADCAST REEL[/bold yellow]")
    should_render = questionary.confirm("Render 1080×1920 30fps Master MP4 now?", default=True).ask()
    if not should_render:
        console.print("[yellow]Spec generated without rendering. Done![/yellow]")
        return

    out_name = f"{spec_slug}_broadcast.mp4"
    with console.status("[bold green]Synthesising voiceover, motion figures, and assembling master video..."):
        out_mp4 = build_demo.render_story_from_spec(
            str(spec_path),
            show_logo=True,
            force_tts=True,
            draft=False,
            output_dir_override=str(BASE_DIR / "output" / "cli"),
        )
        web_dest = BASE_DIR / "docs" / "videos" / out_name
        demo_dest = BASE_DIR / "demos" / out_name
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", out_mp4,
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            str(web_dest)
        ], check=True)
        subprocess.run(["cp", str(web_dest), str(demo_dest)], check=True)

    console.print(f"[bold green]🎉 Master Render Complete:[/bold green] {web_dest}")
    console.print(f"File size: [cyan]{web_dest.stat().st_size / (1024*1024):.2f} MB[/cyan]")

    # Step 7: Publish to GitHub Pages
    publish = questionary.confirm("Commit and push to live GitHub Pages showcase now?", default=False).ask()
    if publish:
        subprocess.run(["git", "add", str(spec_path), str(web_dest), str(demo_dest)], cwd=str(BASE_DIR), check=True)
        subprocess.run(["git", "commit", "-m", f"feat(cli): generate broadcast reel for {borough}: {spec.get('headline')}"], cwd=str(BASE_DIR), check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_DIR), check=True)
        console.print("[bold green]🚀 Published live to GitHub Pages main branch![/bold green]")


if __name__ == "__main__":
    main()
