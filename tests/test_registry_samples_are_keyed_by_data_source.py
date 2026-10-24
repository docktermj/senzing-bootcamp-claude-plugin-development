"""Every YAML sample of `config/data_sources.yaml` keys its entries by DATA_SOURCE under `sources:`.

Module 4 Step 2's **Record the intended band per source** sample was a YAML list item
(`- name: MERIDIAN_CRM`, with no `sources:` key), while every other site says `sources:` is a
mapping keyed by DATA_SOURCE: Module 4's registry note ("an empty `sources:` mapping", "Under the
source's DATA_SOURCE key in `sources:`"), Module 1 Step 11 ("a `sources:` mapping keyed by
DATA_SOURCE") and graduation. Option 5 of the own-data path tells the guide to write its entry
"shaped as *Record the intended band per source* above shows", so a guide copying the sample
wrote a registry its readers do not parse as written. The `scenario_intent` sample beside it
wrote `sources:` with only a comment under it, which parses as null rather than as the empty
mapping the registry note describes.

What this file pins, over every fenced YAML block (info string `yaml` or `yml`) in shipped
Markdown under `plugins/senzing-bootcamp/`:

1. **Which blocks are registry samples, by shape.** A block with a `sources:` key, or a
   source-entry shape: a `name:` together with a registry field (`provenance`,
   `quality_intent`, `file_path`, `record_count`, `mapping_status`). A `sources:`-only test
   would have missed the defect, because the list sample had no `sources:` key. A key-only
   fragment (part of one entry, no `name:`), such as the regeneration keys of
   `quality_intent`, is not a registry sample.
2. **Every registry sample** has a top-level `sources:`; holds no `- name:` list item; writes
   an empty `sources:` as `{}`; and keys each entry under `sources:` by a DATA_SOURCE code
   (an upper-case identifier) whose `name:`, when shown, is that same code. Every `name:` sits
   directly inside a `sources:` entry.
3. **The two Module 4 samples** read as #784 left them: the band sample is `sources:` →
   `MERIDIAN_CRM:` → its fields, and the `scenario_intent` sample's `sources:` is `{}`.

Negative controls: the original list-shaped sample with no `sources:` key fails; `sources:`
holding a `- name:` list fails; a comment-only `sources:` fails; a lower-case entry key and a
`name:` that differs from its key fail. A key-only fragment passes untouched.

The YAML is read by indentation with the stdlib only, as the rest of `tests/` does (no YAML
library); the shapes the samples use are plain block mappings, block lists and `{}`.

Source issue: #784. Invariants applied: INV-300 (one definition of the registry, every sample
agrees with it), INV-402.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _corpus import REPO_ROOT, corpus_files  # noqa: E402

PLUGIN = "plugins/senzing-bootcamp"
COLLECTION = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
              / "module-04-data-collection" / "SKILL.md")

#: The registry fields that, beside a `name:`, make a block a source-entry sample.
REGISTRY_FIELDS = frozenset(("provenance", "quality_intent", "file_path", "record_count",
                             "mapping_status"))

#: A DATA_SOURCE code as the registry keys it.
DATA_SOURCE = re.compile(r"[A-Z][A-Z0-9_]*")

FENCE_OPEN = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})[ \t]*(?P<info>[^\s`]*)")
LINE = re.compile(r"^(?P<indent> *)(?P<dash>- +)?(?P<key>[A-Za-z_][\w-]*):(?:[ \t]+(?P<val>.*?))?"
                  r"[ \t]*$")


def yaml_blocks(markdown):
    """``(line_number, text)`` for each fenced `yaml`/`yml` block, dedented by its fence."""
    lines = markdown.splitlines()
    out, i = [], 0
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        fence, indent = m.group("fence"), len(m.group("indent"))
        close = re.compile(r"^[ \t]*" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*$")
        j = i + 1
        while j < len(lines) and not close.match(lines[j]):
            j += 1
        if m.group("info").lower() in ("yaml", "yml"):
            body = [ln[indent:] if ln[:indent].strip() == "" else ln.lstrip()
                    for ln in lines[i + 1:j]]
            out.append((i + 1, "\n".join(body) + "\n"))
        i = j + 1
    return out


def uncomment(value):
    """``value`` without a trailing ` # comment` (values here carry no quoted `#`)."""
    return re.sub(r"(?:^|\s+)#.*$", "", value or "").strip()


def nodes(text):
    """The block's key lines as dicts, each with its ``parent`` index (None at top level).

    Blank lines, comment lines and list scalars (`- "text"`) are skipped. A line's parent is the
    nearest earlier key line indented less than it.

    Line-scoped by design (#784): a YAML key and its value sit on one line, and the structure is
    read from each line's indentation, so the read is per line and matches no prose phrase."""
    out = []
    for raw in text.splitlines():
        m = LINE.match(raw.expandtabs(2))
        if not m:
            continue
        col = len(m.group("indent"))
        parent = None
        for k in range(len(out) - 1, -1, -1):
            if out[k]["col"] < col:
                parent = k
                break
        out.append({"col": col, "dash": bool(m.group("dash")), "key": m.group("key"),
                    "val": uncomment(m.group("val")), "parent": parent})
    return out


def is_registry_sample(text):
    """A `sources:` key, or a `name:` together with a registry field."""
    keys = {n["key"] for n in nodes(text)}
    return "sources" in keys or ("name" in keys and bool(keys & REGISTRY_FIELDS))


def registry_problems(text):
    """Why ``text`` is not a registry sample keyed by DATA_SOURCE under `sources:`; [] if it is."""
    ns = nodes(text)
    problems = []
    if any(n["dash"] and n["key"] == "name" for n in ns):
        problems.append("a `- name:` list item: a source entry is keyed by its DATA_SOURCE")
    tops = [i for i, n in enumerate(ns) if n["key"] == "sources" and n["parent"] is None]
    if not tops:
        problems.append("no top-level `sources:` key")
        return problems
    top = tops[0]
    entries = [i for i, n in enumerate(ns) if n["parent"] == top]
    value = ns[top]["val"]
    if value:
        if value != "{}":
            problems.append("`sources:` has the inline value %r, not a mapping or `{}`" % value)
    elif not entries:
        problems.append("an empty `sources:` must be written `sources: {}`")
    for i in entries:
        n = ns[i]
        if n["dash"]:
            problems.append("`sources:` holds a list item (`- %s:`), not a mapping keyed by "
                            "DATA_SOURCE" % n["key"])
            continue
        if not DATA_SOURCE.fullmatch(n["key"]):
            problems.append("entry key %r is not a DATA_SOURCE code" % n["key"])
        if n["val"] and not n["val"].startswith("{"):
            problems.append("entry %r is a scalar, not a mapping of its fields" % n["key"])
        for c in ns:
            if c["parent"] == i and c["key"] == "name" and c["val"] != n["key"]:
                problems.append("entry %r has `name: %s`, not its own key" % (n["key"], c["val"]))
    for n in ns:
        if n["key"] == "name" and not n["dash"]:
            p = n["parent"]
            if p is None or ns[p]["parent"] != top:
                problems.append("a source entry's `name:` sits outside a `sources:` entry")
    return problems


def shipped_samples():
    """``(where, text)`` for every registry sample in shipped Markdown."""
    out = []
    for path in corpus_files(PLUGIN, suffixes=(".md",)):
        for line, text in yaml_blocks(Path(path).read_text(encoding="utf-8")):
            if is_registry_sample(text):
                out.append(("%s:%d" % (Path(path).relative_to(REPO_ROOT).as_posix(), line), text))
    return out


#: The defect's shape as #784 found it: a list item, no `sources:` key.
LIST_SAMPLE = """\
- name: MERIDIAN_CRM
  provenance: synthesized
  quality_intent:
    target_band: "70-79"        # one of: ">=80", "70-79", "<70"
"""

#: `sources:` holding a `- name:` list.
SOURCES_LIST = """\
version: "1"
sources:
  - name: MERIDIAN_CRM
    provenance: synthesized
"""

#: A comment-only `sources:`, which parses as null.
SOURCES_NULL = """\
version: "1"
sources:
  # one entry per source
"""

#: A key-only fragment: part of one entry's `quality_intent`, no `name:` (Module 4's
#: regeneration keys).
KEY_ONLY = """\
target_band: ">=80"           # was the band the original generation targeted
regenerated:
  from_band: "70-79"
  at: "<ISO 8601>"
gaps: [...]
measured_score: 86.0          # written by the self-check, never by hand
"""

GOOD = """\
version: "1"
sources:
  MERIDIAN_CRM:
    name: MERIDIAN_CRM
    provenance: synthesized
    quality_intent:
      target_band: "70-79"
      gaps:
        - "phone missing ~70% of records"
"""


class EveryShippedRegistrySampleIsAMapping(unittest.TestCase):

    def test_the_scan_finds_both_module_4_samples(self):
        where = [w for w, _ in shipped_samples()]
        mod4 = [w for w in where if "module-04-data-collection/SKILL.md" in w]
        self.assertGreaterEqual(len(mod4), 2, where)

    def test_each_sample_is_keyed_by_data_source_under_sources(self):
        for where, text in shipped_samples():
            with self.subTest(sample=where):
                self.assertEqual(registry_problems(text), [])


class TheModule4SamplesReadAsFixed(unittest.TestCase):

    def samples(self):
        blocks = yaml_blocks(COLLECTION.read_text(encoding="utf-8"))
        return [t for _, t in blocks if is_registry_sample(t)]

    def test_the_band_sample_is_keyed_by_meridian_crm(self):
        band = [t for t in self.samples() if "quality_intent:" in t]
        self.assertEqual(len(band), 1)
        ns = nodes(band[0])
        top = next(i for i, n in enumerate(ns) if n["key"] == "sources")
        entry = next(i for i, n in enumerate(ns) if n["parent"] == top)
        self.assertEqual(ns[entry]["key"], "MERIDIAN_CRM")
        fields = {n["key"]: n["val"] for n in ns if n["parent"] == entry}
        self.assertEqual(fields.get("name"), "MERIDIAN_CRM")
        self.assertEqual(fields.get("provenance"), "synthesized")
        self.assertIn("quality_intent", fields)

    def test_the_scenario_intent_sample_writes_an_empty_mapping(self):
        scen = [t for t in self.samples() if "scenario_intent:" in t]
        self.assertEqual(len(scen), 1)
        self.assertRegex(scen[0], r"(?m)^sources: \{\}[ \t]*#")


class TheGuardsControls(unittest.TestCase):

    def test_a_good_sample_passes(self):
        self.assertTrue(is_registry_sample(GOOD))
        self.assertEqual(registry_problems(GOOD), [])

    def test_negative_control_the_original_list_sample_fails(self):
        self.assertTrue(is_registry_sample(LIST_SAMPLE))
        problems = registry_problems(LIST_SAMPLE)
        self.assertIn("no top-level `sources:` key", problems)
        self.assertTrue(any("`- name:` list item" in p for p in problems))

    def test_negative_control_sources_holding_a_name_list_fails(self):
        self.assertTrue(is_registry_sample(SOURCES_LIST))
        problems = registry_problems(SOURCES_LIST)
        self.assertTrue(any("`- name:` list item" in p for p in problems))
        self.assertTrue(any("holds a list item" in p for p in problems))

    def test_negative_control_a_comment_only_sources_fails(self):
        self.assertTrue(is_registry_sample(SOURCES_NULL))
        self.assertIn("an empty `sources:` must be written `sources: {}`",
                      registry_problems(SOURCES_NULL))

    def test_negative_control_a_lower_case_key_fails(self):
        bad = GOOD.replace("  MERIDIAN_CRM:", "  meridian_crm:")
        self.assertTrue(any("not a DATA_SOURCE code" in p for p in registry_problems(bad)))

    def test_negative_control_a_name_unlike_its_key_fails(self):
        bad = GOOD.replace("name: MERIDIAN_CRM", "name: OTHER_CRM")
        self.assertTrue(any("not its own key" in p for p in registry_problems(bad)))

    def test_negative_control_a_shipped_sample_rewritten_as_a_list_fails(self):
        text = COLLECTION.read_text(encoding="utf-8")
        reverted = text.replace("  sources:\n    MERIDIAN_CRM:\n      name: MERIDIAN_CRM\n",
                                "  - name: MERIDIAN_CRM\n", 1)
        self.assertNotEqual(reverted, text)
        found = []
        for _, t in yaml_blocks(reverted):
            if is_registry_sample(t):
                found.extend(registry_problems(t))
        self.assertIn("no top-level `sources:` key", found)

    def test_a_key_only_fragment_is_not_a_registry_sample(self):
        self.assertFalse(is_registry_sample(KEY_ONLY))

    def test_the_shipped_key_only_fragment_is_not_checked(self):
        blocks = yaml_blocks(COLLECTION.read_text(encoding="utf-8"))
        frags = [t for _, t in blocks if "regenerated:" in t]
        self.assertEqual(len(frags), 1)
        self.assertFalse(is_registry_sample(frags[0]))


if __name__ == "__main__":
    unittest.main()
