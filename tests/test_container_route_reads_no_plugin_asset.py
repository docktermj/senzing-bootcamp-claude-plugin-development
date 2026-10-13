"""Nothing that runs inside the SDK container reads a plugin asset by its plugin path.

Issue #525. On SDK setup's `docker` route the SDK container mounts only the project, so the
plugin's `scripts/` does not exist inside it. Two shipped instructions reached for it anyway:
Module 5's quality pages inlined `${CLAUDE_PLUGIN_ROOT}/scripts/vendor/d3.v7.min.js` and the brand
tokens with no statement of where the page is built, and Module 7's server took its palette from
`${CLAUDE_PLUGIN_ROOT}/scripts/brand_tokens.py` at runtime while its D3 copy had no destination.
The fix states where each asset is read:

- **Host.** Module 5 step 6 generates the quality page on the host on every route, the `docker`
  route included, at the anchor `quality-page-runs-on-the-host`; step 15 links there (INV-300).
- **Carried into the project.** Module 7's server copies the brand-token **values** into its own
  code in every language, and resolves D3 from `src/server/vendor/d3.v7.min.js`, copied on the
  host at first build. Module 3b's Truth Set server already does this (#490).

**The site set is derived, not listed (INV-246).** A *plugin asset* is a file under the plugin's
`scripts/` that nothing runs: not a Python entry point (no `__main__` guard) and not a hook
command in `hooks/hooks.json`. Today that is `brand_tokens.py`, `vendor/d3.v7.min.js` and a few
library modules and images. A *site* is a section of any shipped skill file (from a heading to
the next heading of the same or a higher level) that names an asset by its plugin path, either
`${CLAUDE_PLUGIN_ROOT}/scripts/<asset>` or the skill-relative `../../scripts/<asset>` (INV-252).
Every site must dispose of every asset it names, in the same section, in one of three ways:

1. **host**: the section says the artifact is generated on the host on every route, or links to
   an anchor whose text says so;
2. **project copy**: the section names a project path for that asset, `src/…/<asset name>` or
   `data/…/<asset name>`;
3. **values** (Python modules only): the section says to copy or replicate the token values.

A section that disposes of nothing is reported with its file, line and asset, so a new skill that
tells a server to read a plugin asset fails here without anyone adding it to a list. Two sites are
exempt, each with its reason in `EXEMPT`; an exemption that stops matching a site fails too.

**What this guard cannot see**, said plainly:

- **Whether the code runs in the container at all.** No container runs in this suite, and a
  section does not say where its code runs in any form a scan can read reliably. So the guard
  asks every asset-path mention to say where the asset is read, container or not.
- **Disposition is per section and per asset, not per sentence.** A section that disposes of an
  asset for one code path credits every mention of that asset in it: Module 3b Step 2's project
  copy (2.1) is for the Python path, and its "replicate the token values" is for the others.
- **An asset named without a plugin path** (a bare `brand_tokens.py`), a plugin **entry point
  run** inside the container (#490's shape, guarded by
  `test_truthset_container_route_runs_a_project_copy.py`), and any file outside `skills/`.
- **Whether a disposition is true, or a guide follows it.** The phrases are a vocabulary; a
  section that disposes of an asset in new words is reported, and the fix is to widen the
  vocabulary (INV-282), not to exempt the site.

The four statements #525's acceptance names are also asserted at their sites, found by anchor
and heading rather than line number (INV-246), with negative controls on in-memory copies of the
shipped text. Prose is read wrap-aware (INV-346).

Stdlib only; nothing under the plugin is imported (INV-108).

Enforces **INV-091** (its #525 note, applied 2026-10-13), **INV-081**, **INV-252** and **INV-300**.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines as _match_lines

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "senzing-bootcamp"
SCRIPTS = PLUGIN / "scripts"
SKILLS = PLUGIN / "skills"
HOOKS = PLUGIN / "hooks" / "hooks.json"

M5_P1 = "module-05-data-quality-mapping/phase1-quality-assessment.md"
M5_P2 = "module-05-data-quality-mapping/phase2-data-mapping.md"
M7_P1 = "module-07-query-visualize-discover/phase1-query-visualize.md"

HOST_ANCHOR = "quality-page-runs-on-the-host"
BRAND = "brand_tokens.py"
D3 = "vendor/d3.v7.min.js"

#: Sites that name a plugin asset and run no code, keyed (skill-relative file, section heading).
EXEMPT = {
    ("bootcamp-onboarding/ground-rules.md", "Visual deliverables (Senzing brand)"):
        "the statement of record for the brand rule: it binds every deliverable and builds "
        "none, so the step that builds each one carries the disposition",
    ("module-03b-truthset-visualization/visualization-api-reference.md", "Modal chrome"):
        "names where the token values come from; #525 leaves it out of scope because both "
        "dispositions satisfy it, and the step that builds the server carries one",
}

#: The sites #525 fixed. A floor, not the site set: it stops the scan degrading to silence.
KNOWN_SITES = frozenset({(M5_P1, BRAND), (M5_P1, D3), (M5_P2, BRAND), (M5_P2, D3),
                         (M7_P1, BRAND), (M7_P1, D3)})

HOST = re.compile(r"(?i)\bgenerated? (?:the|this) [\w -]{1,40}? on the host, on every route")
VALUES = re.compile(r"(?i)\b(?:copy|copies|replicate)\w*\s+the\s+(?:brand-)?token\s+\**values")
LINK = re.compile(r"\]\(([^)#\s]*)#([\w-]+)\)")
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def match_lines(text, pattern):
    """`_wrapped_text.match_lines` (INV-346), taking a compiled pattern or a string."""
    return _match_lines(text, pattern if hasattr(pattern, "finditer") else re.compile(pattern))


def plugin_assets():
    """Files under `scripts/` that nothing runs, as POSIX paths relative to `scripts/`."""
    hooks = set(re.findall(r"scripts/([\w.-]+)", HOOKS.read_text(encoding="utf-8")))
    found = set()
    for path in SCRIPTS.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(SCRIPTS).as_posix()
        if rel in hooks:
            continue
        if path.suffix == ".py" and re.search(
                r"""__name__\s*==\s*['"]__main__['"]""", path.read_text(encoding="utf-8")):
            continue
        found.add(rel)
    return found


