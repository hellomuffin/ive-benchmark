# Interactive Visual Evaluation — release preview

A source-grounded website for IVE: three voiced episode replays, synchronized observations and dialogue, task progress, scheduled events, personas, contextual rubric scores, and a model leaderboard.

## One-minute quickstart (no API key or GPU)

```bash
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000`. Select an environment, press play, and jump to a scheduled event. All observations, audio, and episode data are static files. This **replays** benchmark episodes; it does not run a new interactive evaluation.

## What is included

- Three original recorded trajectories with new presentation voices and a new visualization. Dialogue is not rewritten. Native simulation ticks remain visible; playback is deliberately time-expanded for speech.
- A 14-model paper baseline, pinned to source commit `69f62e53e294cb56dfb48eaa2ae542c2cbac0070`. Overall scores average the three environments equally. Success and quality summarize three runs; detection recall is run 1.
- 105 underlying cases × three personas = 315 case–persona episodes (150 cooking, 75 household, 90 mobile). These are not 315 independently constructed tasks.
- Downloadable normalized demo records and leaderboard JSON.
- A submission manifest schema, browser structure checks, and a local validator.

## Submission validation

```bash
python tools/validate_submission.py my-submission.json --traces ./submission --full
```

The full check requires all three environments, three runs, the expected episode counts, unique case/persona IDs within each run, and matching trace hashes. It does not independently establish that traces came from the claimed model or reproduce judge scores. A result must pass engine/judge verification before it can become a verified leaderboard entry. The example manifest contains placeholders and intentionally cannot pass the full validator.

For a public submission service, accept manifests and trace archives, run validation in an isolated job, retain provenance and coverage counts, and publish a separate provisional entry until verification completes. Never execute submitted code or load pickle files in the validation service.

## Rebuilding from the research workspace

`tools/build_data.py` reads the pinned paper snapshots and selected engine records. `tools/build_media.py` extracts observations, verifies ScreenSim replay, and synthesizes labelled presentation audio. `tools/export_videos.py` creates standalone MP4s. These build tools require the original sibling engine repositories and are not needed to view the website. API credentials remain outside the repository.

`tools/check_site.py` tests the desktop/mobile page, model filtering, and horizontal overflow using Playwright. It expects a local server on port 8793.

## Production-release checklist

- Publish versioned engine distributions, full case definitions, runtime dependencies, and model adapter instructions after their separate dependency/licensing and secret audits. This website does not claim those packages have been released.
- Pin engine, human-model, prompt, judge, and configuration versions for accepted submissions.
- Establish submission storage and isolated scoring workers; keep API keys server-side. Static website hosting alone cannot re-run simulation or judge submitted traces.
- Add paper/citation links once final public metadata is available; do not invent an arXiv identifier or author list.
- Review demo transcript fidelity, synthetic voices, case/persona descriptions, and model display names before announcing the public launch.

No participant conversations are included; the three demos use simulated users.
