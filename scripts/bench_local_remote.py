#!/usr/bin/env python
"""
Compare local vLLM latency vs a remote provider (via litellm) for a short prompt.
Requires: .env populated (OPENROUTER_API_KEY or OPENAI_API_KEY), vLLM installed and a local model active.

Usage:
  python scripts/bench_local_remote.py --prompt "Say hello" --iters 3

Notes:
- Local uses vLLM LLM() with current VLLM_MODEL_ID
- Remote uses litellm.completion with a default remote model id (configurable via REMOTE_MODEL_ID)
"""

from __future__ import annotations

import argparse
import os
import time
from statistics import mean

from dotenv import load_dotenv

load_dotenv()


def bench_local(prompt: str, iters: int) -> float:
    from vllm import LLM, SamplingParams

    model = os.environ.get("VLLM_MODEL_ID")
    max_len = int(os.environ.get("VLLM_MAX_MODEL_LEN", "1024"))
    llm = LLM(model=model, tensor_parallel_size=1, max_model_len=max_len, gpu_memory_utilization=0.95)
    _ = SamplingParams(temperature=0.2, max_tokens=64)
    # warmup
    llm.generate(["ping"])  # warm the graph
    times = []
    for _ in range(iters):
        t0 = time.perf_counter()
        out = llm.generate([prompt])
        _ = out[0].outputs[0].text
        times.append(time.perf_counter() - t0)
    return mean(times)


def bench_remote(prompt: str, iters: int) -> float:
    import litellm

    # Choose a default remote model (adjust if using OpenAI or another provider)
    remote_model = os.environ.get("REMOTE_MODEL_ID", "openrouter/anthropic/claude-3-haiku")
    times = []
    for _ in range(iters):
        t0 = time.perf_counter()
        resp = litellm.completion(model=remote_model, messages=[{"role": "user", "content": prompt}])
        _ = resp.choices[0].message["content"]
        times.append(time.perf_counter() - t0)
    return mean(times)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default="Give one use for RL routing.")
    ap.add_argument("--iters", type=int, default=3)
    args = ap.parse_args()

    print("Benchmarking...\n")
    try:
        tl = bench_local(args.prompt, args.iters)
        print(f"Local vLLM avg latency over {args.iters} iters: {tl:.2f}s")
    except Exception as e:
        print("Local benchmark failed:", e)

    try:
        tr = bench_remote(args.prompt, args.iters)
        print(f"Remote avg latency over {args.iters} iters: {tr:.2f}s")
    except Exception as e:
        print("Remote benchmark failed:", e)


if __name__ == "__main__":
    main()
