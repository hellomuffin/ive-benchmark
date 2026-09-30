# IVE result submissions

Add one JSON manifest per model/configuration in a pull request. The website provides the schema and an example. Include a stable model/API revision, the benchmark version, all three independent runs, and the 150/75/90 case–persona episodes per run for CookSim/VHSim/ScreenSim.

Automated checks validate manifest structure, episode counts, and duplicate IDs. They do **not** certify scores or run submitted code. Provide trace archives and engine/harness/judge versions in your pull request description so maintainers can reproduce and verify results. Do not commit credentials or human participant data. A passing manifest check does not publish a leaderboard result.

The local verifier additionally checks SHA-256 hashes when `--traces` points to a downloaded trace directory:

```bash
python ive-source/tools/validate_submission.py ive-submissions/my-model.json --full --traces ./my-traces
```

Use [GitHub's file-upload flow](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository) to propose a manifest. Fork workflows use read-only repository permissions and no scoring credentials; external contributors may require the repository's normal workflow approval. Before publishing scores, maintainers must verify exact case IDs, configuration, coverage denominators, and engine/judge outputs, not just counts.