def asset_path(asset):
    """An asset named by its plugin path, `${CLAUDE_PLUGIN_ROOT}/…` or skill-relative."""
    return re.compile(r"(?:\$\{CLAUDE_PLUGIN_ROOT\}/|\.\./\.\./)scripts/" + re.escape(asset)
                      + r"(?![\w.-])")


def project_copy(asset):
    """A project path for the asset, e.g. `src/server/vendor/d3.v7.min.js`."""
    name = re.escape(asset.rsplit("/", 1)[-1])
    return re.compile(r"`(?:src|data)/(?:[\w.-]+/)*" + name + "`")


def headings(lines):
    """`(index, level, text)` for each ATX heading outside a code fence."""
    out, fence = [], None
    for i, line in enumerate(lines):
        opener = FENCE.match(line)
        if opener and (fence is None or opener.group(1)[0] == fence):
            fence = None if fence else opener.group(1)[0]
            continue
        if fence:
            continue
        m = HEADING.match(line)
        if m:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def sections(text):
    """`(heading, first line index, end line index, text)` for each heading's section.

    A section runs from its heading to the next heading of the same or a higher level, so it
    holds its subsections. Text before the first heading is a section with heading "".
    """
    lines = text.split("\n")
    marks = headings(lines)
    out = []
    if not marks or marks[0][0] > 0:
        first = marks[0][0] if marks else len(lines)
        out.append(("", 0, first, "\n".join(lines[:first])))
    for n, (i, level, title) in enumerate(marks):
        end = next((j for j, lv, _ in marks[n + 1:] if lv <= level), len(lines))
        out.append((title, i, end, "\n".join(lines[i:end])))
    return out


def anchored_text(text, anchor):
    """The text from `<a id="anchor">` to the next heading, or None when there is no anchor."""
    lines = text.split("\n")
    tag = '<a id="%s"></a>' % anchor
    start = next((i for i, line in enumerate(lines) if tag in line), None)
    if start is None:
        return None
    nxt = next((i for i, _, _ in headings(lines) if i > start), len(lines))
    return "\n".join(lines[start:nxt])


