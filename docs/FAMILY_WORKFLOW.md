# The Senzing Bootcamp family — development workflow

**Status:** normative. **Adopted:** 2026-09-22. **Amendments:** see [§10](#10-amendments).
**Home:** `docs/FAMILY_WORKFLOW.md` in
`docktermj/senzing-bootcamp-claude-plugin-development` (the parent). Every child development
repository links to this page rather than restating it — a rule with two homes is a rule that
will disagree with itself.

The goal this document serves: **a Senzing Bootcamp behaves the same way for a bootcamper on
Claude, Kiro, ChatGPT, Copilot and Gemini.** Every rule below exists because it keeps those
five experiences from drifting apart.

Rules are numbered `R1`…`R12` so an issue can cite one.

---

## 1. Repositories and roles

| Role | Repository | Owns |
|---|---|---|
| **Parent — development** | `docktermj/senzing-bootcamp-claude-plugin-development` | The curriculum, the bootcamper experience, and the `INV-NNN` invariant namespace |
| Parent — public | `Senzing/senzing-bootcamp-claude-plugin` | Nothing. A mirror bootcampers install from |
| **Child — development** | `docktermj/senzing-bootcamp-kiro-power-development` | The Claude → Kiro transformation and `KINV-NNN` |
| | `docktermj/senzing-bootcamp-chatgpt-plugin-development` | The Claude → Codex transformation and `CINV-NNN` |
| | `docktermj/senzing-bootcamp-copilot-plugin-development` | The Claude → Copilot transformation and `CPINV-NNN` |
| | `docktermj/senzing-bootcamp-gemini-plugin-development` | The Claude → Gemini transformation and `GINV-NNN` |
| Child — public | `Senzing/senzing-bootcamp-{kiro-power,chatgpt-plugin,copilot-plugin,gemini-plugin}` | Nothing. Mirrors |

**R1 — The parent owns the curriculum; children transform, never fork.** A child never copies
or renumbers an `INV-NNN`. Bootcamp content and outcomes are decided in exactly one place.

**R2 — Propagation is a pull, and it starts at a tag.** The parent never pushes into a child
and never files an issue into one. A child takes a **tagged release**, never `main` or `HEAD`.
A version that was never tagged is invisible to the whole mechanism: *a port cannot target a
release that was never tagged.*

**R3 — Public repositories have minimal knowledge of their development repositories.** Every
maintainer command lives in a development repository. A public repository holds only what a
bootcamper installs. This is deliberate and is not an oversight to be corrected.

---

## 2. Canonical operations

**R4 — The canonical operation names are reserved family-wide, and every development
repository exposes each applicable operation under its canonical name.** The *name* is the
invariant; the *invocation mechanism* is the host's business. A Claude slash command, a Kiro
power skill triggered by natural language, and a Codex `commands/` entry are all conforming
implementations of `parity-check` — an operation named `publish-bootcamp-power` is not.

**An operation with no parent counterpart keeps a host-specific name and must not shadow a
canonical one.** Kiro's `create-bootcamp-power` and `update-bootcamp-power` are transformation
mechanisms, not maintainer-facing phases; they keep their names.

| Canonical operation | Phase | Parent | Children | Boundary |
|---|---|---|---|---|
| `feedback-to-issues` | 1 | required | required | In a child, routes each item parent-bound or local (R6) |
| `retrofit-from-public` | 1 | required | required | Files issues. **Writes nothing into any working tree** |
| `parity-check` | 1 | — | required | Reads a parent **tag**. Never writes to the parent |
| `implement-github-issue` | 2 | required | required | Never merges. In a child, advances `PARENT_VERSION` on a parity close |
| `escalate-to-parent` | 2 | — | required | **The only command in a child that writes outside its own repository** |
| `production-readiness-audit` | 3 | required | required | Consistency, coherency, completeness |
| `dry-run` | 3 | required | required | Runtime review |
| `auto-test` | 3 | required | *not mandated* | Probes the live Senzing MCP server for drift |
| `release` | 4 | required | required | **Development repository only** (R8) |
| `propagate-to-public` | 4 | required | required | **Public working tree only** (R8) |
| `unattended-issue-loop` | drives 2–3 | required | *not mandated* | `unattended-ok`-labeled issues only |
| `delegate-to-mcp-server` | maintenance | required | — | Parent only |
| `compact-dev-environment` | maintenance | required | — | Parent only |
| `review-invariants` | maintenance | required | *open question* | See §8 |
| `check-skill-drift` | maintenance | required | — | Parent only. Compares a duplicated rule block against its out-of-repo twin |

⚠️ **Renaming is not free.** Where a child's engine, contract, tests or docs reference an
operation by its old name, the rename is the whole change — a new file beside the old one
leaves two operations where the family expects one.

---

## 3. The per-change flow

```mermaid
flowchart TB
    P1["<b>Phase 1 · Generate issues</b><br/>feedback-to-issues<br/>retrofit-from-public<br/>parity-check <i>(children only)</i><br/>escalated from children <i>(parent only)</i><br/>manual"]
    P2["<b>Phase 2 · Development</b><br/>implement-github-issue<br/>escalate-to-parent <i>(children only)</i>"]
    P3["<b>Phase 3 · Test</b><br/>production-readiness-audit<br/>dry-run<br/>auto-test <i>(parent)</i><br/>recorded host-behavior checklist <i>(children)</i>"]
    P4["<b>Phase 4 · Publish</b><br/>release<br/>then propagate-to-public"]

    P1 ==> P2 ==> P3 ==> P4
    P3 -->|"test failures needing code changes<br/>loop back here, <b>never into maintenance</b>"| P2

    LOOP["<b>unattended-issue-loop</b><br/>drives phases 2 and 3 in turn,<br/>on <i>unattended-ok</i> issues only"]
    LOOP -.-> P2
    LOOP -.-> P3

    classDef phase fill:#eaf2fb,stroke:#3a6ea5,color:#1b3a57
    classDef driver fill:#f3f0fa,stroke:#6a5a9a,color:#2e2350
    class P1,P2,P3,P4 phase
    class LOOP driver
```

The four phases run in order and **only one edge goes backwards**: a test failure needing a
code change returns to development, never to maintenance. Maintenance is where you go when
nothing is failing.

Phases 2, 3 and 4 are identical in the parent and in the children. **Phase 1 is where they
differ**, because it is where work originates: a child additionally runs `parity-check` to pick
up what the parent released; the parent additionally receives what children escalate.

### Maintenance — a separate track, on its own cadence, parent only

```mermaid
flowchart LR
    subgraph M["Maintenance · parent only"]
        direction LR
        M1["delegate-to-mcp-server"] ~~~ M2["compact-dev-environment"] ~~~ M3["review-invariants"] ~~~ M4["check-skill-drift"]
    end
    classDef cmd fill:#eaf2fb,stroke:#3a6ea5,color:#1b3a57
    class M1,M2,M3,M4 cmd
```

Nothing in the four phases waits on these and they wait on nothing. An "optional" per-change
step gets skipped every time, and a step skipped every time never runs at all; giving these
their own cadence is what stops them becoming ceremony.

---

## 4. Repository topology

```mermaid
flowchart LR
    subgraph PARENT["Parent — Claude"]
        direction TB
        PD["claude-plugin-<br/>development"]
        PP["claude-plugin<br/><i>(public)</i>"]
        PTAG(["tagged release"])
        PD -->|"release"| PTAG
        PD -->|"propagate-to-public"| PP
        PP -.->|"retrofit-from-public<br/>files issues — copies nothing"| PD
    end

    subgraph CHILDREN["Children — one per host, identical in shape"]
        direction TB
        K["kiro-power-development<br/>→ kiro-power"]
        G["chatgpt-plugin-development<br/>→ chatgpt-plugin"]
        CP["copilot-plugin-development<br/>→ copilot-plugin"]
        GM["gemini-plugin-development<br/>→ gemini-plugin"]
    end

    PTAG ==>|"PULL · parity-check<br/>the parent never pushes"| K
    PTAG ==> G
    PTAG ==> CP
    PTAG ==> GM

    K -.->|"escalate-to-parent<br/>files issues only"| PD
    G -.-> PD
    CP -.-> PD
    GM -.-> PD

    classDef repo fill:#eaf2fb,stroke:#3a6ea5,color:#1b3a57
    classDef tag fill:#fdf3e0,stroke:#b8860b,color:#5c4208
    class PD,PP,K,G,CP,GM repo
    class PTAG tag
```

- **Solid arrows move files. Dotted arrows move only issues.**
- **The topology is one level deep.** Nothing ports from a child. A change that reached two
  children reached each from the parent, never from each other.
- Each child's public repository is its own leaf with the same `release` →
  `propagate-to-public` → `retrofit-from-public` triangle drawn inside the parent box.

---

## 5. Issue ownership

**R5 — The "spec" mechanism is deprecated family-wide. Work is tracked as GitHub issues.**
No development repository generates spec files for new work.

**R6 — The repository that owns the defect owns the issue.**

```mermaid
flowchart TB
    START{{"A problem is observed<br/>in a child port"}}
    Q1{"Curriculum, content,<br/>a Senzing fact, or<br/>parent-owned behavior?"}
    PARENTISSUE["File in the <b>parent</b><br/>via escalate-to-parent<br/>— the only cross-repo write path"]
    CHILDISSUE["File in the <b>child</b><br/>— host packaging, hooks,<br/>lifecycle, interaction, release"]
    FIX["Parent fixes it canonically<br/>→ release → the child's next<br/>parity-check brings it down"]

    START --> Q1
    Q1 -->|yes · applies to every bootcamp| PARENTISSUE
    Q1 -->|no · this host only| CHILDISSUE
    PARENTISSUE --> FIX

    classDef q fill:#fdf3e0,stroke:#b8860b,color:#5c4208
    classDef act fill:#eaf2fb,stroke:#3a6ea5,color:#1b3a57
    class START,Q1 q
    class PARENTISSUE,CHILDISSUE,FIX act
```

`feedback-to-issues` and `retrofit-from-public` run this decision **per item** in a child and
must show the verdict for each. In the parent there is nothing to decide — every issue is
local.

**R7 — Escalation closes on arrival, not on the parent's close.** An escalated issue carries a
cross-reference in both directions. The child's local tracking issue closes when a
`parity-check` against a parent tag **containing** the fix confirms it arrived. A parent issue
closed but not yet released has not reached any bootcamper.

**R8 — `implement-github-issue` never begins work on an issue the maintainer has not
approved.** Invoked with no argument it reviews the open set, reports what it found, **names the
issue it suggests**, and **stops**. It may analyze, it may rank, it may name one; it may not
start. The command pushes branches and opens pull requests, and *acting without approval* is the
autonomy it is designed not to have.

⛔ **The report ends by naming one issue**, so the maintainer's next act is approval rather than
selection — the command has just read the whole backlog and is the thing best placed to propose
a target. ⚠️ **Where the open set is empty, or where no issue is a defensible suggestion, the
report says so** rather than naming one to satisfy the form.

⛔ **It MUST first review the open set for dependencies and report them** — a suggested order
where one follows, and which issues are independent — so the choice is made informed rather
than blind. ⛔ **Every ordering claim carries the evidence that establishes it**: the sentence,
file or acceptance criterion a reader can check. An ordering offered without citable evidence is
a **preference**, which is permitted and MUST be labeled as one rather than presented as a
dependency.

⛔ **A reference asserting NON-dependence is never read as a dependency.** An `owner-checked:`
line naming other issues to support an absence claim — *"none of which touch …"* — says they are
**unrelated**; reading it as an edge inverts the clearest signal in the corpus. **Shared-file
coupling is reported separately, as merge risk**, and never folded into the order. Where issues
are independent the report says so and **implies no order**.

⛔ **This rule has been narrowed three times in two days, and ONE clause now carries it** —
see [§10](#10-amendments). As adopted it forbade recommending **and** picking; 2026-09-22
removed the ban on recommending; 2026-09-23 removed *asks which issue*. What remains is
**approval before action**, and it is stated first above rather than last because it is no
longer one restraint among several — it is the whole of the guarantee. ⚠️ **A child port
reading only the current text will not see that**, which is why the trajectory is recorded and
not just the endpoint.

---

## 6. Release and publication boundaries

**R9 — `release` touches only the development repository.** It bumps the version everywhere it
is asserted, writes the CHANGELOG entry, commits, and creates the git tag — as one operation,
with no path that moves one without the others. It does not touch the public repository.

**R10 — `propagate-to-public` touches only the public repository's working tree.** It mirrors
what a bootcamper needs, rewrites development self-references to the public slug, and **stops
there: no commit, no push, no branch, no pull request, no release.** The maintainer reviews the
diff and publishes by hand, and a versioned release in a public repository is created only
after that version has been tested.

⚠️ **This is the boundary most easily eroded**, because "just open the PR too" looks like
convenience. It is not: the diff a maintainer reviews before anything leaves the machine is the
last gate before a bootcamper sees the change.

---

## 7. Invariants

**R11 — Each development repository maintains `specs/INVARIANTS.md`, and every child
additionally maintains an inherited-invariant disposition register.**

| | Parent | Child |
|---|---|---|
| Own namespace | `INV-NNN` in `specs/INVARIANTS.md` | `KINV` / `CINV` / `CPINV` / `GINV`-`NNN` in `specs/INVARIANTS.md` — guarantees true of the *host port itself*, with no upstream source |
| Inherited register | — | **Required.** Every upstream `INV-NNN` recorded as *honored* / *preserved-restated* / *discounted*, a discount carrying a mandatory conflict and resolution |
| Evaluated when | Every change | **Both registers, on every propagation of a newer parent release** (dual-evaluation) |

A host-native invariant MUST NOT restate an upstream `INV-NNN` or a disposition-register entry.
Where it names an upstream invariant it does so only to locate the parity gap it is about.

A host-native prefix is registered in this table so two children cannot collide. A failed
invariant on either side is a **release blocker**, not advisory documentation.

**R12 — Succession has exactly one syntax, in every invariant file in the family.** A full
supersession is recorded in **both** directions; each marker is a bullet of its own, and the
identifier is zero-padded to three digits:

```markdown
- **Superseded by:** INV-312 — the guard moved from the hook to the contract
- **Supersedes:** INV-208
```

Where only a **clause** of a rule is replaced, the marker is:

```markdown
- **Partly superseded by:** INV-198 — what was replaced, and what still stands
```

Nothing else establishes supersession — not prose, not a status word, not a strikethrough. An
invariant carrying `Superseded by:` has status `superseded`; one that does not has status
`active`; and **there is no third status.**

⛔ **Three markers, two statuses — and conflating those two counts is what left the third
marker unwritten here for two days.** `Partly superseded by:` does **not** establish
supersession: the entry stays `active` and **still binds in full**, which is precisely why it
needs a marker of its own rather than the `Superseded by:` one. Reporting it superseded would
tell a child the whole rule is obsolete. A child MUST record the replaced clause and its
successor, and MUST NOT let a partial supersession change an entry's status. This exists because the parent's prose had written
supersession six different ways, leaving a substantial minority of its invariants reporting
`status: unclear` in the generated manifest. Adopting the single syntax (#112) took that to
zero. ⚠️ **No count is stated here deliberately**: a figure in normative prose goes stale
silently while reading authoritative, and four repositories cite this rule. Read the live
number off `invariant-manifest.json`.

### Provenance: one name

**The pinned parent release is `PARENT_VERSION` (an exact SemVer tag) and `PARENT_COMMIT` (the
full SHA), in every child.** Not `UPSTREAM_VERSION`. "Upstream" is already taken in this family
— the Senzing MCP server is upstream of every repository here, and a feedback item routed
"upstream" goes to Senzing, not to the parent. The parent/child vocabulary is the one the
topology uses, so the provenance names follow it.

Where a child stores those values is the host's business — a manifest extension block and a
pair of files are both conforming — but the *names* are fixed, and a child reads them from one
place.

---

## 8. `specs/` is frozen, with five live exceptions

The parent froze `specs/` on 2026-09-15 (INV-307). ⛔ **The archive is read-only; no new spec
files are written by any command.** Five files in it are **not** frozen and are still written
to:

- `specs/INVARIANTS.md` — the invariant register
- `specs/IMPLEMENTED.md` — the implementation ledger, including `DEFERRED INVARIANT` blocks
- `specs/DECLINED.md` — decisions *not* to build, with a required reason and revisit condition
- `specs/README.md` — the freeze notice itself
- `specs/mcp-coverage.jsonl` — `/delegate-to-mcp-server`'s coverage ledger

⚠️ **This list said "four" and named four until 2026-09-24 (#142)**, while the fifth had been
written to throughout. It was justified where it is used on the grounds that it is `.jsonl`
rather than `*.md` and so *"sits outside the freeze by construction"* — which is a permission
resting on a **guard's blind spot**, not on a decision: the freeze guard globs `specs/*.md`,
and widening it would silently revoke an exception nobody recorded. ⛔ **(INV-307) An exception to the freeze is a DECISION and MUST be
named in this list**, never left resting on what a guard happens not to reach. The same
repository rejects exactly this reasoning for `invariant-manifest.json`, which sits at the root
rather than relying on the glob missing it.

⚠️ **"`specs/` is no longer used except for `INVARIANTS.md`" is the wrong reading** and would
delete the implementation ledger and the record of declined decisions. The archive is retained
deliberately: it is where the reasoning behind shipped behavior lives.

**Open question, deliberately not decided here:** children now maintain two invariant registers
and therefore have the same deferred-invariant problem the parent solved with
`review-invariants`. Whether that operation is ported down is unresolved; until it is, a child's
dual-evaluation gate at update time is the only thing standing in for it.

---

## 9. Bootstrapping a new child

A new child reuses **unchanged**: the transformation engine, the disposition-register shape,
reconciliation, and the governance operations. It supplies **only** three host-specific things:
its own invariant prefix and register, its substitution sets and host mechanisms in the
contract, and its host-behavior checks. The parent, and the `INV-NNN` it owns, do not change.

The nine components every child provides:

| | Component | Release gate |
|---|---|---|
| A | Tagged provenance (`PARENT_VERSION`, `PARENT_COMMIT`) | A stable parent tag and full commit only; never `HEAD` |
| B | Declarative transformation contract | Every upstream file matched exactly once, or fail |
| C | Inherited-invariant disposition register | Every `INV-NNN` honored, preserved-restated, or justified as discounted |
| D | Host-native invariant namespace | Both registers evaluated on every update |
| E | Mechanical port checks | Provenance, files, residual host references, static hook behavior |
| F | Three-way reconciliation | A pre-write report naming added, modified, removed, preserved and conflicting paths |
| G | Recorded host-behavior test checklist | Every critical manual result recorded per release |
| H | CI determinism gate | A rebuild at the pinned tag leaves no diff |
| I | Cross-repo governance | `parity-check` pulls down; `escalate-to-parent` is the sole upward write path |

Where a host lacks a mechanism the parent relies on, **preserve the guarantee with a
host-native construction where possible; otherwise document the advisory degradation** in the
disposition register and the release evidence. Never drop it silently.


---

## 10. Amendments

⛔ **A numbered rule that changes meaning is recorded here, with the wording it replaced.**
Four repositories cite these rules by number, and their conformance issues are written against
whatever the page said on the day they were opened. A reader holding an earlier copy has no
other way to discover that a rule moved: the parent never files into a child (R2), so this
section **is** the notification channel, and it travels by parity like everything else.

⚠️ **Not every edit is an amendment.** A typo, a link, a clearer example: not recorded. The
unit here is a change to what a numbered rule *requires*, because that is the unit another
repository cites.

⚠️ **An amendment does not renumber.** R8 stays R8. A rule that is withdrawn keeps its number
and says so, for the same reason `INVARIANTS.md` never reuses an id: a citation that silently
resolves to a different rule is worse than one that fails.

### 2026-09-24 — R12 names its third marker: `Partly superseded by:`

**Was:** two markers — `Superseded by:` and `Supersedes:` — introduced as *"Both lines are
required"*, followed by *"Nothing else establishes supersession"* and *"there is no third
state."*

**Now:** three markers and two statuses, stated as separate counts. `Partly superseded by:
INV-nnn` records that only a **clause** was replaced; the entry stays `active` and still binds
in full. *"There is no third **status**"* is unchanged in substance and now says `status`
rather than `state`.

The parent had been using the third marker **six** times — INV-040, INV-079, INV-086, INV-101,
INV-104, INV-137 — while this page named two. A child implementing R12 as written had no form
for the case, and the parent's own published manifest had no field for it either: all six
shipped `superseded_by: null` with the successor buried in free text. Both are fixed together
(#143).

⛔ **What a child must do:** record the replaced clause and its successor, and **do not** let a
partial supersession change an entry's status. The parent publishes this as a separate
`partly_superseded_by` field rather than overloading `superseded_by`, so a consumer already
reading that field is unaffected.

**For a child:** a conformance issue citing R12's two-marker text is not wrong about the rule.
The requirement — one syntax, a bullet per marker, zero-padded ids, both directions for a full
supersession — is unchanged. A third marker was added for a case the rule always had.

### 2026-09-24 — R4's reserved register gains `check-skill-drift`

**Was:** the §2 table reserved fourteen operation names.

**Now:** fifteen. `check-skill-drift` is added as **maintenance · parent required · children —**.

It shipped in the parent on 2026-09-23 (#128) and was absent from this page for a day. **No
rule text changed**, and the row itself records that no child is required to have it. This is
recorded here anyway because R4 reserves names *family-wide*: a child holding an earlier copy
reads `check-skill-drift` as unclaimed and could give the name to something else, and §10 is
the only channel that would tell it otherwise.

⚠️ **Its mechanism is Claude-specific and that does not make it host-specific.** It compares a
rule block against a twin outside the repository — under `~/.claude/skills/` in this host. R4
already settles the case: *the name is the invariant; the invocation mechanism is the host's
business.* A child that duplicates a rule block anywhere has the same problem and may claim the
name; one that does not, needs nothing.

**For a child:** no conformance action. The name is now taken.

### 2026-09-23 — R8 narrowed again: it names the issue it suggests

**Was:** *"Invoked with no argument it **asks which issue** and stops until answered; it does not
pick, and it never begins work on an issue it selected."*

**Now:** it reviews the open set, reports what it found, **names the issue it suggests**, and
stops. *Stops until approved* survives; **"asks which issue" is removed.**

The reasoning: the command has just read the whole backlog and analyzed it for dependencies, so
it is the thing best placed to propose a target — ending with *"tell me which issue"* hands the
selection back at the moment its analysis is most useful.

⛔ **Three narrowings in two days, and what is left is one clause.** The trajectory belongs here
because a child port reading only R8's current text cannot see it:

| Date | Removed | Remaining restraints |
|---|---|---|
| adopted 2026-09-22 | — | does not recommend · does not pick · stops until answered |
| 2026-09-22 (#119) | *does not recommend* | does not pick · stops until answered |
| 2026-09-23 (#124) | *asks which issue* | **approval before action** |

⚠️ **Each step was defensible on its own and the direction has been consistent.** R8's remaining
guarantee is no longer one restraint among several — it carries the rule by itself, which is why
it is now stated first in R8 rather than last. **A child implementing this must treat approval
before action as the rule, not as a qualifier on it.**

⚠️ **What did NOT change:** the dependency report, the evidence requirement for every ordering
claim, the prohibition on reading a non-dependence reference as an edge, and the separation of
merge risk from order. This amendment touches the closing act only.

### 2026-09-22 — R8 narrowed: the recommendation ban removed, a dependency report required

**Was:** *"Invoked with no argument, it asks which issue and stops until answered. **It does not
recommend and it does not pick.** The command pushes branches and opens pull requests; selecting
its own work is the one autonomy it is designed not to have."*

**Now:** the command **must** review the open set for dependencies and report them, with a
suggested order and the evidence for each claim, before the user chooses. *Does not pick* and
*stops until answered* survive unchanged; **"does not recommend" is removed.**

⚠️ **What was given up, stated rather than buried.** R8's rationale is that *acting on its own
selection* is the autonomy this command must not have, and a ranked list is the mechanism by
which a user rubber-stamps. That risk is real and was accepted on the maintainer's decision: the
countervailing cost — a maintainer choosing blind among issues that genuinely depend on one
another — was judged the larger one. **The surviving guarantee is narrower and should be read
as narrower**: the command may advise; it still may not act on its own advice.

⛔ **The reading rules in R8 are not decoration, and a child implementing this must not skip
them.** They were derived by running the analysis over the parent's seven open issues on
2026-09-22, where **both** mechanical methods failed:

- **Counting cross-references inverted the strongest signal.** Two issues named two others
  inside their `owner-checked:` lines — *"none of which touch `conformance.py`'s corpus"* — which
  is an absence claim asserting the issues are **unrelated**. Read as edges, those lines produce
  the exact opposite of what they say.
- **Shared-file coupling made five of seven look ordered**, because all five name
  `specs/INVARIANTS.md`. It is a hub; it establishes merge risk, not sequence.
- **The one real relation was visible to neither method** and only by reading content: an issue
  quoting a figure that a later change had already altered.

**For a child:** an implementation that derives order from reference counts or shared paths is
**not** conforming, however plausible its output looks.

### 2026-09-22 — R8 widened, and the parent brought into line

**Recorded as a restatement; it was not one.** #111's notes described R8 as restating the
existing guardrail in the parent's `implement-github-issue` command. That command said:

> If `$ARGUMENTS` is **empty**, ask which issue and stop until answered. Do not choose one.

R8 adds **"It does not recommend and it does not pick."** *Do not choose* and *do not
recommend* are different rules — ranking the open issues, or marking one *(Recommended)*, is
choosing with extra steps, and the guardrail as written permitted it.

**Resolution:** R8 stands as written and the **parent command was brought up to it**, so the
rule has one home (INV-300). R8's text is unchanged from adoption; what changed is that it is
now an accurate statement of what the parent does.

⚠️ **A child implementing `implement-github-issue` from the adopted text was already correct.**
The divergence was in the parent, and in the note claiming the two agreed.

### 2026-09-22 — R12's count removed

**Was:** *"…the parent's generated manifest currently reports `status: unclear` for 33 of 309
invariants, the prose having written supersession six different ways."*

**Now:** the same evidence with **no denominator**.

`33` was correct; `309` was already stale on the day of adoption — the manifest held **311**,
INV-311 and INV-312 having been registered that morning. ⛔ **The figure was removed rather than
corrected**, because correcting it only resets the clock: the parent's own suite fails a count
of commands stated in prose in `docs/development.md`, on the ground that *a number goes stale
silently while reading authoritative*. A normative page four repositories cite is the worst
place for one.

**For a child:** a conformance issue citing R12's count is not wrong about the rule. R12's
requirement — one syntax for succession, both lines, zero-padded — is unchanged. Only the
supporting figure was dropped.
