# Agent Design Patterns

These are small, dependency-free Python building blocks for agentic workflows.
They accept callables, so an application can supply its own model, tools, and
retrieval system. They do not themselves call a model or provide an agent runtime.
Run the examples with Python 3.9 or later.

## Patterns

| Pattern | When to use it | How it works here |
| --- | --- | --- |
| **Errand** | Delegate a focused, bounded task, such as looking up a status, without handing over the entire workflow. | `errand(task, agent)` calls the delegated agent once and returns its result to the caller. The caller decides what context to share and how to use the result. |
| **Guardrail** | Enforce application rules on requests and responses. | `guardrail(task, agent, input_allowed, output_allowed)` rejects an input before calling the agent, or rejects its output before returning it, with `ValueError`. |
| **Resampler** | Try again when a generated answer fails a known acceptance check. | `resampler(task, agent, acceptable, max_attempts)` returns the first accepted result, or raises `ValueError` after the bounded number of attempts. |
| **Voter** | Reduce reliance on a single answer by comparing multiple samples. | `voter(task, agent, samples)` returns the plurality winner among hashable results. A tie goes to the first result seen; `samples` must be positive. |
| **Retriever** | Ground an answer in relevant external information. | `retriever(task, retrieve, agent)` retrieves context for the task, materializes it as a list, and calls `agent(task, context)`. The retrieval callable is responsible for selecting and ranking sources. |
| **Decompose–process–recompose** | Split a larger task into manageable subtasks and combine their results. | `decompose_process_recompose(task, decompose, process, recompose)` processes subtasks in order and passes their results as a list to `recompose`. Empty decompositions produce an empty list for `recompose`. |

These patterns can be composed. For example, a planner can decompose a request,
delegate each part as an errand, retrieve supporting context, and guard the final
answer. The validators, decomposition, retrieval, and recomposition are
application-specific. Agent and callback exceptions propagate to the caller;
the resampler retries rejected results, not exceptions.

Guardrails are not a security sandbox: validate and authorize tool calls and
side effects separately, before they execute. Treat retrieved material as
untrusted data, not instructions, and control access to sources. Voting and
resampling add cost and do not guarantee correctness; correlated samples can
agree on the same wrong answer. Choose meaningful checks and independent samples
where possible.

## Runnable example

The following deterministic stand-ins illustrate the interfaces without requiring
an API key or network connection. Replace them with real agents and retrieval
functions for an application.

```python
from patterns import (
    decompose_process_recompose, errand, guardrail, resampler, retriever, voter,
)

print(errand("check status", lambda task: f"Completed: {task}"))

print(guardrail("hello", str.upper, bool, lambda result: len(result) <= 10))

answers = iter(["", "usable answer"])
print(resampler("question", lambda _: next(answers), bool, max_attempts=2))

votes = iter(["yes", "no", "yes"])
print(voter("question", lambda _: next(votes), samples=3))

documents = {"hours": ["The library closes at 5pm."]}
print(retriever(
    "hours",
    lambda query: documents.get(query, []),
    lambda query, context: f"{query}: {context[0]}" if context else "No source found",
))

print(decompose_process_recompose(
    "one,two",
    lambda task: task.split(","),
    str.upper,
    lambda results: " + ".join(results),
))
```

Save the example as a Python file in the repository and run it with `python3`,
or paste it into a Python interpreter started in the repository. Run the tests
with:

```sh
python3 -m unittest -v test_patterns
```
