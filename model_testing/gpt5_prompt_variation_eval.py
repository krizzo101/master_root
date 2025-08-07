#!/usr/bin/env python3
"""
GPT-5 Prompt Variation Evaluation Script (Responses API)

- Focused on GPT-5 series only (gpt-5, gpt-5-mini)
- Tests multiple prompt patterns and parameter settings:
  - reasoning_effort: minimal, low, medium, high
  - verbosity: low, medium, high (via text={"verbosity": ...})
  - prompt variants: baseline, self_reflection, tool_preambles, persistence, finalization
  - optional two-turn flow using previous_response_id (planning -> finalization)
- No hard max_output_tokens cap (omit parameter)
- Async with bounded concurrency; structured JSON + Markdown report

Usage:
  python gpt5_prompt_variation_eval.py \
    --model gpt-5-mini \
    --concurrency 12 \
    --log-file gpt5_prompt_eval.log \
    --results-dir results_gpt5 \
    --quick

Environment:
  Requires OPENAI_API_KEY set. Optionally set MODEL_TEST_CONCURRENCY.
"""

import argparse
import asyncio
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from openai import AsyncOpenAI


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def log_line(path: str, message: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{_now()} | {message}\n")


BASELINE_CODE_TASKS = {
    "python_function": (
        "Implement a Python function that returns the nth Fibonacci number using an iterative approach with O(1) extra space. Add type hints and a short docstring.\n"
        "Return only the code in a single fenced code block."
    ),
    "design_pattern": (
        "Refactor an event notification system to use the Observer pattern in Python. Include Subject and Observer abstractions and a small demo. Return code in a single fenced code block."
    ),
}

BASE_PREFIX = ""
SELF_REFLECTION = (
    "<self_reflection>\n- Think of a brief internal rubric for quality.\n- Iterate privately until confident.\n</self_reflection>"
)
TOOL_PREAMBLES = (
    "<tool_preambles>\n- Rephrase the goal concisely.\n- Outline a short plan.\n- Summarize completion at the end.\n</tool_preambles>"
)
PERSISTENCE = (
    "<persistence>\n- Keep going until the task is fully completed.\n- Do not hand back early due to uncertainty.\n</persistence>"
)
FINALIZATION = (
    "<finalization>\n- At the very end, add a line starting with 'Final Answer:'\n- For code tasks, produce a single fenced code block as the final deliverable.\n</finalization>"
)

PROMPT_VARIANTS = {
    "baseline": [BASE_PREFIX, FINALIZATION],
    "self_reflection": [SELF_REFLECTION, FINALIZATION],
    "preambles": [TOOL_PREAMBLES, FINALIZATION],
    "persistent": [PERSISTENCE, FINALIZATION],
    "self_reflection+preambles": [SELF_REFLECTION, TOOL_PREAMBLES, FINALIZATION],
}

REASONING_LEVELS = ["minimal", "low", "medium", "high"]
VERBOSITY_LEVELS = ["low", "medium", "high"]


@dataclass
class EvalConfig:
    model: str
    concurrency: int
    log_file: str
    results_dir: str
    quick: bool


@dataclass
class EvalResult:
    model: str
    task: str
    variant: str
    reasoning_effort: str
    verbosity: str
    two_turn: bool
    execution_time: float
    input_tokens: int
    output_tokens: int
    empty_output: bool
    had_retry: bool
    output_preview: str


class GPT5PromptEvaluator:
    def __init__(self, cfg: EvalConfig) -> None:
        self.cfg = cfg
        self.client = AsyncOpenAI()
        self.sem = asyncio.Semaphore(cfg.concurrency)
        self.results: List[EvalResult] = []

    async def _create(self, **kwargs) -> Any:
        async with self.sem:
            return await self.client.responses.create(**kwargs)

    @staticmethod
    def _extract_text(resp: Any) -> str:
        text = getattr(resp, "output_text", None)
        if text:
            return text
        try:
            data = resp.model_dump()
        except Exception:
            data = getattr(resp, "to_dict", lambda: {})()
        pieces: List[str] = []
        for item in data.get("output") or []:
            itype = item.get("type")
            if itype == "message":
                for c in item.get("content") or []:
                    ctype = c.get("type")
                    if ctype in ("output_text", "text", "input_text"):
                        t = c.get("text")
                        if isinstance(t, dict):
                            val = t.get("value") or t.get("text")
                        else:
                            val = t
                        if val:
                            pieces.append(str(val))
            elif itype == "reasoning":
                for s in item.get("summary", []) or []:
                    if s.get("type") in ("summary_text", "text"):
                        val = s.get("text")
                        if val:
                            pieces.append(str(val))
        return "\n".join(pieces)

    @staticmethod
    def _preview(text: str, limit: int = 800) -> str:
        if not text:
            return ""
        return text if len(text) <= limit else text[:limit] + f"... [truncated {len(text)-limit} chars]"

    def _compose_prompt(self, variant: str, task_text: str) -> str:
        parts = PROMPT_VARIANTS[variant]
        return ("\n\n".join(parts) + "\n\n" + task_text).strip()

    async def _eval_single(
        self,
        task_name: str,
        task_text: str,
        variant: str,
        reasoning_effort: str,
        verbosity: str,
        two_turn: bool,
    ) -> None:
        model = self.cfg.model
        start = time.time()
        had_retry = False
        input_tokens = output_tokens = 0

        prompt = self._compose_prompt(variant, task_text)

        kwargs: Dict[str, Any] = {
            "model": model,
            "input": prompt,
            "text": {"verbosity": verbosity},
        }
        if reasoning_effort:
            kwargs["reasoning"] = {"effort": reasoning_effort}

        log_line(self.cfg.log_file, f"Request → model={model} task={task_name} variant={variant} effort={reasoning_effort} verbosity={verbosity} two_turn={two_turn}")
        try:
            resp = await self._create(**kwargs)
        except Exception as e:
            log_line(self.cfg.log_file, f"ERROR create: {e}")
            return

        if two_turn:
            prev_id = getattr(resp, "id", None)
            followup = prompt + "\n\nNow produce your Final Answer as requested above."
            kwargs2 = {
                "model": model,
                "input": followup,
                "previous_response_id": prev_id,
                "text": {"verbosity": verbosity},
            }
            if reasoning_effort:
                kwargs2["reasoning"] = {"effort": reasoning_effort}
            try:
                resp = await self._create(**kwargs2)
            except Exception as e:
                log_line(self.cfg.log_file, f"ERROR followup: {e}")
                return

        text = self._extract_text(resp)
        usage = getattr(resp, "usage", None)
        if usage is not None:
            input_tokens = int(getattr(usage, "input_tokens", 0))
            output_tokens = int(getattr(usage, "output_tokens", 0))

        if not (text or "").strip():
            had_retry = True
            retry_prompt = prompt + "\n\nFinal Answer:"
            kwargs_retry = {
                "model": model,
                "input": retry_prompt,
                "text": {"verbosity": verbosity},
            }
            try:
                resp_retry = await self._create(**kwargs_retry)
                text = self._extract_text(resp_retry) or text
                usage2 = getattr(resp_retry, "usage", None)
                if usage2 is not None:
                    input_tokens = int(getattr(usage2, "input_tokens", input_tokens))
                    output_tokens = int(getattr(usage2, "output_tokens", output_tokens))
            except Exception as e:
                log_line(self.cfg.log_file, f"ERROR retry: {e}")

        elapsed = time.time() - start
        result = EvalResult(
            model=model,
            task=task_name,
            variant=variant,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            two_turn=two_turn,
            execution_time=elapsed,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            empty_output=not bool(text and text.strip()),
            had_retry=had_retry,
            output_preview=self._preview(text),
        )
        self.results.append(result)
        log_line(self.cfg.log_file, f"Result ← {asdict(result)}")

    async def run(self) -> Dict[str, Any]:
        os.makedirs(self.cfg.results_dir, exist_ok=True)
        tasks: List[asyncio.Task] = []
        task_items = list(BASELINE_CODE_TASKS.items())
        if self.cfg.quick:
            task_items = task_items[:1]
        for task_name, task_text in task_items:
            for variant in PROMPT_VARIANTS.keys():
                for r in REASONING_LEVELS:
                    for v in VERBOSITY_LEVELS:
                        for two_turn in ([False] if self.cfg.quick else [False, True]):
                            tasks.append(
                                asyncio.create_task(
                                    self._eval_single(task_name, task_text, variant, r, v, two_turn)
                                )
                            )
        await asyncio.gather(*tasks)
        report = self._aggregate()
        self._save(report)
        return report

    def _aggregate(self) -> Dict[str, Any]:
        by_key: Dict[str, Dict[str, Any]] = {}
        for r in self.results:
            key = f"{r.variant} | {r.reasoning_effort} | {r.verbosity} | {'two' if r.two_turn else 'one'}-turn"
            if key not in by_key:
                by_key[key] = {"count": 0, "avg_time": 0.0, "empty_count": 0, "retry_count": 0, "avg_output_tokens": 0.0}
            slot = by_key[key]
            slot["count"] += 1
            slot["avg_time"] += r.execution_time
            slot["avg_output_tokens"] += r.output_tokens
            if r.empty_output:
                slot["empty_count"] += 1
            if r.had_retry:
                slot["retry_count"] += 1
        for k, slot in by_key.items():
            c = max(slot["count"], 1)
            slot["avg_time"] /= c
            slot["avg_output_tokens"] /= c
        return {
            "metadata": {
                "model": self.cfg.model,
                "date": _now(),
                "concurrency": self.cfg.concurrency,
                "quick": self.cfg.quick,
            },
            "variants_summary": by_key,
            "results": [asdict(r) for r in self.results],
        }

    def _save(self, report: Dict[str, Any]) -> None:
        json_path = os.path.join(self.cfg.results_dir, "gpt5_prompt_variation_results.json")
        md_path = os.path.join(self.cfg.results_dir, "gpt5_prompt_variation_report.md")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# GPT-5 Prompt Variation Evaluation\n\n")
            f.write(f"Model: {self.cfg.model}\n\n")
            f.write(f"Date: {_now()}\n\n")
            f.write(f"Concurrency: {self.cfg.concurrency}\n\n")
            f.write("## Summary (by variant | reasoning | verbosity | turns)\n\n")
            for k, v in report["variants_summary"].items():
                f.write(f"- {k}: count={v['count']}, avg_time={v['avg_time']:.2f}s, avg_output_tokens={v['avg_output_tokens']:.0f}, empty={v['empty_count']}, retries={v['retry_count']}\n")
            f.write("\n## Notes\n\n")
            f.write("- Prompts include a finalization instruction; retries occur when the model returns empty text.\n")
            f.write("- Verbosity lever used via text={\\"verbosity\\": ...}.\n")
            f.write("- No max_output_tokens cap is set.\n")


async def main_async(args: argparse.Namespace) -> None:
    cfg = EvalConfig(
        model=args.model,
        concurrency=args.concurrency,
        log_file=args.log_file,
        results_dir=args.results_dir,
        quick=args.quick,
    )
    os.makedirs(os.path.dirname(cfg.log_file) or ".", exist_ok=True)
    log_line(cfg.log_file, f"Starting GPT-5 prompt variation eval | model={cfg.model} | concurrency={cfg.concurrency}")
    evaluator = GPT5PromptEvaluator(cfg)
    await evaluator.run()
    log_line(cfg.log_file, f"Completed. Results saved to {cfg.results_dir}")
    print("✅ Done. See:")
    print(f"- {cfg.results_dir}/gpt5_prompt_variation_results.json")
    print(f"- {cfg.results_dir}/gpt5_prompt_variation_report.md")
    print(f"- Log: {cfg.log_file}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate GPT-5 prompt variations (Responses API)")
    p.add_argument("--model", default=os.environ.get("GPT5_MODEL", "gpt-5-mini"), help="GPT-5 model (gpt-5, gpt-5-mini)")
    p.add_argument("--concurrency", type=int, default=int(os.environ.get("MODEL_TEST_CONCURRENCY", "12")))
    p.add_argument("--log-file", default=os.path.join("results_gpt5", "gpt5_prompt_eval.log"))
    p.add_argument("--results-dir", default="results_gpt5")
    p.add_argument("--quick", action="store_true", help="Reduce task/variants for a fast run")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(main_async(parse_args()))


