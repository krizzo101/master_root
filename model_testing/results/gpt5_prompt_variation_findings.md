## GPT-5 Prompt Optimization Findings (from prompt-variation evals)

### Scope
- Models: gpt-5, gpt-5-mini
- API: Responses API (no output cap by default)
- Sweeps: prompt variants (baseline, self_reflection, preambles), reasoning_effort (minimal, medium), verbosity (low, medium), one-turn vs two-turn
- Tasks: Python function (Fibonacci), bugfix, optimization, simple React TSX component

### Key findings
- One-turn with strong finalization instruction is sufficient for coding tasks; two-turn adds large latency with limited quality gains in these tests.
- Latency and token usage scale with verbosity and reasoning_effort. Minimal/low is fastest; medium/medium is a good balance.
- self_reflection helps low-effort runs keep quality while staying concise; preambles improve structure and narration but cost more.
- Code outputs consistently produced a single fenced code block; Python syntax and Fibonacci tests passed in sweeps.
- No empty outputs when using finalization instruction and retry-on-empty.

### Recommended defaults (coding)
- reasoning_effort: medium (default), minimal for quick utilities, high only for complex multi-step tasks.
- verbosity: medium for balanced detail; low for terse scripts; high for tutorials/audits.
- turns: one-turn with finalization instruction; reserve two-turn for agentic plan→execute flows.

### Cost/performance guidance
- Use verbosity to control length instead of prompt rewrites.
- Prefer minimal/low when speed matters; medium/medium for completeness.
- Keep preambles for workflows needing visible plan/progress; otherwise baseline/self_reflection is cost-efficient.

### Prompt patterns that worked
- Finalization: ensure a single fenced code block and a closing “Final Answer:” cue.
- self_reflection: brief rubric-before-answer improved consistency at low effort.
- tool_preambles: better structure and explainability, at higher cost.

### Practical defaults to adopt
- Default profile: reasoning=medium, verbosity=medium, one-turn, finalization instruction ON.
- Fast profile: reasoning=minimal, verbosity=low, self_reflection variant.

### How to reproduce (examples)
- Full one-turn sweep (gpt-5):
  - python model_testing/gpt5_prompt_variation_eval.py --model gpt-5 --concurrency 20 --save-raw --validate-python --turns one --variants baseline,self_reflection,preambles --reasoning minimal,medium --verbosity low,medium --price-in 2.0 --price-out 10.0 --log-file results_gpt5/run_gpt5.log --results-dir results_gpt5
- Costed, focused A/B:
  - python model_testing/gpt5_prompt_variation_eval.py --model gpt-5-mini --variants baseline,self_reflection --reasoning minimal,medium --verbosity low,medium --turns one --concurrency 20 --save-raw --validate-python --price-in 2.0 --price-out 10.0 --log-file results_gpt5/run_cost.log --results-dir results_gpt5

### Files of record
- Report: results_gpt5/gpt5_prompt_variation_report.md
- Metrics: results_gpt5/gpt5_prompt_variation_results.json
- Logs: results_gpt5/run_*.log
- Raw outputs: results_gpt5/raw/

### Prompt templates (copy/paste)

- System coding preface (optional; use via `--system`):

```
Write code for clarity first. Prefer readable, maintainable solutions with clear names and straightforward control flow. Avoid overly clever one-liners unless requested. Keep narration concise; focus verbosity inside code comments only when essential.
```

- Finalization (always include):

```
<finalization>
- At the very end, add a line starting with 'Final Answer:'
- For code tasks, produce a single fenced code block as the final deliverable.
</finalization>
```

- Self-reflection (good with minimal/low):

```
<self_reflection>
- Think of a brief internal rubric for quality.
- Iterate privately until confident.
</self_reflection>
```

- Tool preambles (structured plan and summary):

```
<tool_preambles>
- Rephrase the goal concisely.
- Outline a short plan of steps.
- Summarize completion distinctly at the end.
</tool_preambles>
```

- Persistence (use for agentic flows; not needed for simple one-turn codegen):

```
<persistence>
- Keep going until the task is fully completed.
- Do not hand back early due to uncertainty.
</persistence>
```

- Minimal reasoning nudge (for speed):

```
Give only what is necessary to satisfy the task. Provide a short bullet list of key steps, then the final code block. Avoid long explanations.
```

- Example composed coding prompt (baseline, one-turn):

```
<finalization>
- At the very end, add a line starting with 'Final Answer:'
- For code tasks, produce a single fenced code block as the final deliverable.
</finalization>

Implement a Python function that returns the nth Fibonacci number using an iterative approach with O(1) extra space. Add type hints and a short docstring.
Return only the code in a single fenced code block.
```

### Parameter usage (Responses API)
- Reasoning effort: reasoning={"effort": "minimal|low|medium|high"}
- Verbosity: text={"verbosity": "low|medium|high"}
- Two-turn follow-up: append "\n\nNow produce your Final Answer as requested above." and pass previous_response_id.
