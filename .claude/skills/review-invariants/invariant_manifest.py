#!/usr/bin/env python3
"""Generate the machine-readable invariant manifest from `specs/INVARIANTS.md`.

Downstream ports (Kiro, Codex, and the rest) each owe an **invariant-disposition register**:
every `INV-NNN` resolving to exactly one disposition in the port. Building that mechanically
needs an authoritative list of the ids and their statements. ⛔ **Without one, each child writes
its own parser of a 398 KB prose file designed for human authority** — and each parses it
differently, which defeats the uniformity the register exists for (#88).

⚠️ **(INV-311) The prose stays the source of truth.** This file is derived, regenerated, and checked in CI
to match; it is never edited by hand and never authoritative.

⛔ **Two fields #88 asked for cannot be derived from the prose as it stands, and are reported
rather than invented.**

* **`summary`** — there is no one-line statement to extract. Measured 2026-09-21 across 309
  entries: the median first sentence is **249 characters** and **113 of 309 exceed 300**, the
  longest being 3,013. So a summary is emitted only when the first sentence is at or under
  `SUMMARY_MAX`; otherwise it is `null`, and the null count is printed. ⚠️ **A null summary means
  "not derivable", never "no rule"** — `statement` always carries the full text.
* **`status`** — **two values, and there is no third (#112).** An entry carrying a
  `- **Superseded by:** INV-nnn` bullet is `superseded`; every other entry is `active`. ⛔ **(INV-311)** Prose
  is **not** read as evidence: supersession was written six different ways (`superseded`,
  `Superseded`, `supersedes`, `Corrected`, `Amended`, `withdrawn`), and the same word marks an
  entry that supersedes another as well as one that was superseded. Reading it produced
  `unclear` for **33** entries, most of which were not supersessions at all.
  ⚠️ **`unclear` left the vocabulary with that change** — it is not a value this generator can
  emit, and a consumer need not handle it. (This paragraph described the retired three-state
  model until #143, nine days after the model was retired, and the published `note` said the
  same thing to four child repositories.)
* **`partly_superseded_by`** — the successor where only a **clause** was replaced, from a
  `- **Partly superseded by:** INV-nnn` bullet. ⛔ **(INV-311)** Such an entry stays `active` and **still
  binds in full**; a partial supersession is not a third state. Null means no partial
  supersession, never that the entry is obsolete.

Stdlib only. Read-only with respect to `specs/`; writes one file at the repository root.

    invariant_manifest.py            # write the manifest, print the counts
    invariant_manifest.py --check    # exit 1 if the checked-in file is stale

Source issue: #88.
"""
import argparse
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
INVARIANTS = REPO / "specs" / "INVARIANTS.md"

#: ⛔ At the repository root, NOT in `specs/`. The freeze guard globs `specs/*.md`, so a `.json`
#: there would be legal only because the glob does not reach it -- a scope-narrowing that happens
#: to produce correct behavior, which INV-308 says must not be relied on. The root also matches
#: what the file is: a release artifact for downstream consumers, not part of the archive.
MANIFEST = REPO / "invariant-manifest.json"

#: One entry: `- **INV-NNN** — <body>`, up to the next entry or heading.
ENTRY = re.compile(r"(?m)^- \*\*(INV-\d{3})\*\*\s*—\s*(.+?)(?=\n- \*\*INV-\d{3}\*\*|\n## |\Z)", re.S)

#: A subject-index group: a bolded name, then the ids beneath it.
GROUP = re.compile(r"(?m)^- \*\*(.+?)\*\*\s*—.*?\n((?:.*\n)*?)(?=^- \*\*|\Z)")

#: Longest first sentence still worth calling a summary. Set from the measurement above rather
#: than from taste: at 200 the median entry (249) is excluded, so this is deliberately generous.
SUMMARY_MAX = 300