def links_to_host_statement(rel, section_text, files):
    """True when the section links to an anchor whose text says the artifact runs on the host."""
    for target, anchor in LINK.findall(section_text):
        target_rel = rel if not target else (Path(rel).parent / target).as_posix()
        parts = []
        for part in target_rel.split("/"):
            if part == "..":
                parts = parts[:-1]
            elif part not in ("", "."):
                parts.append(part)
        body = files.get("/".join(parts))
        segment = anchored_text(body, anchor) if body is not None else None
        if segment is not None and match_lines(segment, HOST):
            return True
    return False


def derived_sites(files, assets):
    """Every `(file, line, heading, asset, section text)` naming an asset by plugin path.

    One record per asset per innermost section: a site is reported in the section whose heading
    is nearest above it, and that section (with its subsections) is what must dispose of it.
    """
    out = []
    for rel, text in sorted(files.items()):
        all_sections = sections(text)
        for asset in sorted(assets):
            hits = match_lines(text, asset_path(asset))
            seen = set()
            for line in hits:
                idx = line - 1
                owner = max((s for s in all_sections if s[1] <= idx < s[2]),
                            key=lambda s: s[1])
                if owner[1] in seen:
                    continue
                seen.add(owner[1])
                out.append((rel, line, owner[0], asset, owner[3]))
    return out


def disposition(rel, asset, section_text, files):
    """How the section disposes of the asset: 'host', 'project copy', 'values', or None."""
    if match_lines(section_text, HOST) or links_to_host_statement(rel, section_text, files):
        return "host"
    if match_lines(section_text, project_copy(asset)):
        return "project copy"
    if asset.endswith(".py") and match_lines(section_text, VALUES):
        return "values"
    return None


def undisposed(files, assets):
    """`file:line [heading] asset` for each derived, unexempt site that disposes of nothing."""
    found = []
    for rel, line, heading, asset, body in derived_sites(files, assets):
        if (rel, heading) in EXEMPT:
            continue
        if disposition(rel, asset, body, files) is None:
            found.append("%s:%d [%s] %s" % (rel, line, heading, asset))
    return found


def shipped_skills():
    return {p.relative_to(SKILLS).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(SKILLS.rglob("*.md"))}


def section_named(text, prefix):
    """The text of the first section whose heading starts with `prefix`."""
    for title, _, _, body in sections(text):
        if title.startswith(prefix):
            return body
    raise AssertionError("no section headed %r" % prefix)


class EverySiteSaysWhereItsAssetIsRead(unittest.TestCase):
    """INV-246: the sites are derived from the corpus, and each one is checked."""

    @classmethod
    def setUpClass(cls):
        cls.files = shipped_skills()
        cls.assets = plugin_assets()

    def test_the_asset_set_is_not_vacuous(self):
        for asset in (BRAND, D3):
            with self.subTest(asset=asset):
                self.assertIn(asset, self.assets,
                              "the asset derivation lost %s, so every site naming it went "
                              "unchecked" % asset)
        for entry in ("senzing_viz_server.py", "capture_screenshots.py", "session-start.py"):
            with self.subTest(entry=entry):
                self.assertNotIn(entry, self.assets,
                                 "%s is run, not read; it is not an asset" % entry)

    def test_the_site_scan_finds_every_known_site(self):
        found = {(rel, asset) for rel, _, _, asset, _ in derived_sites(self.files, self.assets)}
        self.assertEqual(set(), KNOWN_SITES - found,
                         "the scan no longer sees sites #525 fixed, so it is inspecting a set "
                         "it cannot see")

    def test_every_site_disposes_of_every_asset_it_names(self):
        self.assertEqual(
            [], undisposed(self.files, self.assets),
            "a shipped skill names a plugin asset by its plugin path in a section that never "
            "says where the asset is read. The SDK container mounts only the project, so code "
            "run there cannot read the plugin's `scripts/`. Say the artifact is generated on "
            "the host on every route (or link to such a statement), copy the asset to a named "
            "project path, or copy its values into the code (#525, INV-091).")

    def test_every_exemption_still_matches_a_site(self):
        live = {(rel, heading) for rel, _, heading, _, _ in
                derived_sites(self.files, self.assets)}
        self.assertEqual(set(), set(EXEMPT) - live,
                         "an exemption names a section that no longer names a plugin asset; "
                         "remove it so it cannot hide a site added later")

    def test_the_fixed_sites_dispose_as_intended(self):
        expected = {(M5_P1, BRAND): "host", (M5_P1, D3): "host",
                    (M5_P2, BRAND): "host", (M5_P2, D3): "host",
                    (M7_P1, BRAND): "values", (M7_P1, D3): "project copy"}
        got = {(rel, asset): disposition(rel, asset, body, self.files)
               for rel, _, _, asset, body in derived_sites(self.files, self.assets)
               if (rel, asset) in expected}
        self.assertEqual(expected, got)


