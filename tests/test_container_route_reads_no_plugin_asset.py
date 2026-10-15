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
  host at first build. Module 3b's Python path already copies its server into the project (#490).

Issue #601 found the non-Python Truth Set server still reading D3 by its plugin path, passed by
the Python path's copy. The copy into `src/server/vendor/` is now stated once, in Module 3b
2.1's "Any other language" bullet at the anchor `server-d3-project-copy`, and Module 7 step 3c
links there (INV-300). The guard now reads a section's **path branches**: a disposition inside one
branch credits that branch alone.

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

**Path branches (#601).** A *path list* is two or more consecutive top-level bullets that each
open with a bold label and an arrow, such as 2.1's `- **Python** →` and
`- **Any other language** →`; a reader takes one of them. When a site's section holds a path
list, each branch is checked on its own view: the section without the list's other branches. A
branch whose view names the asset by its plugin path and disposes of nothing is reported with
its label, so a copy made on one path no longer passes a site the other path reads. Text outside
the list is in every view and credits every branch.

**What this guard cannot see**, said plainly:

- **Whether the code runs in the container at all.** No container runs in this suite, and a
  section does not say where its code runs in any form a scan can read reliably. So the guard
  asks every asset-path mention to say where the asset is read, container or not.
- **Disposition is per section, per branch and per asset, not per sentence.** Outside a path
  list, a section that disposes of an asset for one code path still credits every mention of
  that asset in it; only a branch written as a path list is told apart. Module 3b Step 2's
  "replicate the token values" sits outside 2.1's list, so it credits both paths, as the brand
  rule intends.
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
M3B_P1 = "module-03b-truthset-visualization/phase1-visualization.md"
M3B_STEP2 = "Step 2: Build and run the visualization server in your chosen programming language"
M3B_21 = "2.1 Choose the path"
OTHER = "Any other language"
D3_COPY_ANCHOR = "server-d3-project-copy"

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

#: The sites #525 and #601 fixed. A floor, not the site set: it stops the scan degrading to
#: silence. Module 7 names D3 by no plugin path since #601 (it links to Module 3b's copy), so its
#: D3 site is gone and Module 3b's two are in its place.
KNOWN_SITES = frozenset({(M5_P1, BRAND), (M5_P1, D3), (M5_P2, BRAND), (M5_P2, D3),
                         (M7_P1, BRAND), (M3B_P1, D3)})

#: The branch sites #601 added: `(file, section heading, branch label, asset)`.
KNOWN_BRANCH_SITES = frozenset({(M3B_P1, M3B_STEP2, "Python", D3),
                                (M3B_P1, M3B_STEP2, OTHER, D3),
                                (M3B_P1, M3B_21, OTHER, D3)})

HOST = re.compile(r"(?i)\bgenerated? (?:the|this) [\w -]{1,40}? on the host, on every route")
VALUES = re.compile(r"(?i)\b(?:copy|copies|replicate)\w*\s+the\s+(?:brand-)?token\s+\**values")
LINK = re.compile(r"\]\(([^)#\s]*)#([\w-]+)\)")
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
BRANCH = re.compile(r"^[-*][ \t]+\*\*([^*\n]+)\*\*[ \t]*→")


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


def path_lists(text):
    """The path lists in a section: each a list of `(label, first line, end line)` items.

    A path list is two or more consecutive top-level bullets that each open with a bold label and
    an arrow. An item runs from its bullet to the next line, outside a code fence, that is not
    blank and not indented: the next bullet, a paragraph or a heading.
    """
    lines = text.split("\n")
    items, current, fence = [], None, None
    for i, line in enumerate(lines):
        opener = FENCE.match(line)
        in_fence = fence is not None
        if opener and (fence is None or opener.group(1)[0] == fence):
            fence = None if fence else opener.group(1)[0]
        if in_fence or not line.strip() or line[0] in " \t":
            continue
        if current is not None:
            items.append((current[0], current[1], i))
            current = None
        m = BRANCH.match(line)
        if m and not opener:
            current = (m.group(1).strip(), i)
    if current is not None:
        items.append((current[0], current[1], len(lines)))
    lists, run = [], []
    for item in items:
        if run and run[-1][2] != item[1]:
            lists.append(run)
            run = []
        run.append(item)
    lists.append(run)
    return [run for run in lists if len(run) >= 2]


def branch_views(text):
    """`(label, view)` for each branch of each path list, or `[("", text)]` when there is none.

    A branch's view is the section without the other items of its own list.
    """
    lines = text.split("\n")
    views = []
    for run in path_lists(text):
        for label, first, end in run:
            drop = {i for other, f, e in run if (f, e) != (first, end) for i in range(f, e)}
            views.append((label, "\n".join(ln for i, ln in enumerate(lines) if i not in drop)))
    return views or [("", text)]


def checked_sites(files, assets):
    """`(file, line, heading, branch, asset, view)` for each site, one per branch that names it.

    A section with no path list is one site with branch "". A section with one is a site per
    branch whose view still names the asset by its plugin path.
    """
    out = []
    for rel, line, heading, asset, body in derived_sites(files, assets):
        for label, view in branch_views(body):
            if match_lines(view, asset_path(asset)):
                out.append((rel, line, heading, label, asset, view))
    return out


def undisposed(files, assets):
    """`file:line [heading] asset` for each derived, unexempt site that disposes of nothing.

    A branch site reads `file:line [heading → branch] asset`.
    """
    found = []
    for rel, line, heading, label, asset, view in checked_sites(files, assets):
        if (rel, heading) in EXEMPT:
            continue
        if disposition(rel, asset, view, files) is None:
            where = "%s → %s" % (heading, label) if label else heading
            found.append("%s:%d [%s] %s" % (rel, line, where, asset))
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
                    (M7_P1, BRAND): "values"}
        got = {(rel, asset): disposition(rel, asset, body, self.files)
               for rel, _, _, asset, body in derived_sites(self.files, self.assets)
               if (rel, asset) in expected}
        self.assertEqual(expected, got)

    def test_the_scan_finds_each_branch_of_truth_set_step_2(self):
        """#601: the non-Python branch is a site of its own, not credited by the Python copy."""
        found = {(rel, heading, label, asset)
                 for rel, _, heading, label, asset, _ in checked_sites(self.files, self.assets)}
        self.assertEqual(set(), KNOWN_BRANCH_SITES - found)

    def test_each_truth_set_branch_has_its_own_project_copy(self):
        expected = {(M3B_P1, M3B_STEP2, "Python", D3): "`data/temp/truthset-viz/vendor/d3.v7.min.js`",
                    (M3B_P1, M3B_STEP2, OTHER, D3): "`src/server/vendor/d3.v7.min.js`",
                    (M3B_P1, M3B_21, OTHER, D3): "`src/server/vendor/d3.v7.min.js`"}
        for rel, _, heading, label, asset, view in checked_sites(self.files, self.assets):
            key = (rel, heading, label, asset)
            if key not in expected:
                continue
            with self.subTest(branch=label, heading=heading):
                self.assertEqual("project copy", disposition(rel, asset, view, self.files))
                self.assertIn(expected[key], view)
        python_view = next(view for rel, _, heading, label, _, view
                           in checked_sites(self.files, self.assets)
                           if (rel, heading, label) == (M3B_P1, M3B_STEP2, "Python"))
        self.assertNotIn("`src/server/vendor/d3.v7.min.js`", python_view,
                         "the Python view still holds the other branch's copy, so a branch "
                         "is not being read apart from its siblings")


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

    def test_module_7_reading_d3_by_its_plugin_path_again_is_reported(self):
        files = self.mutated(M7_P1, "`src/server/vendor/d3.v7.min.js`", "the project", -1)
        files[M7_P1] = files[M7_P1].replace(
            "Make the host-side copy into `src/server/vendor/` that",
            "Read `${CLAUDE_PLUGIN_ROOT}/scripts/vendor/d3.v7.min.js` at runtime, as", 1)
        self.assertIn("%s %s" % (M7_P1, D3), self.reported(files))

    def test_the_non_python_branch_without_its_copy_is_reported(self):
        """#601's negative control: 2.1's Python copy no longer credits the other branch."""
        text = self.files[M3B_P1]
        start = text.index('  <a id="%s"></a>' % D3_COPY_ANCHOR)
        end = text.index("### 2.2 ")
        files = dict(self.files)
        files[M3B_P1] = text[:start].rstrip(" \n") + "\n\n" + text[end:]
        got = undisposed(files, self.assets)
        where = "[%s → %s] %s" % (M3B_STEP2, OTHER, D3)
        self.assertTrue(any(f.startswith(M3B_P1 + ":") and f.endswith(where) for f in got),
                        "the non-Python branch of Truth Set Step 2 lost its D3 copy and was "
                        "not reported: %r" % got)
        self.assertFalse(any("→ Python]" in f for f in got),
                         "the Python branch keeps its copy and must not be reported: %r" % got)

    def test_a_copy_in_one_branch_credits_that_branch_alone(self):
        files = dict(self.files)
        files["module-99-new/SKILL.md"] = (
            "# New module\n\n## 3. Build the server\n\n"
            "Inline `${CLAUDE_PLUGIN_ROOT}/scripts/vendor/d3.v7.min.js` into the page.\n\n"
            "- **Python** → copy it to `data/temp/new/vendor/d3.v7.min.js` first.\n"
            "- **Any other language** → generate the server.\n")
        got = undisposed(files, self.assets)
        self.assertIn("module-99-new/SKILL.md:5 [3. Build the server → Any other language] %s"
                      % D3, got)
        self.assertFalse(any(f.startswith("module-99-new/SKILL.md") and "→ Python]" in f
                             for f in got))

    def test_a_copy_outside_the_branches_credits_every_branch(self):
        files = dict(self.files)
        files["module-99-new/SKILL.md"] = (
            "# New module\n\n## 3. Build the server\n\n"
            "Inline `${CLAUDE_PLUGIN_ROOT}/scripts/vendor/d3.v7.min.js` from\n"
            "`src/server/vendor/d3.v7.min.js`.\n\n"
            "- **Python** → run the reference.\n"
            "- **Any other language** → generate the server.\n")
        self.assertNotIn("module-99-new/SKILL.md %s" % D3, self.reported(files))

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

    def test_d3_points_to_module_3b_and_does_not_restate_the_copy(self):
        """#601: step 3c links to the one statement and keeps no copy of it (INV-300)."""
        self.assertTrue(match_lines(
            self.section,
            r"\]\(\.\./module-03b-truthset-visualization/phase1-visualization\.md#%s\)"
            % D3_COPY_ANCHOR), "step 3c must link to Module 3b's statement of the D3 copy")
        self.assertEqual([], match_lines(self.section, asset_path(D3)),
                         "step 3c names the D3 asset by its plugin path again, so it restates "
                         "the copy Module 3b states once")
        self.assertEqual([], match_lines(self.section, COPY_STATEMENT))

    def test_the_module_7_lines_stay(self):
        for label, pattern in (
                ("the position-dependent lookup", r"position-dependent and does not travel"),
                ("the snapshot note", r"The standalone snapshot is unaffected"),
                ("first build", r"at this server's first build")):
            with self.subTest(element=label):
                self.assertTrue(match_lines(self.section, pattern), "Module 7 lost: " + label)

    def test_the_refusal_stays_and_names_the_recovery(self):
        self.assertTrue(match_lines(
            self.section, r"`src/server/vendor/d3\.v7\.min\.js` is later missing, the server "
                          r"names `d3\.v7\.min\.js` and writes no page"))


