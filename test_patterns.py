import unittest

from patterns import (
    decompose_process_recompose,
    errand,
    guardrail,
    resampler,
    retriever,
    voter,
)


class PatternTests(unittest.TestCase):
    def test_errand_returns_delegated_result(self):
        self.assertEqual(errand("status", str.upper), "STATUS")

    def test_guardrail_checks_input_before_agent(self):
        calls = []
        with self.assertRaisesRegex(ValueError, "Input rejected"):
            guardrail("blocked", calls.append, lambda _: False, lambda _: True)
        self.assertEqual(calls, [])

    def test_guardrail_checks_output(self):
        self.assertEqual(guardrail("ok", str.upper, bool, bool), "OK")
        with self.assertRaisesRegex(ValueError, "Output rejected"):
            guardrail("ok", str.upper, bool, lambda _: False)

    def test_resampler_stops_on_first_acceptable_result(self):
        results = iter(["bad", "good", "unused"])
        self.assertEqual(resampler("task", lambda _: next(results), lambda x: x == "good", 3), "good")
        self.assertEqual(next(results), "unused")

    def test_resampler_is_bounded(self):
        calls = []
        with self.assertRaisesRegex(ValueError, "attempt limit"):
            resampler("task", lambda x: calls.append(x), bool, 2)
        self.assertEqual(calls, ["task", "task"])
        with self.assertRaisesRegex(ValueError, "max_attempts"):
            resampler("task", lambda _: self.fail("called"), bool, 0)

    def test_voter_uses_plurality_and_first_seen_tie_break(self):
        votes = iter(["a", "b", "b"])
        self.assertEqual(voter("task", lambda _: next(votes), 3), "b")
        votes = iter(["b", "a"])
        self.assertEqual(voter("task", lambda _: next(votes), 2), "b")
        with self.assertRaisesRegex(ValueError, "samples"):
            voter("task", lambda _: self.fail("called"), 0)

    def test_retriever_passes_task_and_materialized_context(self):
        seen = []

        def agent(task, context):
            seen.append((task, context))
            return "answer"

        self.assertEqual(retriever("question", lambda _: iter(["source"]), agent), "answer")
        self.assertEqual(seen, [("question", ["source"])])
        self.assertEqual(retriever("question", lambda _: [], lambda _, context: context), [])

    def test_decompose_process_recompose_preserves_order(self):
        self.assertEqual(
            decompose_process_recompose("a,b,c", lambda x: x.split(","), str.upper, "-".join),
            "A-B-C",
        )
        self.assertEqual(decompose_process_recompose("task", lambda _: [], str.upper, list), [])

    def test_errors_propagate(self):
        def fail(_):
            raise RuntimeError("agent failed")

        with self.assertRaisesRegex(RuntimeError, "agent failed"):
            resampler("task", fail, bool, 2)
        with self.assertRaisesRegex(RuntimeError, "agent failed"):
            decompose_process_recompose("task", lambda x: [x], fail, list)


if __name__ == "__main__":
    unittest.main()