class TheGuardBites(unittest.TestCase):
    """Negative controls: each edit, made in memory, is reported."""

    @classmethod
    def setUpClass(cls):
        cls.files = shipped_skills()
        cls.assets = plugin_assets()

    def mutated(self, rel, old, new, count=1):
        files = dict(self.files)
        self.assertIn(old, files[rel], "the control's fixture text is gone from %s" % rel)
        files[rel] = files[rel].replace(old, new, count)
        return files

    def reported(self, files):
        return {f.split(":")[0] + " " + f.rsplit(" ", 1)[-1] for f in
                undisposed(files, self.assets)}

    def test_module_7_reverting_to_a_runtime_palette_read_is_reported(self):
        text = self.files[M7_P1]
        start = text.index("  - ⛔ **(INV-081, INV-091) Copy the brand-token values")
        end = text.index("  - ⛔ **(INV-091) Copy the D3 asset into the project")
        old_bullet = ("- Render offline with the vendored D3 asset inlined, no CDN (INV-091), "
                      "and take palette/typography\n  from `${CLAUDE_PLUGIN_ROOT}/scripts/"
                      "brand_tokens.py` (INV-081; skill-relative fallback\n  `../../scripts/"
                      "brand_tokens.py`, INV-252).\n")
        head = text.rindex("- Render offline with the vendored D3 asset inlined", 0, start)
        files = dict(self.files)
        files[M7_P1] = text[:head] + old_bullet + text[end:]
        self.assertIn("%s %s" % (M7_P1, BRAND), self.reported(files))
        self.assertTrue(match_lines(section_named(files[M7_P1], "3c."), RUNTIME_PALETTE))

    def test_module_7_losing_its_d3_destination_is_reported(self):
        files = self.mutated(M7_P1, "`src/server/vendor/d3.v7.min.js`", "the project", -1)
        self.assertIn("%s %s" % (M7_P1, D3), self.reported(files))

    def test_module_5_losing_its_host_statement_is_reported_at_both_pages(self):
        files = self.mutated(M5_P1, "on the host, on every route", "where the SDK runs")
        got = self.reported(files)
        for rel in (M5_P1, M5_P2):
            for asset in (BRAND, D3):
                with self.subTest(rel=rel, asset=asset):
                    self.assertIn("%s %s" % (rel, asset), got)

    def test_step_15_losing_its_link_is_reported(self):
        files = self.mutated(M5_P2, "(phase1-quality-assessment.md#%s)" % HOST_ANCHOR, "")
        got = self.reported(files)
        self.assertIn("%s %s" % (M5_P2, D3), got)
        self.assertNotIn("%s %s" % (M5_P1, D3), got)

    def test_a_new_site_nobody_listed_is_reported(self):
        files = dict(self.files)
        files["module-99-new/SKILL.md"] = (
            "# New module\n\n## 3. Build the dashboard\n\nThe server reads\n"
            "`${CLAUDE_PLUGIN_ROOT}/scripts/vendor/d3.v7.min.js` at startup.\n")
        self.assertIn("module-99-new/SKILL.md %s" % D3, self.reported(files))

    def test_a_wrapped_host_statement_still_counts(self):
        """INV-346: the disposition phrase is matched across a line wrap."""
        files = dict(self.files)
        files["module-99-new/SKILL.md"] = (
            "# New module\n\n## 3. Build the page\n\nGenerate the page on the host,\non every "
            "route. Inline `${CLAUDE_PLUGIN_ROOT}/scripts/vendor/d3.v7.min.js`.\n")
        self.assertNotIn("module-99-new/SKILL.md %s" % D3, self.reported(files))


#: The pre-#525 runtime read: the server told to take its palette from the plugin path.
RUNTIME_PALETTE = re.compile(
    r"(?i)\btake (?:the )?(?:palette|colou?rs?)[\w/ ]*? from "
    r"`\$\{CLAUDE_PLUGIN_ROOT\}/scripts/brand_tokens\.py`")


