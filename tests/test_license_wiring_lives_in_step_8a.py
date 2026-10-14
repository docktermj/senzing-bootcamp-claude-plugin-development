"""Data collection Step 8a sub-step 5 states the license wiring once, and measures what it wired (#592).

A Bootcamper who applied a license key at Step 8a could have the limit measured without it.
Three defects sat at one step:

1. **No re-source between the edit and the measurement.** Module 2's env script exports
   `SENZING_ENGINE_CONFIGURATION_JSON` from `config/engine_config.json` only when it is sourced,
   and nothing between sub-step 5 (apply) and sub-step 7 (measure) said to source it again. The
   measuring program read the configuration from before the key, so sub-step 7 could record the
   built-in figure with the `(engine configuration in force)` marker: the measured-but-incomplete
   case INV-295 forbids.
2. **A relative path.** `"LICENSEFILE": "licenses/g2.lic"` was written, while Module 2 Step 8
   requires every path value in `config/engine_config.json` to be absolute.
3. **Module 2 and Module 4 disagreed on the key.** Module 2 said a Base64 key is wired as
   `LICENSESTRINGBASE64`; Step 8a decoded every Base64 key to `licenses/g2.lic` and wired only
   `LICENSEFILE`, and Data processing Phase B's pointer repeated the decode.

Decided in #592 (rev 1): a Base64 key goes into the engine-config `PIPELINE` section inline as
`LICENSESTRINGBASE64`; a `.lic` file is copied to `licenses/g2.lic` and wired as `LICENSEFILE`
with an absolute path. Sub-step 5 is the one statement of that wiring; Module 2's license note,
Phase B and graduation point at it (INV-300).

Re-checked on MCP server 1.38.1, 2026-10-14: `search_docs(query='LICENSEFILE PIPELINE engine
configuration license file path')` returns *"Points to a license file received from Senzing. For
existing licenses only. All new licenses use `LICENSESTRINGBASE64`."*, and
`sdk_guide(topic='load', language='python', platform='linux_apt', record_count=10000)` names
`LICENSESTRINGBASE64` (inline, preferred) or `LICENSEFILE` (a `.lic` path) in the `PIPELINE`
section. Those facts stay in the server (INV-080); this file pins only the plugin's own wiring.

**Every site is found by a scan, not a list of line numbers.** Each Markdown block under
`plugins/` (listed by `_corpus.corpus_files`, cut by `_wrapped_text.blocks` so a wrapped phrase is
one phrase, INV-346) that names `LICENSEFILE` or `LICENSESTRINGBASE64` must be sub-step 5 itself
or a registered pointer whose block carries the phrase that points to sub-step 5. A block that
names a key without describing the wiring is registered apart, with its reason, and may not say
"wire". So a new block that restates the wiring somewhere else fails until it is reduced to a
pointer and registered. The discovery is carried over from the competing approach in #592's race.

⚠️ What the scan cannot see: a site outside `plugins/` or in a file that is not Markdown, and a
registered pointer that restates the wiring beside its pointer phrase.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _corpus import corpus_files
from _wrapped_text import blocks

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_2 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
MODULE_4 = SKILLS / "module-04-data-collection" / "SKILL.md"
PHASE_B = SKILLS / "module-06-data-processing" / "phaseB-load-first-source.md"
GRADUATION = SKILLS / "graduation" / "SKILL.md"

RESOURCE_POSIX = "`source src/scripts/senzing-env.sh`"
RESOURCE_WINDOWS = "`. .\\src\\scripts\\senzing-env.ps1`"
#: The decode this issue retired, in its POSIX and Windows forms.
OLD_DECODES = ("base64 --decode", "FromBase64String")
#: The relative path value the old sub-step wrote.
RELATIVE_LICENSEFILE = '"LICENSEFILE": "licenses/g2.lic"'

#: Either engine-config license key, as a whole token.
KEY = re.compile(r"\b(LICENSEFILE|LICENSESTRINGBASE64)\b")

#: The one statement of the wiring: (file, a phrase inside its block).
STATEMENT = (MODULE_4, "5. **Apply a Senzing License Key (options 1–2).**")

#: Registered pointers: (file, a phrase inside the block, the phrase that points to sub-step 5).
POINTERS = (
    (MODULE_2, "A `PIPELINE` license key remains the other supported route",
     "which is what Module 4 Step 8a sub-step 5 wires"),
    (PHASE_B, "**The apply procedure already exists — point at it, do not restate it (INV-300).**",
     "Module 4 Step 8a **sub-step 5**"),
    (GRADUATION, "- **License** — where the license lives",
     "as Data collection Step 8a sub-step 5 wired it"),
    (GRADUATION, "Also show the `PIPELINE` alternative as a comment",
     "matching Data collection's wiring"),
)

#: Blocks that name a key without describing the bootcamp's wiring: (file, phrase, reason).
NOT_THE_WIRING = (
    (MODULE_2, "shows license only as the `PIPELINE` keys",
     "INV-194's note on which server route answers: it quotes what one `sdk_guide` topic shows"),
)


def flat(text):
    return " ".join(text.split())


def between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i + len(start))]


def sub_step_5(text):
    return between(text, "5. **Apply a Senzing License Key", "6. **Obtain a Senzing License Key")


def base64_bullet(step):
    return between(step, "**Base64 key →", "**`.lic` file →")


def lic_bullet(step):
    return between(step, "**`.lic` file →", "⚠️ The Windows forms above")


def phase_b_pointer(text):
    return flat(between(text, "**The apply procedure already exists", "**Then re-measure"))


def graduation_license_line(text):
    return flat(between(text, "- **License** — where the license lives", "- **Where things are**"))


def module_2_note(text):
    return flat(between(text, "A `PIPELINE` license key remains the other supported route",
                        "The record capacity **is** looked up"))


def plugin_markdown():
    """``{path: text}`` for every shipped Markdown file under `plugins/`."""
    return {p: p.read_text(encoding="utf-8") for p in corpus_files("plugins", suffixes={".md"})}


def key_blocks(texts):
    """``(path, block)`` for each Markdown block in ``texts`` naming either key, collapsed."""
    found = []
    for path, text in sorted(texts.items()):
        for block in blocks(text):
            flat_block = flat(" ".join(line for _, line in block))
            if KEY.search(flat_block):
                found.append((path, flat_block))
    return found


def registered(path, block):
    """The registry row whose phrase sits in ``block`` of ``path``, else None."""
    rows = [STATEMENT] + [row[:2] for row in POINTERS] + [row[:2] for row in NOT_THE_WIRING]
    return next((row for row in rows if row[0] == path and row[1] in block), None)


def site_problems(texts):
    """Every block naming a key that is not sub-step 5 or a registered site that keeps its role."""
    problems = []
    for path, block in key_blocks(texts):
        row = registered(path, block)
        where = path.relative_to(REPO_ROOT).as_posix() if path.is_absolute() else str(path)
        if row is None:
            problems.append(f"{where}: unregistered block names the license key: {block[:110]}")
            continue
        pointer = next((ptr for f, phrase, ptr in POINTERS if (f, phrase) == row), None)
        if pointer is not None and pointer not in block:
            problems.append(f"{where}: pointer no longer points to sub-step 5: {block[:110]}")
        if any((f, phrase) == row for f, phrase, _ in NOT_THE_WIRING) and "wire" in block.lower():
            problems.append(f"{where}: a block registered as not the wiring describes it: "
                            f"{block[:110]}")
    return problems


def wires_base64_inline(step):
    """The Base64 bullet wires `LICENSESTRINGBASE64` and decodes nothing."""
    bullet = flat(base64_bullet(step))
    return ("`LICENSESTRINGBASE64`" in bullet and "It is not decoded to a file" in bullet
            and not any(d in bullet for d in OLD_DECODES))


def resources_before_measuring(step):
    """Both re-source forms follow the wiring inside sub-step 5, before sub-step 7 runs."""
    wiring_end = step.find("⚠️ The Windows forms above")
    return (wiring_end != -1
            and step.find(RESOURCE_POSIX, wiring_end) != -1
            and step.find(RESOURCE_WINDOWS, wiring_end) != -1
            and "Sub-step 7 runs only after this re-source" in flat(step))


def pointer_agrees(pointer):
    """A pointer names `LICENSESTRINGBASE64` for a Base64 key and does not decode it."""
    return ("`LICENSESTRINGBASE64`" in pointer and "`LICENSEFILE`" in pointer
            and "decodes a Base64 key" not in pointer)


class SubStep5WiresEachFormByItsKey(unittest.TestCase):

    def setUp(self):
        self.step = sub_step_5(MODULE_4.read_text(encoding="utf-8"))

    def test_a_base64_key_goes_inline_as_licensestringbase64(self):
        self.assertTrue(wires_base64_inline(self.step))

    def test_it_goes_in_the_pipeline_section(self):
        self.assertIn("Each form goes into the `PIPELINE` section of `config/engine_config.json`",
                      flat(self.step))

    def test_the_bootcamper_runs_the_command_on_both_platforms(self):
        """🚨 The key never passes through chat: the agent writes a placeholder, not the key."""
        bullet = flat(base64_bullet(self.step))
        self.assertIn("sed -i.bak 's|__SENZING_LICENSE_BASE64__|<BASE64_STRING>|' "
                      "config/engine_config.json", bullet)
        self.assertIn(".Replace('__SENZING_LICENSE_BASE64__', '<BASE64_STRING>')", bullet)
        self.assertIn("Never ask the bootcamper to paste a license key into chat", flat(self.step))
        self.assertIn("never print or quote its `LICENSESTRINGBASE64` value", bullet)

    def test_a_lic_file_is_wired_as_licensefile_with_an_absolute_path(self):
        bullet = flat(lic_bullet(self.step))
        self.assertIn("`LICENSEFILE`, with an absolute path", bullet)
        self.assertIn("the absolute path of `licenses/g2.lic` under the project root", bullet)

    def test_the_absolute_path_rule_is_cited_not_restated(self):
        self.assertIn("SDK setup's (Module 2) Step 8 requires every path value in "
                      "`config/engine_config.json` to be absolute", flat(lic_bullet(self.step)))

    def test_the_binary_check_is_on_the_lic_path_only(self):
        self.assertIn("`file licenses/g2.lic`", lic_bullet(self.step))
        self.assertNotIn("`file licenses/g2.lic`", base64_bullet(self.step))

    def test_no_relative_path_is_written(self):
        self.assertNotIn(RELATIVE_LICENSEFILE, MODULE_4.read_text(encoding="utf-8"))

    def test_license_custom_is_recorded_for_both_forms(self):
        tail = flat(self.step[self.step.index("Then, for either form"):])
        self.assertIn("record `license: custom` in `config/bootcamp_preferences.yaml`", tail)


class SubStep5ReSourcesBeforeSubStep7Measures(unittest.TestCase):

    def setUp(self):
        self.module = MODULE_4.read_text(encoding="utf-8")
        self.step = sub_step_5(self.module)

    def test_both_platforms_re_source_after_the_wiring(self):
        self.assertTrue(resources_before_measuring(self.step))

    def test_it_cites_module_2s_env_script_section(self):
        self.assertIn("(SDK setup's (Module 2) Step 3, \"Create the project-local environment "
                      "script\")", flat(self.step))

    def test_it_names_the_failure_it_prevents(self):
        self.assertIn("the measured-but-incomplete case INV-295 forbids", flat(self.step))

    def test_sub_step_7_says_it_follows_the_re_source(self):
        self.assertIn("7. **Detect the active license's record limit (after sub-step 5 applies a "
                      "custom key and re-sources the env script).**", flat(self.module))


class TheOtherSitesPointAtSubStep5AndAgree(unittest.TestCase):

    def test_module_2s_note_names_both_keys_and_sub_step_5(self):
        note = module_2_note(MODULE_2.read_text(encoding="utf-8"))
        self.assertIn("`LICENSEFILE` for a `.lic` path", note)
        self.assertIn("`LICENSESTRINGBASE64` for an inline Base64 key", note)
        self.assertIn("which is what Module 4 Step 8a sub-step 5 wires", note)

    def test_module_2s_handoff_no_longer_says_licensefile_alone(self):
        self.assertNotIn("decoding/placing a `.lic` or Base64 key, wiring `LICENSEFILE`",
                         flat(MODULE_2.read_text(encoding="utf-8")))

    def test_phase_bs_pointer_agrees(self):
        pointer = phase_b_pointer(PHASE_B.read_text(encoding="utf-8"))
        self.assertTrue(pointer_agrees(pointer))
        self.assertIn("`LICENSEFILE` with an absolute path", pointer)
        self.assertIn("re-sources the env script", pointer)

    def test_phase_b_stays_a_pointer(self):
        """INV-300: the commands live in sub-step 5 only."""
        text = flat(PHASE_B.read_text(encoding="utf-8"))
        self.assertIn("Module 4 Step 8a **sub-step 5**", text)
        self.assertNotIn("__SENZING_LICENSE_BASE64__", text)

    def test_graduation_says_where_each_form_lives(self):
        line = graduation_license_line(GRADUATION.read_text(encoding="utf-8"))
        self.assertIn("Data collection Step 8a sub-step 5", line)
        self.assertIn("inline in `config/engine_config.json` (`LICENSESTRINGBASE64`)", line)
        self.assertIn("`licenses/g2.lic` (`LICENSEFILE`)", line)

    def test_no_skill_decodes_a_base64_key_any_more(self):
        offenders = []
        for path, body in sorted(plugin_markdown().items()):
            for decode in OLD_DECODES:
                if decode in body:
                    offenders.append((str(path.relative_to(REPO_ROOT)), decode))
        self.assertEqual([], offenders)


class EveryBlockNamingAKeyIsSubStep5OrPointsToIt(unittest.TestCase):
    """The sites are found by a scan of `plugins/`, so a new one is caught when it appears."""

    def test_every_block_naming_a_key_is_registered_and_keeps_its_role(self):
        self.assertEqual([], site_problems(plugin_markdown()))

    def test_every_registered_site_is_found_once(self):
        found = key_blocks(plugin_markdown())
        rows = [STATEMENT] + [row[:2] for row in POINTERS] + [row[:2] for row in NOT_THE_WIRING]
        for path, phrase in rows:
            with self.subTest(site=phrase):
                self.assertEqual(1, sum(1 for p, b in found if p == path and phrase in b))

    def test_the_scan_reads_more_than_the_registered_files(self):
        """The discovery walks every shipped Markdown file, not just the four named above."""
        texts = plugin_markdown()
        self.assertGreater(len(texts), 4)
        self.assertTrue({MODULE_2, MODULE_4, PHASE_B, GRADUATION} <= set(texts))


class NegativeControls(unittest.TestCase):
    """Each check fails on the text #592 replaced."""

    OLD_STEP = (
        "5. **Apply a Senzing License Key (options 1–2).** 🚨 Never ask the bootcamper to paste a "
        "license key into chat. Decode/place it to `licenses/g2.lic`:\n"
        "   - **Base64 key →** Linux/macOS: `echo '<BASE64_STRING>' | base64 --decode > "
        "licenses/g2.lic`. It is not decoded to a file.\n"
        "   - **`.lic` file →** `cp <path-to>/g2.lic licenses/g2.lic`\n\n"
        "   ⚠️ The Windows forms above are unverified.\n\n"
        "   Then add `LICENSEFILE` to the engine config PIPELINE section\n"
        "   (`\"PIPELINE\": { \"LICENSEFILE\": \"licenses/g2.lic\" }`) and record `license: custom`"
        " in `config/bootcamp_preferences.yaml`. Continue to sub-step 7 to detect the limit.\n")
    OLD_POINTER = ("Module 4 Step 8a **sub-step 5** decodes a Base64 key or copies a `.lic` to "
                   "`licenses/g2.lic`, adds `LICENSEFILE` to the engine-config PIPELINE section, "
                   "and records `license: custom`.")

    def test_the_old_decode_is_caught(self):
        self.assertFalse(wires_base64_inline(self.OLD_STEP))

    def test_a_removed_re_source_is_caught(self):
        self.assertFalse(resources_before_measuring(self.OLD_STEP))

    def test_a_re_source_before_the_wiring_is_caught(self):
        early = self.OLD_STEP.replace("Decode/place it", RESOURCE_POSIX + " " + RESOURCE_WINDOWS
                                      + " Sub-step 7 runs only after this re-source. Decode/place it")
        self.assertFalse(resources_before_measuring(early))

    def test_the_old_relative_path_is_caught(self):
        self.assertIn(RELATIVE_LICENSEFILE, self.OLD_STEP)

    def test_the_old_phase_b_pointer_is_caught(self):
        self.assertFalse(pointer_agrees(self.OLD_POINTER))

    def test_a_pointer_with_licensefile_for_a_base64_key_is_caught(self):
        self.assertFalse(pointer_agrees("sub-step 5 decodes a Base64 key and adds `LICENSEFILE`."))

    NEW_SITE = SKILLS / "module-07-query-visualize-discover" / "SKILL.md"
    RESTATED = ("Before you load, wire the license yourself: put a Base64 key into the `PIPELINE`"
                " section as `LICENSESTRINGBASE64`, or a `.lic` as `LICENSEFILE`.")

    def test_a_new_unregistered_site_restating_the_wiring_is_caught(self):
        texts = plugin_markdown()
        texts[self.NEW_SITE] = texts.get(self.NEW_SITE, "") + "\n\n" + self.RESTATED + "\n"
        problems = site_problems(texts)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("unregistered block names the license key", problems[0])

    def test_a_pointer_that_stops_pointing_is_caught(self):
        texts = plugin_markdown()
        texts[PHASE_B] = texts[PHASE_B].replace("Module 4 Step 8a\n  **sub-step 5**",
                                                "Module 4 Step 8a\n  **the license step**", 1)
        self.assertNotEqual(texts[PHASE_B], PHASE_B.read_text(encoding="utf-8"))
        self.assertTrue(any("no longer points" in p for p in site_problems(texts)))

    def test_a_not_the_wiring_block_that_describes_it_is_caught(self):
        texts = plugin_markdown()
        texts[MODULE_2] = texts[MODULE_2].replace(
            "shows license only as the `PIPELINE` keys",
            "shows license only as the `PIPELINE` keys, which you wire as", 1)
        self.assertTrue(any("registered as not the wiring" in p for p in site_problems(texts)))


if __name__ == "__main__":
    unittest.main()