#: ⛔ **(#112) Status comes from THESE BULLETS ALONE — prose is never evidence.** The old
#: reading matched the word anywhere and produced `unclear` for **33** entries, of which most
#: were not supersessions at all: the word used about a *file* in a tree diagram (INV-050), a
#: *figure* (INV-278, INV-295), or an explicit negative — *"supersedes nothing"* (INV-300),
#: *"INV-089 is **not** superseded"* (INV-263). #122 was the same defect at one entry.
SUPERSEDED_BULLET = re.compile(r"^\s*- \*\*Superseded by:\*\* (INV-\d{3})", re.M)

#: ⚠️ **A third relation the two-state model has no room for, and the data does.** Six entries
#: say only a *clause* of themselves is superseded — INV-040's parenthetical, INV-079's recap
#: heading, INV-086's framing, INV-101's Docker-only scope, INV-104's tab enumeration, and
#: INV-137's trigger. **They still bind.** Calling them `superseded` would tell four child
#: ports the whole rule is obsolete, which is false and is the dangerous direction; so they
#: remain `active` and say why in a bullet of their own.
#:
#: ⚠️ **The count here said "Five" and listed five until #143, omitting INV-104** — the entry
#: whose partial supersession (INV-155, the tab enumeration) is the one a production-readiness
#: audit had already cited as the canonical example of a stale enumeration. A prose count
#: beside a list is two things to keep in step, and this is what it looks like when they part.
#: ⚠️ **Do not re-derive this list by reading**: `grep -c 'Partly superseded by:'` is the count,
#: and `test_supersession_has_one_syntax.py` now holds the set against the register.
PARTLY_SUPERSEDED_BULLET = re.compile(r"^\s*- \*\*Partly superseded by:\*\* (INV-\d{3})", re.M)

#: The back-link. A successor names what it replaced, because a successor that does not read
#: as a new rule -- which is how six variants of this came to exist.
SUPERSEDES_BULLET = re.compile(r"^\s*- \*\*Supersedes:\*\* (INV-\d{3})", re.M)

#: Kept ONLY to find prose that still talks about supersession, so a guard can require each
#: such entry to be dispositioned. ⛔ It no longer decides status.
SUPERSESSION_WORDS = re.compile(r"supersede|Supersede|withdrawn|Corrected \d{4}|Amended \d{4}")


def flat(s):
    return re.sub(r"\s+", " ", s).strip()


def groups_by_id(text):
    """{INV-nnn: subject-group name} read from the index, so the manifest agrees with it."""
    out = {}
    idx = text.find("Index by subject")
    if idx == -1:
        return out
    for name, body in GROUP.findall(text[idx:]):
        for inv in re.findall(r"INV-\d{3}", body):
            out.setdefault(inv, flat(name))
    return out


def sections_by_id(text):
    """{INV-nnn: enclosing heading} -- the document's own structure.

    ⚠️ Separate from `index_group` on purpose. 33 of 309 entries -- the foundational and
    whole-Bootcamp invariants -- are organized under narrative headings and appear in no
    *Index by subject* group at all. Reporting a heading as though it were an index group would
    make one key mean two things in a schema other repositories pin to; reporting null and
    stopping would lose a grouping the file genuinely has. So both are emitted and each means
    exactly one thing.
    """
    out, current = {}, None
    for line in text.splitlines():
        if line.startswith("#"):
            # ⛔ Only `#`/`##` set the section. `### Index by subject` is a SUB-heading of
            # `## Invariants added from implemented specs`, and taking the nearest heading of any
            # level put 259 of 309 entries under the index rather than under the section that
            # actually contains them -- a wrong value in a field other repositories pin to,
            # caught by reading the emitted JSON rather than by any assertion.
            if len(line) - len(line.lstrip("#")) <= 2:
                current = flat(line.lstrip("#"))
            continue
        m = re.match(r"- \*\*(INV-\d{3})\*\*\s*—", line)
        if m:
            out[m.group(1)] = current
    return out