class Module5StatesWhereThePageIsBuilt(unittest.TestCase):
    """Step 6 holds the statement; step 15 links to it and carries no copy (INV-300)."""

    @classmethod
    def setUpClass(cls):
        cls.p1 = (SKILLS / M5_P1).read_text(encoding="utf-8")
        cls.p2 = (SKILLS / M5_P2).read_text(encoding="utf-8")

    def test_the_statement_is_in_step_6_at_the_visualization_checkpoint(self):
        step6 = section_named(self.p1, "6. Assess data quality")
        self.assertIn('<a id="%s"></a>' % HOST_ANCHOR, step6)
        self.assertLess(step6.index("**Visualization checkpoint:**"),
                        step6.index('<a id="%s"></a>' % HOST_ANCHOR))

    def test_the_statement_names_the_docker_route_and_the_reason(self):
        body = anchored_text(self.p1, HOST_ANCHOR)
        for label, pattern in (
                ("host on every route", HOST),
                ("the docker route", r"`docker`\s+route"),
                ("no SDK is needed", r"(?i)needs no SDK"),
                ("scripts/ resolves only on the host",
                 r"(?i)plugin's `scripts/`.{0,120}?resolves only on the host"),
                ("the citation", r"INV-300")):
            with self.subTest(element=label):
                self.assertTrue(match_lines(body, pattern), "step 6 lost: " + label)

    def test_step_15_links_and_does_not_restate(self):
        step15 = section_named(self.p2, "15. Quality analysis")
        self.assertTrue(match_lines(
            step15, r"\]\(phase1-quality-assessment\.md#%s\)" % HOST_ANCHOR),
            "step 15 must link to step 6's statement")
        for copy in (r"(?i)on the host", r"(?i)every route", r"`docker`", r"(?i)needs no SDK"):
            with self.subTest(copy=copy):
                self.assertFalse(match_lines(step15, copy),
                                 "step 15 restates step 6's statement (INV-300)")


class Module7CarriesItsAssetsInTheProject(unittest.TestCase):
    """The palette bullet and its D3 sub-bullet, found by their text in step 3c."""

    @classmethod
    def setUpClass(cls):
        cls.section = section_named((SKILLS / M7_P1).read_text(encoding="utf-8"), "3c.")

    def test_the_bullet_is_where_it_was(self):
        self.assertTrue(match_lines(
            self.section, r"Render offline with the vendored D3 asset inlined, no CDN"))

    def test_the_palette_is_copied_as_values_in_every_language(self):
        for label, pattern in (
                ("copy the values into the server's code",
                 r"Copy the brand-token values into the server's own code"),
                ("every language, Python included", r"in every language, Python included"),
                ("never imports brand_tokens.py", r"never imports `brand_tokens\.py`"),
                ("no plugin path at runtime",
                 r"never reads any `\$\{CLAUDE_PLUGIN_ROOT\}` path at runtime"),
                ("Module 3b's precedent linked",
                 r"\]\(\.\./module-03b-truthset-visualization/phase1-visualization\.md\)")):
            with self.subTest(element=label):
                self.assertTrue(match_lines(self.section, pattern), "Module 7 lost: " + label)

    def test_the_palette_is_not_read_from_the_plugin_at_runtime(self):
        self.assertEqual([], match_lines(self.section, RUNTIME_PALETTE),
                         "Module 7 again tells the server to take its palette from the "
                         "plugin path, which the SDK container cannot see (#525)")

    def test_d3_has_a_named_destination_copied_on_the_host_at_first_build(self):
        self.assertTrue(match_lines(
            self.section,
            r"At first build, copy it on the host from `\$\{CLAUDE_PLUGIN_ROOT\}/scripts/vendor/"
            r"d3\.v7\.min\.js`.{0,120}? to `src/server/vendor/d3\.v7\.min\.js`"))

    def test_the_refusal_stays_and_names_the_recovery(self):
        self.assertTrue(match_lines(
            self.section, r"`src/server/vendor/d3\.v7\.min\.js` is later missing, the server "
                          r"names `d3\.v7\.min\.js` and writes no page"))


if __name__ == "__main__":
    unittest.main()
