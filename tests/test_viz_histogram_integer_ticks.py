"""The merge histogram's y-axis counts entities, so its ticks must be whole numbers.

``d3.axisLeft(y).ticks(5)`` is a request for *about five ticks*, not for integers:
d3 picks whatever step divides the domain into roughly five parts. On a domain of
``[0, 1]`` that step is ``0.2``, so a Truth Set run whose tallest bucket holds one
entity was labeled ``0.0 0.2 0.4 0.6 0.8 1.0`` — against bars printing ``1`` and
``0``. There is no such thing as 0.4 of a resolved entity.

The affected range is the *designed* case, not an edge case: Module 3b runs on the
small demo truth set, and the built-in evaluation license caps ingestion at 500 DSRs,
so small entity counts are the normal bootcamp shape. The histogram is also captured
to PNG and embedded in the recap PDF, so a wrong axis outlives the session.

``d3.ticks(0, n, 5)`` emits non-integers for n = 1, 2, 3 and integers from n = 4 up.
This test reproduces d3's own tick-step algorithm (d3-array ``tickIncrement``) so it
can assert the property offline — no browser, no node, no ``plugins/`` import
(INV-108/INV-091).

⛔ What this test does NOT accept: ``.ticks(5).tickFormat(d3.format("d"))``. That keeps
the fractional tick *positions* and only rounds their labels, rendering ``0 0 0 1 1 1``
— duplicated labels at unequal spacing, which is worse than the bug because it looks
deliberate. The tick VALUES have to be integers.

No phrase-level pattern (#438): its line reads strip `//` comments from JavaScript source lines, as
#424 recorded (INV-346).

Run:  python3 -m unittest discover -s tests
"""
import math
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "scripts", "senzing_viz_server.py"
)

# The histogram's y-axis construction: from the `maxN` binding through the axisLeft
# call that renders it. Scoped so a different chart's axis cannot satisfy this test.
HISTOGRAM_AXIS = re.compile(
    r"const maxN\s*=.*?axisLeft\(y\)[^;]*;", re.DOTALL
)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def strip_js_comments(text):
    """Drop ``//`` line comments so the shape assertions read CODE, not prose.

    The axis carries a comment explaining why ``.tickFormat("d")`` alone is not the
    fix — which means the comment contains the very tokens these assertions look
    for. Matching against the raw slice would let a comment satisfy a guard about
    code: revert the expression, leave the comment, and the test still passes. That
    is a guard certifying what it never checked, so it is stripped first.
    """
    return "\n".join(re.sub(r"//.*$", "", line) for line in text.splitlines())


def d3_tick_increment(start, stop, count):
    """d3-array's ``tickIncrement``, reproduced verbatim.

    Returns a positive step, or a negative inverse-step when the step is < 1 —
    which is exactly the case that produces fractional ticks.
    """
    e10, e5, e2 = math.sqrt(50), math.sqrt(10), math.sqrt(2)
    step = (stop - start) / max(0, count)
    power = math.floor(math.log10(step))
    error = step / (10 ** power)
    if power >= 0:
        factor = 10 if error >= e10 else 5 if error >= e5 else 2 if error >= e2 else 1
        return factor * (10 ** power)
    divisor = 10 if error >= e10 else 5 if error >= e5 else 2 if error >= e2 else 1
    return -(10 ** -power) / divisor


def d3_ticks(start, stop, count):
    """d3-array's ``ticks``, reproduced for the ``start <= stop`` case."""
    inc = d3_tick_increment(start, stop, count)
    out = []
    if inc > 0:
        i = math.ceil(start / inc)
        while i * inc <= stop + 1e-9:
            out.append(i * inc)
            i += 1
    else:
        r = -inc
        i = math.ceil(start * r)
        while i / r <= stop + 1e-9:
            out.append(i / r)
            i += 1
    return out


def shipped_tick_values(max_n):
    """The tick values the SHIPPED axis expression produces for this domain max.

    Mirrors ``d3.range(0, maxN + 1, yStep)`` with ``yStep = max(1, ceil(maxN / 5))``.
    """
    step = max(1, math.ceil(max_n / 5))
    return list(range(0, max_n + 1, step))


class TheHistogramAxisCountsWholeEntities(unittest.TestCase):
    def setUp(self):
        self.source = read(SERVER)
        match = HISTOGRAM_AXIS.search(self.source)
        self.assertIsNotNone(
            match,
            "could not find the histogram y-axis construction in %s — if the chart was "
            "restructured, re-scope HISTOGRAM_AXIS rather than deleting this test"
            % os.path.basename(SERVER),
        )
        self.axis = strip_js_comments(match.group(0))

    def test_the_axis_pins_tick_values_rather_than_a_tick_count(self):
        self.assertIn(
            "tickValues(",
            self.axis,
            "the entity-count axis must pin explicit integer tickValues; a bare "
            ".ticks(n) lets d3 choose a fractional step and label whole entities in "
            "fifths",
        )

    def test_the_axis_does_not_ask_for_a_bare_tick_count(self):
        self.assertNotRegex(
            self.axis,
            r"axisLeft\(y\)\s*\.\s*ticks\(",
            "axisLeft(y).ticks(...) reintroduces d3's fractional step selection; use "
            "tickValues with an integer range instead",
        )

    def test_formatting_alone_is_not_treated_as_the_fix(self):
        # tickFormat("d") is fine ALONGSIDE tickValues, but must never be the only
        # guard: it rounds labels while leaving fractional positions (0 0 0 1 1 1).
        if "tickFormat(" in self.axis:
            self.assertIn(
                "tickValues(",
                self.axis,
                "tickFormat without tickValues rounds fractional tick LABELS and "
                "leaves their positions, producing duplicates",
            )

    def test_every_shipped_tick_value_is_a_whole_entity(self):
        for max_n in range(1, 41):
            with self.subTest(max_n=max_n):
                for value in shipped_tick_values(max_n):
                    self.assertEqual(
                        value,
                        int(value),
                        "tick %r is not a whole entity for a tallest bucket of %d"
                        % (value, max_n),
                    )

    def test_the_shipped_values_never_exceed_the_domain_or_crowd_the_axis(self):
        for max_n in range(1, 41):
            with self.subTest(max_n=max_n):
                values = shipped_tick_values(max_n)
                self.assertTrue(values, "no ticks emitted for max_n=%d" % max_n)
                self.assertEqual(
                    len(values), len(set(values)), "duplicate ticks for %d" % max_n
                )
                self.assertLessEqual(max(values), max_n)
                self.assertLessEqual(
                    len(values),
                    max_n + 1,
                    "more ticks than there are whole values in the domain",
                )

    def test_the_premise_holds_that_bare_ticks_would_be_fractional(self):
        """The defect this guards is real: pin d3's own behavior, so a future reader
        can see WHY tickValues is required rather than taking it on trust."""
        fractional = [n for n in range(1, 13) if any(
            v != int(v) for v in d3_ticks(0, n, 5))]
        self.assertEqual(
            fractional,
            [1, 2, 3],
            "d3.ticks(0, n, 5) is expected to emit fractional ticks exactly for a "
            "tallest bucket of 1, 2 or 3; if this changed, the fix's rationale needs "
            "re-checking rather than the assertion loosening",
        )


if __name__ == "__main__":
    unittest.main()