#: The statement of the host-side D3 copy into `src/server/vendor/`, wherever it is written.
COPY_STATEMENT = re.compile(
    r"(?i)\bcop(?:y|ies)\b[^.`]{0,40}`\$\{CLAUDE_PLUGIN_ROOT\}/scripts/vendor/d3\.v7\.min\.js`"
    r".{0,200}?\bto\s+`src/server/vendor/d3\.v7\.min\.js`")


class TheD3CopyIsStatedOnce(unittest.TestCase):
    """#601: Module 3b 2.1's "Any other language" bullet holds the one statement (INV-300)."""

    @classmethod
    def setUpClass(cls):
        cls.files = shipped_skills()
        cls.text = cls.files[M3B_P1]
        cls.statement = anchored_text(cls.text, D3_COPY_ANCHOR)

    def test_the_anchor_is_in_the_non_python_branch_of_2_1(self):
        body = section_named(self.text, "2.1 ")
        tag = '<a id="%s"></a>' % D3_COPY_ANCHOR
        lines = body.split("\n")
        at = next(i for i, line in enumerate(lines) if tag in line)
        owners = [label for run in path_lists(body) for label, first, end in run
                  if first <= at < end]
        self.assertEqual([OTHER], owners)

    def test_the_statement_says_what_to_copy_where_and_on_which_routes(self):
        self.assertIsNotNone(self.statement)
        for label, pattern in (
                ("the copy itself", COPY_STATEMENT),
                ("on the host", r"on the host"),
                ("on every route", r"on every route"),
                ("the skill-relative fallback",
                 r"skill-relative fallback `\.\./\.\./scripts/vendor/d3\.v7\.min\.js`, INV-252"),
                ("resolved beside the server", r"resolve it from beside its own file there"),
                ("Module 7 in every language",
                 r"results server in every language, Python included"),
                ("the docker route", r"`docker` route"),
                ("the recovery", r"copy it again from the plugin on the host"),
                ("the citation", r"INV-300")):
            with self.subTest(element=label):
                self.assertTrue(match_lines(self.statement, pattern),
                                "Module 3b's D3 copy lost: " + label)

    def test_the_copy_is_stated_in_one_place(self):
        where = {rel: len(match_lines(text, COPY_STATEMENT)) for rel, text in self.files.items()}
        where = {rel: n for rel, n in where.items() if n}
        self.assertEqual({M3B_P1: 1}, where,
                         "the host-side D3 copy into `src/server/vendor/` is stated in more than "
                         "one place; point at Module 3b 2.1 instead (INV-300)")

    def test_a_restated_copy_is_caught(self):
        restated = ("At first build, copy it on the host from\n"
                    "`${CLAUDE_PLUGIN_ROOT}/scripts/vendor/d3.v7.min.js` (skill-relative fallback\n"
                    "`../../scripts/vendor/d3.v7.min.js`, INV-252) to `src/server/vendor/d3.v7.min.js`.")
        self.assertEqual([1], match_lines(restated, COPY_STATEMENT))


if __name__ == "__main__":
    unittest.main()
