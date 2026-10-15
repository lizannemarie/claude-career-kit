# Split-decision eval

Decides whether a career-kit flow should run inline or fan out to subagents, using measured dollar cost and quality instead of raw token counts. Method, background and current status: [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md#the-split-decision-eval).

```bash
python3 evals/split-decision/run_eval.py --dry-run            # free: print the plan
python3 evals/split-decision/run_eval.py --sizes 5 10 20 40   # real runs (spends usage)
```

You need a logged-in `claude` CLI (`claude -p "hi"` should answer). Results go to `results/<timestamp>/` (gitignored): `runs.jsonl` holds every run, and `report.md` holds the tables, the break-even N per flow, and the `split_thresholds` block to paste into `career-kit.config.json`.
