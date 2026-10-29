# OCN video improvement system

Status: **Proposed implementation, not yet built.** Owner approval required before publishing or merging code changes.

## Objective

Improve the existing London Local News V9 pipeline rather than replace it. Make credible, accurate 9:16 local-news videos that people actually want to watch, with a multimodal AI review loop, batch corrections and a lightweight human editorial GUI.

Priorities: storytelling and retention; factual accuracy; visual realism and clarity; pacing and narration; reusable templates and assets; low API cost; editorial approval.

## Before implementing

1. Inspect the current repository, README, `prompts/`, `specs/`, FFmpeg rendering, assets, CI, tests, existing issues and project board.
2. Preserve the V9 declarative story specification and four-stage pipeline. Do not create a second production architecture or duplicate existing capabilities.
3. Verify the available Google AI models, credentials, API quota and costs. Google AI Pro subscription does not by itself guarantee unrestricted API use.
4. Record an implementation plan as a GitHub issue, reuse existing issues where appropriate and work in small verifiable milestones.

## Review and correction algorithm

### A. Generate and record the baseline
Use the current renderer to create an initial version from sourced reporting. Retain article and council evidence, citation identifiers, JSON spec, script, storyboard, source/asset manifest, scene IDs, configuration, audio and output version. Record a baseline quality review and actual consumption.

### B. Multimodal inspection
Select a model capable of inspecting the actual rendered video and audio. Provide it the relevant frames/clips, voiceover, captions, script, timing, scene plan, source evidence and manifest. Never claim to inspect media the model did not receive.

Evaluate:
- Opening hook: why would someone stop scrolling?
- Local significance: why does this matter to the borough?
- Narrative: development, tension, clarity and payoff.
- Retention: dead time, repetitive scenes, weak transitions.
- Visual credibility: specificity, framing, typography, motion, consistency.
- Audio: British-English clarity, cadence, levels, synchronisation.
- Subtitles: correctness, readability and safe placement.
- Factual accuracy: every numerical and material claim traced to its source.
- Editorial safety: distinguish illustrative AI footage from real-event imagery and prevent invented quotes, people or incidents.

Report both objective defects and subjective editorial suggestions. Scores are advisory, not proof of watchability.

### C. Structured correction proposal
Return machine-readable findings with fields like:
```json
{
  "iteration": 1,
  "findings": [{
    "id": "R001",
    "scene_id": "scene_01",
    "time_range_seconds": [0, 4],
    "category": "hook",
    "severity": "high",
    "observation": "Opening explains rather than engages",
    "evidence": "Description of observed frames/audio",
    "proposed_change": "Replace first line and opening overlay",
    "affected_files": [],
    "dependencies": [],
    "requires_regeneration": false,
    "editorial_approval": true,
    "confidence": 0.8,
    "estimated_cost": null
  }]
}
```
Determine changes, dependencies, expected benefits, required approvals and rough cost. Prefer deterministic FFmpeg/template edits, existing footage and cached assets before expensive AI generation. Never regenerate satisfactory scenes without reason.

### D. Human approval gate
Expose proposed corrections in a **minimal single-user GUI** with:
- Video preview with seeking to issue timestamps.
- Correction queue with evidence, severity and affected scene.
- Approve/reject/edit individually, plus approve a compatible batch.
- Controls to apply approved changes, rerender, compare iterations and accept final output.
- Basic job progress, failures, usage and reuse/regeneration details.

This is *not* a full nonlinear video editor. Avoid accounts, permissions, dashboards and unrelated infrastructure. Human editorial approval is required for consequential content changes and all publication.

### E. Batch corrections
Build a dependency-aware change plan from approved proposals. Batch compatible edits; parallelise independent tasks only when safe; prevent concurrent edits to the same file. Preserve stable identifiers, version history and unchanged outputs. Cache reusable results, validate specs, execute tests and render affected components where supported by the existing pipeline.

### F. Re-evaluate
Compare the new output with the baseline and previous iteration. Identify fixed issues, remaining issues, regressions, cost and whether another iteration is warranted. Repeat until human approval or further changes no longer justify their cost. Human judgement overrides model scores.

## Reusable assets
Extend the existing asset conventions rather than duplicating the library. Track borough, location, category, provenance, licence, model and generation parameters, file path/hash and reuse restrictions. An illustrative Camden streetscape can be reused if context permits; never present it as footage of an actual specific incident. Preserve the existing illustrative B-roll labelling and strict source-attribution policy.

## Agent and API approach
Start with **one coordinating agent** calling existing tools. Introduce specialist or parallel agents only for measured benefits, such as factual checks. Use structured schemas and deterministic executors rather than unnecessary agent conversations. Deduplicate tasks, cache results, checkpoint progress, back off on API rate limits and preserve resumability. Log actual usage when API responses expose it, and distinguish estimates from measured costs.

## Milestones
1. Repository audit and integration plan.
2. Structured multimodal video assessment and correction plan.
3. Minimal human-review GUI.
4. Approved batch application, incremental rendering and version comparison.
5. End-to-end evaluation on an existing Westminster, Camden or Southwark demo.

## Acceptance criteria
- V9 rendering continues to work.
- Real video and audio are inspected with a reproducible structured report.
- The editor can approve/reject corrections in a lightweight GUI.
- Approved edits are applied in batches while preserving unaffected assets.
- Iterations can be rendered, compared and accepted.
- Interruptions and rate limits are recoverable.
- Source attribution, labelled illustrative AI media and human final approval remain intact.
- Results include measured quality observations, regressions, limitations and costs.

## GitHub working agreement
Use existing GitHub issues/board for intent and status, a feature branch for implementation, focused commits, tests and a pull request for review. Do not merge or publish without owner approval. Do not treat this document as authorisation to deploy or incur paid API costs.

## First action for an agent
**Audit the repository and propose the smallest end-to-end vertical slice. Do not start by building the entire GUI or rewriting the video pipeline.**
