# Offline Evaluation

Run golden tests to guard quality, cost, and latency.

## Running
```bash
python -m ultimate_discord_intelligence_bot.services.eval_harness run \
  --dataset datasets/golden/v1/analyze_claim.jsonl \
  --task analyze_claim --router-profile baseline --seed 42 \
  --out out/eval/analyze_claim_v1.json
```

Reports are written as JSON and Markdown in `out/eval/`.