def status_of(body):
    """`superseded` or `active` -- two states, decided by a bullet rather than by prose.

    ⛔ **(INV-313) (#112) There is no third state.** An entry carrying `- **Superseded by:** INV-nnn` is
    superseded; every other entry is active. Prose mentioning supersession decides nothing,
    which is what removed 33 `unclear` entries that were mostly not supersessions at all.

    ⚠️ A `Partly superseded by:` bullet leaves the entry **active** deliberately: only a clause
    of it was replaced and the rest still binds. Reporting it as superseded would tell a child
    port the whole rule is obsolete.
    """
    m = SUPERSEDED_BULLET.search(body)
    if m:
        return "superseded", m.group(1)
    # ⛔ Everything else is `active`. `unclear` has left the vocabulary (#112): it existed
    # because prose was being read as evidence, and prose is no longer read at all.
    return "active", None


def build():
    text = INVARIANTS.read_text(encoding="utf-8")
    groups = groups_by_id(text)
    sections = sections_by_id(text)
    entries = []
    for inv, body in ENTRY.findall(text):
        statement = flat(body)
        first = re.match(r"(.+?[.!?])(?:\s|$)", statement)
        summary = first.group(1) if first and len(first.group(1)) <= SUMMARY_MAX else None
        status, by = status_of(body)
        partly = PARTLY_SUPERSEDED_BULLET.search(body)
        entries.append({
            "id": inv,
            "index_group": groups.get(inv),
            "section": sections.get(inv),
            "status": status,
            "superseded_by": by,
            # ⛔ **(INV-311) (#143) Separate from `superseded_by`, never folded into it.** A partly
            # superseded entry is `active` and still binds; putting its successor in
            # `superseded_by` would change what that field means for every consumer already
            # reading it. The regex existed from #112 and was referenced only by a test, so
            # the relation was visible in the prose and in no structured field -- six entries
            # published `superseded_by: null` with the pointer buried in `statement`.
            "partly_superseded_by": partly.group(1) if partly else None,
            "summary": summary,
            "statement": statement,
        })
    entries.sort(key=lambda e: e["id"])
    return {
        "source": "specs/INVARIANTS.md",
        "generator": ".claude/skills/review-invariants/invariant_manifest.py",
        "note": ("Derived, never authoritative. `summary` is null where no one-line statement "
                 "could be extracted -- that means NOT DERIVABLE, never absence of a rule; "
                 "`statement` always carries the full text. `status` has exactly two values: "
                 "`superseded` for an entry carrying a `Superseded by:` bullet, `active` for "
                 "every other entry. There is no `unclear` status -- prose is not read as "
                 "evidence. `partly_superseded_by` names the successor where only a CLAUSE was "
                 "replaced; such an entry stays `active` and still binds in full, so a null "
                 "there means no partial supersession, never that the entry is obsolete."),
        "count": len(entries),
        "invariants": entries,
    }


def render(manifest):
    return json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def report(manifest, stream=sys.stdout):
    """⛔ (INV-308) Print what could NOT be derived beside what could."""
    inv = manifest["invariants"]
    null_summary = sum(1 for e in inv if e["summary"] is None)
    by_status = {}
    for e in inv:
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1
    no_group = sum(1 for e in inv if not e["index_group"])
    no_section = sum(1 for e in inv if not e["section"])
    stream.write("%d invariant(s)\n" % len(inv))
    stream.write("  status: %s\n" % ", ".join("%s %d" % kv for kv in sorted(by_status.items())))
    stream.write("  summary NOT derivable for %d of %d -- null means undetermined, not absent\n"
                 % (null_summary, len(inv)))
    stream.write("  %d entr(ies) in no subject-index group (they are grouped by heading "
                 "instead, which `section` carries)\n" % no_group)
    stream.write("  %d entr(ies) under no heading at all\n" % no_section)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the checked-in manifest differs from a fresh generation")
    args = ap.parse_args(argv)
    manifest = build()
    rendered = render(manifest)
    if args.check:
        current = MANIFEST.read_text(encoding="utf-8") if MANIFEST.is_file() else ""
        if current != rendered:
            sys.stderr.write(
                "invariant-manifest.json is stale: it does not match specs/INVARIANTS.md.\n"
                "Regenerate it with:\n"
                "  python3 .claude/skills/review-invariants/invariant_manifest.py\n")
            return 1
        report(manifest)
        return 0
    MANIFEST.write_text(rendered, encoding="utf-8")
    report(manifest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
