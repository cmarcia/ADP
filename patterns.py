"""Small, framework-independent building blocks for agent workflows."""

from collections import Counter
from typing import Callable, Hashable, Iterable, List, Sequence, TypeVar


Task = TypeVar("Task")
Result = TypeVar("Result")
Context = TypeVar("Context")
Part = TypeVar("Part")
Vote = TypeVar("Vote", bound=Hashable)


def errand(task: Task, agent: Callable[[Task], Result]) -> Result:
    """Delegate a focused task and return its result to the caller."""
    return agent(task)


def guardrail(
    task: Task,
    agent: Callable[[Task], Result],
    input_allowed: Callable[[Task], bool],
    output_allowed: Callable[[Result], bool],
) -> Result:
    """Reject disallowed inputs before execution and outputs before return."""
    if not input_allowed(task):
        raise ValueError("Input rejected by guardrail")
    result = agent(task)
    if not output_allowed(result):
        raise ValueError("Output rejected by guardrail")
    return result


def resampler(
    task: Task,
    agent: Callable[[Task], Result],
    acceptable: Callable[[Result], bool],
    max_attempts: int,
) -> Result:
    """Generate until a result is accepted or the attempt limit is exhausted."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    for _ in range(max_attempts):
        result = agent(task)
        if acceptable(result):
            return result
    raise ValueError("No acceptable result within the attempt limit")


def voter(task: Task, agent: Callable[[Task], Vote], samples: int) -> Vote:
    """Return the most frequent result; ties go to the first result seen."""
    if samples < 1:
        raise ValueError("samples must be at least 1")
    votes = Counter(agent(task) for _ in range(samples))
    return votes.most_common(1)[0][0]


def retriever(
    task: Task,
    retrieve: Callable[[Task], Iterable[Context]],
    agent: Callable[[Task, Sequence[Context]], Result],
) -> Result:
    """Retrieve context for a task and pass it to the agent."""
    context = list(retrieve(task))
    return agent(task, context)


def decompose_process_recompose(
    task: Task,
    decompose: Callable[[Task], Iterable[Part]],
    process: Callable[[Part], Result],
    recompose: Callable[[List[Result]], Context],
) -> Context:
    """Process each subtask in order and combine the results."""
    return recompose([process(part) for part in decompose(task)])
