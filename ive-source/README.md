# Interactive Visual Gym — release preview

Interactive Visual Gym supports closed-loop evaluation of visual assistants through joint simulation of task environments and human users. This website presents matched assistant comparisons, recorded failure examples, persona-conditioned user simulation, and results from the Interactive Visual Evaluation (IVE) benchmark.

[Live preview](https://hellomuffin.github.io/ive-benchmark/) · [Submission intake](https://github.com/hellomuffin/ive-benchmark/tree/main/ive-submissions)

## View the recorded episodes locally

Run this command from the repository root.

```bash
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000`. Select an environment, press play, and jump to a scheduled event. All observations, audio, and episode data are static files. This **replays** benchmark episodes; it does not run a new interactive evaluation.

## What is included

- Two assistants under matched task, persona, and scheduled-event settings in each environment; original failure excerpts from the paper; and three CookSim personas with the same assistant and task. Dialogue is transcribed verbatim. Speech is synthetic and playback is time-expanded. CookSim's views are re-rendered from saved states at 960 × 720 each. ScreenSim's reconstructed gestures are checked against the recorded action outcomes. Presentation reconstructions do not change the assistants' evaluation inputs.
- A 14-model paper baseline, pinned to source commit `69f62e53e294cb56dfb48eaa2ae542c2cbac0070`. Overall scores average the three environments equally. Success and quality summarize three runs; detection recall is run 1.
- 105 underlying cases × three personas = 315 case–persona episodes (150 cooking, 75 household, 90 mobile). These are not 315 independently constructed tasks.
- Downloadable normalized demo records and leaderboard JSON.
- A submission manifest schema, browser structure checks, and a local validator.

The legacy `ive-preview-kit.zip` contains the earlier three-demo preview, not the expanded comparison page. Clone this repository for the current website.

## Submission validation

The [submission guide](https://hellomuffin.github.io/ive-benchmark/submission.html) specifies required files, JSON fields, the trace archive layout, and all nine engine/run cohorts. For traces following the recommended naming convention, `tools/create_manifest.py` generates a complete manifest and computes hashes without making model calls.

```bash
python ive-source/tools/validate_submission.py my-submission.json --traces ./submission --full
```

The full check requires all three environments, three runs, exact membership in the versioned case/persona catalog, unique IDs within each run, and matching trace hashes when a trace directory is supplied. It does not independently establish that traces came from the claimed model or reproduce judge scores. A result must pass engine/judge verification before it can become a verified leaderboard entry.

The example manifest is a valid, single-episode demonstration with a real trace hash. Try it without `--full`:

```bash
python ive-source/tools/validate_submission.py docs/submission/example.json --traces docs
```

It is explicitly labeled `demo_only` and is rejected as a full benchmark submission.

For a public submission service, accept manifests and trace archives, run validation in an isolated job, retain provenance and coverage counts, and publish a separate provisional entry until verification completes. Never execute submitted code or load pickle files in the validation service.

The preview's GitHub intake runs read-only manifest checks on pull requests. It does not automatically trust submitted scores or promote them to the verified leaderboard. Full simulator execution and judge re-evaluation require scoring workers beyond static website hosting.

## Rebuilding from the research workspace

`tools/build_data.py` reads the pinned paper snapshots and selected engine records. `tools/build_media.py` extracts observations, verifies ScreenSim replay, and synthesizes labelled presentation audio. These two tools require the original sibling engine repositories and are not needed to view the website. API credentials remain outside the repository.

The extracted replay kit also supports rebuilding the narrated MP4s from its bundled frames, audio, data, and fonts using `python ive-source/tools/export_videos.py`. This requires Pillow, NumPy, and FFmpeg, but no simulator, API key, or GPU. `tools/build_presentation_media.py` regenerates the high-resolution CookSim views and ScreenSim gestures from the research repositories; this step is unnecessary when using the included presentation frames.

`tools/check_site.py` tests the desktop/mobile page, model filtering, and horizontal overflow using Playwright. It expects a local server on port 8793.

`tools/build_comparison_data.py` checks shared task/event specifications and exports the matched trajectories. `tools/build_comparison_media.py` builds their recorded observations and presentation speech. `tools/build_failure_data.py` traces the qualitative figure back to original episode records. `tools/check_comparisons.py` checks verbatim dialogue, narration, replay controls, and responsive layouts.

## Production-release checklist

- Publish versioned engine distributions, full case definitions, runtime dependencies, and model adapter instructions after their separate dependency/licensing and secret audits. This website does not claim those packages have been released.
- Pin engine, human-model, prompt, judge, and configuration versions for accepted submissions.
- Establish submission storage and isolated scoring workers; keep API keys server-side. Static website hosting alone cannot re-run simulation or judge submitted traces.
- Add paper/citation links once final public metadata is available; do not invent an arXiv identifier or author list.
- Review demo transcript fidelity, synthetic voices, case/persona descriptions, and model display names before announcing the public launch.

No participant conversations are included; all displayed users are simulated.
