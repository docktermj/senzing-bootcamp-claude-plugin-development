#!/usr/bin/env python3
"""Probe the live Senzing MCP server for drift and check the plugin against it.

Zero tokens, no Claude process, stdlib only. Talks JSON-RPC straight to
https://mcp.senzing.com/mcp, so it runs in seconds and can be scheduled as often
as you like.

Why this exists
---------------
``tests/test_mcp_call_contracts.py`` encodes the server's contract *statically*, as
observed on its ``CONTRACT_VERIFIED_ON`` date, deliberately: the suite stays offline
and fast (INV-108). Its own docstring names the cost of that trade —

    "a tool that gains a required parameter will not be caught here until someone
     does [a dry run]"

This script is the online half that closes exactly that gap.

The load-bearing discovery: **most closed value sets live in the description
prose, not in JSON-Schema enums.** When this probe was written (2026-07-27) all 13
tools had zero ``enum`` keys. On server 1.39.0 (2026-10-15) four parameters declare
one — ``sdk_guide.topic``, ``mapping_workflow.action``, ``reporting_guide.topic`` and
``get_sdk_reference.topic`` — but the languages ``generate_scaffold`` and
``sdk_guide`` support, the ``search_docs`` categories and the sample datasets still
live only in the tool's *description prose*. So a checker that reads only
``inputSchema.enum`` misses most of the contract. ``PROSE_VALUES`` below parses
those lists out of the prose, ``PROBE_MATRIX`` discovers the accepted sets, and a
declared enum is unioned into the accepted set (``accepted_values``): it can clear a
suspicion, never add one.

What it checks
--------------
1. **Drift** — live schemas *and* the prose-declared value lists, against a
   committed baseline. A value disappearing from the prose is BREAKING; the schema
   would not have moved.
2. **Conformance** — every ``tool(param='value')`` the plugin writes, against the
   value list for that tool and parameter.
3. **Cross-tool consistency** — two tools that both take ``language`` must agree,
   or the plugin can route a bootcamper into a tool that cannot serve them.
4. **Static-contract audit** — the constants inside
   ``tests/test_mcp_call_contracts.py``, so the offline test cannot quietly certify
   a contract that has since changed.

Subcommands
-----------
    snapshot   fetch and print a normalized snapshot (no comparison)
    check      compare live against the baseline + all conformance checks [default]
    update     overwrite the baseline with the current live snapshot

Exit codes: 0 clean, 1 findings at BREAKING severity, 2 probe failed.
"""
import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
BASELINE = SKILL_DIR / "baseline" / "mcp-snapshot.json"
CONTRACT_TEST = REPO_ROOT / "tests" / "test_mcp_call_contracts.py"

DEFAULT_URL = "https://mcp.senzing.com/mcp"
CONTRACT_STALE_DAYS = 90

# ⛔ Never call these. `submit_feedback` files noise upstream and transmits a real
# name and work email; `download_resource` can pull something large. The dry-run
# skill makes this a rule for a human; here it is enforced in code, because an
# unattended run cannot be trusted to remember a rule.
NEVER_CALL = frozenset({"submit_feedback", "download_resource"})

# Read-only calls whose *content* is worth snapshotting, not just their schema.
CONTENT_PROBES = (("get_capabilities", {}),)

# Where each closed value set is stated in prose. Declared enums cover only four
# parameters on 1.39.0, none of them listed here. Each regex must capture ONE group
# holding the raw list. Verified against the 2026-07-27 descriptions; the two
# `language` patterns were re-fitted to the 1.39.0 descriptions (2026-10-15, #659)
# and still match the older wording. A description change flips these to "no longer
# extractable", which is itself reported rather than silently skipped.
#
# These are the *documented* sets. PROBE_MATRIX below discovers the *accepted* sets,
# and the two disagreeing is a finding in its own right — see `doc_mismatch`.
PROSE_VALUES = {
    ("mapping_workflow", "action"): r"Actions:\s*([a-z_,\s]+?)\.",
    # "Languages: python, java, csharp (official V4 SDKs); rust, typescript
    # (community-maintained wrappers, not official)." — the glosses are skipped by
    # _split_values; the list ends at the first full stop outside parentheses.
    ("generate_scaffold", "language"):
        r"Languages:\s*((?:[a-z#,;\s]|\([^)]*\))+?)\.",
    ("search_docs", "category"): r"'category' to filter:\s*([a-z_,\s]+?)(?:\.|\n|$)",
    # "Languages: 5 (Python, Java, C#, Rust, TypeScript)." on 1.39.0;
    # "5 languages (Python, …)" before it.
    ("sdk_guide", "language"):
        r"(?:\d+\s+languages\s*|Languages:\s*\d+\s*)\(([^)]+)\)",
    ("sdk_guide", "platform"): r"\d+\s+platforms\s*\(((?:[^()]|\([^)]*\))*)\)",
    ("get_sample_data", "dataset"): r"Available datasets:\s*((?:[^.()]|\([^)]*\))+)",
}

# Send one deliberately invalid value and read the rejection. This server answers a
# bad value by naming every good one — `sdk_guide(topic='zzz')` returns "Valid
# topics: install, configure, load, ...". That makes the accepted set *observable*
# rather than inferred, which matters because the descriptions are demonstrably
# incomplete: `generate_scaffold` documents four languages and accepts five.
#
# Every entry here must be side-effect free. `mapping_workflow` qualifies because an
# unknown action fails deserialization before the handler runs, and its workflow
# state travels in the request rather than living on the server. Anything that
# writes, downloads, or transmits stays out — see NEVER_CALL.
PROBE_SENTINEL = "zzz_probe_invalid"
PROBE_MATRIX = (
    ("mapping_workflow", "action", {}),
    ("sdk_guide", "topic", {}),
    ("sdk_guide", "platform", {"topic": "install"}),
    ("sdk_guide", "language", {"topic": "install"}),
    ("get_sdk_reference", "topic", {}),
    ("reporting_guide", "topic", {}),
    ("generate_scaffold", "workflow", {"language": "python"}),
    ("generate_scaffold", "language", {"workflow": "initialize"}),
    ("get_sample_data", "dataset", {}),
    ("search_docs", "category", {"query": "entity resolution"}),
)

# How a probe came back.
ENUMERATED = "enumerated"      # rejected, and named the valid values
OPAQUE = "opaque"              # rejected, but did not say what is valid
SILENT = "silently-accepted"   # took the garbage value without complaint

# Where a rejection message lists the alternatives.
_ENUM_CUES = (
    re.compile(r"expected one of\s+(.+)", re.I),
    re.compile(r"(?:Valid|Available|Supported|Known)\s+\w+[^:]*:\s*([^.\n}\"]+)", re.I),
)

# Parameters that are free text, not closed sets. Listing them explicitly keeps the
# conformance check from flagging `version='current'` or `filter='why_entities'`,
# which are legitimate and unbounded. Anything absent from PROSE_VALUES is skipped
# anyway; this set exists to document the judgment rather than leave it implicit.
FREE_TEXT_PARAMS = frozenset({"version", "filter", "query", "source", "email",
                              "firstname", "lastname", "message", "how_heard",
                              "file_path", "filename", "repo", "scale"})

# Tools that must agree on a shared parameter's value set, because the plugin
# carries one bootcamper choice into both.
CROSS_TOOL_AGREEMENT = (("language", ("sdk_guide", "generate_scaffold")),)

# Spellings of the same value. The server prints "C#" in prose, answers "csharp" in
# its rejection list, and accepts both; "typescript/node" is one entry naming two
# accepted spellings. Without this table every such pair reads as a documentation
# defect, which is noise rather than signal.
ALIASES = {
    "c#": "csharp", "cs": "csharp", "dotnet": "csharp",
    "node": "typescript", "nodejs": "typescript", "js": "typescript",
    "py": "python",
}


def _canon(value):
    return ALIASES.get(value.lower(), value.lower())


def _canon_set(values):
    return {_canon(v) for v in values}


# Mistakes the server's own `common_confabulations` list says an LLM will make,
# as (wrong, right) pairs. Kept explicit rather than parsed out of the prose: the
# list is written for a human reader and a regex over it would be guesswork. When
# the `content` diff reports that get_capabilities changed, re-read it and update
# this tuple.
CONFABULATIONS = (
    ("add_data_source", "register_data_source"),
    ("addDataSource", "registerDataSource"),
    ("close_export", "close_export_report"),
    ("G2Engine", "SzEngine"),
    # 1.39.0 (2026-10-15): "Wrong attribute names (EMPLOYER_NAME vs NAME_ORG)".
    # NAME_ORG is the correct attribute; the pair was inverted until #659.
    ("EMPLOYER_NAME", "NAME_ORG"),
)
# A line that warns *against* a confabulation contains one of these; it is the
# opposite of a defect and must not be flagged.
NEGATION_CUES = re.compile(
    r"(?i)\b(never|not|non-|no\s|instead|wrong|incorrect|avoid|CLI command|"
    r"rather than|do NOT|confabulat|deprecated|V3)\b")

BREAKING, WATCH, INFO = "BREAKING", "WATCH", "INFO"
_VALUE_TOKEN = re.compile(r"^[a-z0-9_#.-]+$")


# --------------------------------------------------------------------------- rpc


def _post(url, payload, timeout):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def _parse(raw):
    """Decode a reply that may be plain JSON or SSE frames.

    The server answers with plain JSON today but advertises ``text/event-stream``,
    and streamable-HTTP servers may switch at any time. Handling both means a
    transport change does not read as a probe failure — which would look identical
    to the server being down.
    """
    text = raw.strip()
    if not text:
        raise ValueError("empty response")
    if not text.startswith("{"):
        for line in text.splitlines():
            if line.startswith("data:"):
                candidate = line[5:].strip()
                if candidate and candidate != "[DONE]":
                    return json.loads(candidate)
        raise ValueError(f"no JSON payload in response: {text[:200]!r}")
    return json.loads(text)


def rpc(url, method, params=None, timeout=30, mid=1):
    payload = {"jsonrpc": "2.0", "id": mid, "method": method}
    if params is not None:
        payload["params"] = params
    reply = _parse(_post(url, payload, timeout))
    if "error" in reply:
        raise RuntimeError(f"{method}: {reply['error']}")
    return reply.get("result", {})


# ---------------------------------------------------------------------- snapshot


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:16]


def _normalize_schema(schema):
    """Order-stabilize a schema so a reordering is not reported as a change."""
    if isinstance(schema, dict):
        out = {}
        for key in sorted(schema):
            val = schema[key]
            if key in ("required", "enum") and isinstance(val, list):
                out[key] = sorted(val, key=str)
            else:
                out[key] = _normalize_schema(val)
        return out
    if isinstance(schema, list):
        return [_normalize_schema(v) for v in schema]
    return schema


def _split_values(raw):
    """Pull discrete values out of a prose list.

    Handles the three shapes the descriptions actually use: quoted items
    (``'las-vegas', 'london'``), comma lists (``start, advance, back``) and
    semicolon lists whose items carry an em-dash gloss (``linux_apt — Ubuntu/Debian
    via apt; linux_yum — RHEL``). Quoted items win when present, because a quoted
    list may legitimately contain commas inside its glosses.
    """
    quoted = re.findall(r"'([^']+)'", raw)
    parts = quoted if quoted else re.split(r"[;,]", raw)
    out = []
    for part in parts:
        part = re.split(r"\s+—|\s+-\s|\(", part)[0]
        part = part.strip().strip("'\").").lower()
        part = re.sub(r"^(?:and|or)\s+", "", part)
        if part and _VALUE_TOKEN.match(part):
            out.append(part)
    seen = set()
    return [v for v in out if not (v in seen or seen.add(v))]


def extract_prose_values(tool_name, description):
    """The closed value sets this tool declares in prose, as {param: [values]}."""
    found = {}
    for (tool, param), pattern in PROSE_VALUES.items():
        if tool != tool_name:
            continue
        match = re.search(pattern, description, re.I)
        found[param] = _split_values(match.group(1)) if match else []
    return found


def _harvest_tokens(raw):
    """Every value token in a rejection's list of alternatives.

    Deliberately permissive. The lists arrive in three shapes at once — backticked
    (``` `start`, `advance` ```), parenthetically glossed (``csharp (official V4);
    rust``) and slash-aliased (``typescript/node``) — and ``get_sdk_reference``
    nests a whole alias list inside parentheses (``parameters (… aliases: functions,
    methods, …)``). Every one of those tokens is genuinely accepted, so harvesting
    all of them is correct rather than sloppy: the goal is to catch an *invented*
    value like ``schema_mappings``, not to police which spelling of a real value the
    plugin picked.
    """
    ticked = re.findall(r"`([^`]+)`", raw)
    source = " ".join(ticked) if ticked else raw
    tokens = re.findall(r"[a-z][a-z0-9_#-]{1,40}", source.lower())
    # Words that appear in the glosses rather than as values.
    noise = {"official", "aliases", "alias", "per", "language", "binding", "and",
             "or", "the", "argument", "types", "method", "see", "use", "with",
             "v3", "v4"}
    seen, out = set(), []
    for token in tokens:
        if token in noise or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def probe_values(url, timeout=30):
    """Discover each parameter's accepted value set by sending one bad value.

    Returns ``{tool: {param: {"mode": ..., "values": [...]}}}``. A probe that fails
    for an unrelated reason (network, unexpected shape) records the error and is
    skipped by the checks rather than reported as a plugin defect.
    """
    found = {}
    for index, (tool, param, base) in enumerate(PROBE_MATRIX):
        if tool in NEVER_CALL:
            continue
        args = dict(base)
        args[param] = PROBE_SENTINEL
        entry = {"mode": OPAQUE, "values": []}
        try:
            result = rpc(url, "tools/call", {"name": tool, "arguments": args},
                         timeout=timeout, mid=100 + index)
            text = "".join(c.get("text", "") for c in result.get("content", [])
                           if isinstance(c, dict))
            if not result.get("isError"):
                # The server took a value that cannot be meaningful. Whatever it
                # returned is not scoped the way the caller asked for.
                entry["mode"] = SILENT
                found.setdefault(tool, {})[param] = entry
                continue
        except RuntimeError as exc:
            text = str(exc)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            found.setdefault(tool, {})[param] = {"mode": "probe-error",
                                                 "values": [], "error": str(exc)}
            continue

        for cue in _ENUM_CUES:
            match = cue.search(text)
            if match:
                values = [v for v in _harvest_tokens(match.group(1))
                          if v != PROBE_SENTINEL]
                if values:
                    entry = {"mode": ENUMERATED, "values": values}
                break
        found.setdefault(tool, {})[param] = entry
    return found


def snapshot(url, timeout=30, probe_content=True, probe_values_too=True):
    init = rpc(url, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "sbcp-auto-test", "version": "1"},
    }, timeout=timeout)
    tools = rpc(url, "tools/list", timeout=timeout, mid=2).get("tools", [])

    snap = {
        "url": url,
        "server": init.get("serverInfo", {}),
        "protocol": init.get("protocolVersion"),
        "instructions_sha": _digest(init.get("instructions", "")),
        "instructions": init.get("instructions", ""),
        "tools": {},
        "content": {},
    }
    for tool in sorted(tools, key=lambda t: t.get("name", "")):
        name = tool.get("name", "")
        schema = _normalize_schema(tool.get("inputSchema", {}) or {})
        props = schema.get("properties", {}) or {}
        description = tool.get("description", "")
        snap["tools"][name] = {
            "required": sorted(schema.get("required", []) or []),
            "properties": sorted(props),
            # Declared JSON-Schema enums. Empty for all 13 tools on 2026-07-27;
            # four parameters declare one on 1.39.0. accepted_values unions them
            # into the accepted set, with null dropped.
            "enums": {p: v["enum"] for p, v in props.items()
                      if isinstance(v, dict) and isinstance(v.get("enum"), list)},
            "prose_values": extract_prose_values(name, description),
            "description_sha": _digest(description),
            "description": description,
            "schema_sha": _digest(schema),
        }

    if probe_content:
        for name, args in CONTENT_PROBES:
            if name in NEVER_CALL:
                continue
            try:
                res = rpc(url, "tools/call", {"name": name, "arguments": args},
                          timeout=timeout, mid=3)
                text = "".join(c.get("text", "") for c in res.get("content", [])
                               if isinstance(c, dict))
                snap["content"][name] = {"sha": _digest(text), "text": text}
            except Exception as exc:  # a content probe must never fail the run
                snap["content"][name] = {"error": str(exc)}

    if probe_values_too:
        for tool, params in probe_values(url, timeout).items():
            if tool in snap["tools"]:
                snap["tools"][tool]["probed_values"] = params
    return snap


def accepted_values(tool_meta, param):
    """The authoritative accepted set for a parameter, or None if unknown.

    Probed values win over prose: the server's own rejection message is evidence,
    while the description is a claim about itself that has been observed to be
    incomplete.
    """
    # Values confirmed accepted by an actual call outrank everything, and are
    # unioned in rather than replacing: `get_sample_data` enumerates four datasets
    # and also honors `dataset='list'`, so neither source alone is the whole set.
    extra = set((tool_meta.get("verified_values") or {}).get(param) or [])
    # A declared JSON-Schema enum joins the same way (#659). It only widens the
    # set, so it can clear a suspicion but never add a rejection. `null` is how a
    # nullable schema spells "may be omitted", not a value the plugin can send.
    extra |= declared_enum_values(tool_meta, param)
    probed = (tool_meta.get("probed_values") or {}).get(param)
    if probed and probed.get("mode") == ENUMERATED and probed.get("values"):
        return set(probed["values"]) | extra
    prose = (tool_meta.get("prose_values") or {}).get(param)
    if prose:
        return set(prose) | extra
    return extra or None


def declared_enum_values(tool_meta, param):
    """The parameter's declared JSON-Schema enum, lower-cased, with `null` dropped."""
    declared = (tool_meta.get("enums") or {}).get(param) or []
    return {v.lower() for v in declared if isinstance(v, str)}


def record_verified_extras(live, url, timeout=30):
    """Confirm every plugin literal the enumeration does not cover, and record it.

    Run at baseline time so the offline suite can reuse the verdict. Without this,
    an offline conformance check has no way to distinguish an invented value from an
    undocumented-but-honored one like `dataset='list'`, and reports the plugin's
    correct text as BREAKING.
    """
    tools = live.get("tools", {})
    for _path, text in _skill_files():
        for line in text.splitlines():
            for tool, args in _CALL.findall(line):
                if tool not in tools:
                    continue
                for param, value in _KWARG.findall(args):
                    if param in FREE_TEXT_PARAMS or value.startswith("<"):
                        continue
                    allowed = accepted_values(tools[tool], param)
                    if not allowed or value.lower() in allowed:
                        continue
                    if verify_literal(url, tool, param, value, timeout) is True:
                        slot = tools[tool].setdefault("verified_values", {})
                        bucket = slot.setdefault(param, [])
                        if value.lower() not in bucket:
                            bucket.append(value.lower())
                            bucket.sort()
    return live


# ------------------------------------------------------------------------- drift


def _finding(sev, code, message):
    return {"severity": sev, "code": code, "message": message}


def diff_baseline(live, base):
    out = []
    if not base:
        return [_finding(INFO, "baseline-missing",
                         "no baseline yet — run `mcp_probe.py update` to create one")]

    if live.get("server") != base.get("server"):
        out.append(_finding(INFO, "server-version",
                            f"server info: {base.get('server')} -> {live.get('server')}"))
    if live.get("protocol") != base.get("protocol"):
        out.append(_finding(WATCH, "protocol",
                            f"protocol {base.get('protocol')} -> {live.get('protocol')}"))
    if live.get("instructions_sha") != base.get("instructions_sha"):
        out.append(_finding(WATCH, "instructions",
                            "server `instructions` text changed — re-read it"))

    lt, bt = live.get("tools", {}), base.get("tools", {})
    for name in sorted(set(bt) - set(lt)):
        out.append(_finding(BREAKING, "tool-removed",
                            f"tool `{name}` no longer exists on the server"))
    for name in sorted(set(lt) - set(bt)):
        out.append(_finding(WATCH, "tool-added",
                            f"new tool `{name}` — the plugin may want to use it"))

    for name in sorted(set(lt) & set(bt)):
        live_t, base_t = lt[name], bt[name]

        new_req = set(live_t["required"]) - set(base_t["required"])
        if new_req:
            out.append(_finding(BREAKING, "required-added",
                                f"`{name}` now REQUIRES {sorted(new_req)} — every "
                                "call omitting it fails"))
        gone_req = set(base_t["required"]) - set(live_t["required"])
        if gone_req:
            out.append(_finding(INFO, "required-dropped",
                                f"`{name}` no longer requires {sorted(gone_req)}"))

        gone_props = set(base_t["properties"]) - set(live_t["properties"])
        if gone_props:
            out.append(_finding(BREAKING, "param-removed",
                                f"`{name}` dropped parameter(s) {sorted(gone_props)}"))
        new_props = set(live_t["properties"]) - set(base_t["properties"])
        if new_props:
            out.append(_finding(INFO, "param-added",
                                f"`{name}` gained parameter(s) {sorted(new_props)}"))

        # The prose value lists are the real contract on this server.
        base_pv = base_t.get("prose_values", {})
        live_pv = live_t.get("prose_values", {})
        for param, base_vals in sorted(base_pv.items()):
            live_vals = live_pv.get(param, [])
            if base_vals and not live_vals:
                out.append(_finding(
                    BREAKING, "prose-unextractable",
                    f"`{name}.{param}` value list can no longer be parsed from the "
                    "description — the wording changed; update PROSE_VALUES or the "
                    "conformance check silently stops covering this parameter"))
                continue
            # Documentation drift only. Whether the value still *works* is settled
            # by the probed diff below, so this stays WATCH to avoid reporting one
            # change twice at two severities.
            removed = set(base_vals) - set(live_vals)
            if removed:
                out.append(_finding(
                    WATCH, "doc-value-removed",
                    f"`{name}.{param}` description no longer lists {sorted(removed)}"))
            added = set(live_vals) - set(base_vals)
            if added:
                out.append(_finding(
                    INFO, "doc-value-added",
                    f"`{name}.{param}` description now lists {sorted(added)}"))

        # Probed sets are the accepted contract; a value disappearing here is a
        # real capability loss, whatever the description still says.
        base_probed = base_t.get("probed_values", {})
        live_probed = live_t.get("probed_values", {})
        for param, base_info in sorted(base_probed.items()):
            live_info = live_probed.get(param, {})
            if base_info.get("mode") != ENUMERATED:
                continue
            if live_info.get("mode") != ENUMERATED:
                out.append(_finding(
                    WATCH, "probe-mode-changed",
                    f"`{name}.{param}` stopped enumerating its valid values on "
                    f"rejection ({base_info.get('mode')} -> {live_info.get('mode')})"))
                continue
            base_vals = set(base_info.get("values", []))
            live_vals = set(live_info.get("values", []))
            if base_vals - live_vals:
                out.append(_finding(
                    BREAKING, "value-removed",
                    f"`{name}.{param}` no longer accepts "
                    f"{sorted(base_vals - live_vals)} — plugin text using it fails"))
            if live_vals - base_vals:
                out.append(_finding(
                    INFO, "value-added",
                    f"`{name}.{param}` now also accepts {sorted(live_vals - base_vals)}"))

        if not base_t.get("enums") and live_t.get("enums"):
            out.append(_finding(INFO, "enums-appeared",
                                f"`{name}` now declares real JSON-Schema enums — "
                                "accepted_values unions them into the accepted set"))

        if live_t["description_sha"] != base_t["description_sha"]:
            out.append(_finding(WATCH, "description",
                                f"`{name}` description changed — the nested contract "
                                "lives in this prose, so re-read it"))

    for name, live_c in sorted(live.get("content", {}).items()):
        base_c = base.get("content", {}).get(name)
        if base_c and "sha" in base_c and "sha" in live_c:
            if live_c["sha"] != base_c["sha"]:
                out.append(_finding(WATCH, "content",
                                    f"`{name}` response changed — re-read "
                                    "common_confabulations and update CONFABULATIONS"))
    return out


# -------------------------------------------------------------------- conformance


def _skill_files():
    for root in (PLUGIN / "skills", PLUGIN / "commands"):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.md")):
            if "pytest_cache" in path.parts:
                continue
            yield path, path.read_text(encoding="utf-8", errors="replace")


# The plugin writes MCP calls as `tool_name(param='value', ...)` on one line, which
# is what makes a tool-scoped check possible: the value is never orphaned from the
# tool it belongs to.
_CALL = re.compile(r"\b([a-z_]{3,32})\(([^)\n]{0,300})")
_KWARG = re.compile(r"\b([a-z_]+)='([A-Za-z0-9_.#-]+)'")


def verify_literal(url, tool, param, value, timeout=30, _cache={}):
    """Ask the server directly whether this exact value is accepted.

    The rejection message is not a complete catalog. ``get_sample_data`` answers a
    bad dataset with "Available datasets: las-vegas, london, moscow, truthset" and
    yet also honors ``dataset='list'``, an undocumented discovery sentinel that
    appears in no list anywhere. Inferring from the enumeration alone therefore
    produces a confident, wrong BREAKING finding against correct plugin text.

    So a value missing from the enumerated set is only a *suspicion*; this turns it
    into evidence. Returns True (accepted), False (rejected) or None (could not
    tell — treated as "do not report").
    """
    key = (tool, param, value)
    if key in _cache:
        return _cache[key]
    base = next((dict(b) for t, p, b in PROBE_MATRIX if t == tool and p == param), None)
    if base is None or tool in NEVER_CALL:
        _cache[key] = None
        return None
    base[param] = value
    try:
        result = rpc(url, "tools/call", {"name": tool, "arguments": base},
                     timeout=timeout, mid=200)
        verdict = not result.get("isError")
    except RuntimeError:
        verdict = False          # the server refused it outright
    except (urllib.error.URLError, OSError, ValueError):
        verdict = None           # transport problem: not evidence either way
    _cache[key] = verdict
    return verdict


def conformance(live, url=None):
    out = []
    tools = live.get("tools", {})
    if not tools:
        return out
    files = list(_skill_files())
    rel = lambda p: p.relative_to(REPO_ROOT)  # noqa: E731

    # 1. Every tool-scoped literal must be in that tool's declared value set.
    for path, text in files:
        for lineno, line in enumerate(text.splitlines(), 1):
            for tool, args in _CALL.findall(line):
                if tool not in tools:
                    continue
                for param, value in _KWARG.findall(args):
                    if param in FREE_TEXT_PARAMS:
                        continue
                    allowed = accepted_values(tools[tool], param)
                    if not allowed:
                        continue
                    # A placeholder such as `<chosen_language>` is not a literal.
                    if value.startswith("<"):
                        continue
                    if value.lower() in allowed:
                        continue
                    probed = (tools[tool].get("probed_values") or {}).get(param, {})
                    if probed.get("mode") != ENUMERATED:
                        continue
                    # Missing from the enumeration is a suspicion, not a verdict.
                    # Settle it against the server before accusing the plugin.
                    if url is not None:
                        verdict = verify_literal(url, tool, param, value)
                        if verdict is not False:
                            if verdict is True:
                                out.append(_finding(
                                    INFO, "undocumented-value",
                                    f"{rel(path)}:{lineno} calls {tool}({param}="
                                    f"'{value}') — accepted by the server but absent "
                                    "from every list it publishes, so it is "
                                    "undocumented rather than wrong"))
                            continue
                    out.append(_finding(
                        BREAKING, "invalid-value",
                        f"{rel(path)}:{lineno} calls {tool}({param}='{value}'), "
                        f"which the server rejects — it accepts {sorted(allowed)}"))

    # 2. Any mcp__senzing__X reference must resolve to a real tool.
    for path, text in files:
        for lineno, line in enumerate(text.splitlines(), 1):
            for name in re.findall(r"mcp__senzing__([a-z_]+)", line):
                if name not in tools:
                    out.append(_finding(
                        BREAKING, "unknown-tool",
                        f"{rel(path)}:{lineno} references mcp__senzing__{name}, "
                        "which the server does not offer"))

    # 3. A required parameter must be named in a file that calls the tool.
    for tool, meta in sorted(tools.items()):
        required = meta.get("required", [])
        if not required:
            continue
        callers = [(p, t) for p, t in files if re.search(rf"`?{re.escape(tool)}\(", t)]
        if not callers:
            continue
        for param in required:
            if not any(param in t for _, t in callers):
                where = ", ".join(str(rel(p)) for p, _ in callers)
                out.append(_finding(
                    BREAKING, "missing-required",
                    f"`{tool}` requires `{param}`, named in none of its calling "
                    f"files ({where}) — the call fails without it"))

    # 4. Confabulations the server warns about, used affirmatively.
    for path, text in files:
        for lineno, line in enumerate(text.splitlines(), 1):
            if NEGATION_CUES.search(line):
                continue
            for wrong, right in CONFABULATIONS:
                if re.search(rf"\b{re.escape(wrong)}\b", line):
                    out.append(_finding(
                        WATCH, "confabulation",
                        f"{rel(path)}:{lineno} uses `{wrong}` with no warning cue on "
                        f"the line — the server's common_confabulations says the "
                        f"correct form is `{right}`"))

    # 5. Sensitive call sites, for a human to confirm are consent-gated.
    for path, text in files:
        for lineno, line in enumerate(text.splitlines(), 1):
            for banned in sorted(NEVER_CALL):
                if re.search(rf"`?{banned}\(", line):
                    out.append(_finding(
                        INFO, "sensitive-call-site",
                        f"{rel(path)}:{lineno} references `{banned}(` — confirm it "
                        "is gated on consent"))
    return out


def server_quality(live, url=None):
    """Findings about the MCP server itself, not about the plugin.

    This is the half of the run that answers "does the server carry inaccurate or
    misleading information", and it is only answerable by comparing what the server
    *documents* against what it *accepts*. Both were observed on 2026-07-27:
    `generate_scaffold` documents four languages and accepts five, and `search_docs`
    takes any `category` string without complaint.
    """
    out = []
    for tool, meta in sorted(live.get("tools", {}).items()):
        probed = meta.get("probed_values") or {}
        prose = meta.get("prose_values") or {}
        for param, info in sorted(probed.items()):
            mode = info.get("mode")

            if mode == SILENT:
                out.append(_finding(
                    WATCH, "silent-accept",
                    f"`{tool}.{param}` accepted the nonsense value "
                    f"'{PROBE_SENTINEL}' without an error — a typo in this parameter "
                    "returns plausible but wrongly-scoped results instead of "
                    "failing, so the plugin cannot detect its own mistake"))
                continue

            if mode == OPAQUE:
                out.append(_finding(
                    INFO, "opaque-rejection",
                    f"`{tool}.{param}` rejects a bad value without naming the valid "
                    "ones — the accepted set cannot be observed, so this parameter "
                    "is checked against the description only"))
                continue

            if mode != ENUMERATED:
                continue

            documented_raw = prose.get(param) or []
            if not documented_raw:
                continue
            documented = _canon_set(documented_raw)
            accepted = _canon_set(info.get("values") or [])

            undocumented = accepted - documented
            if undocumented:
                out.append(_finding(
                    WATCH, "doc-incomplete",
                    f"`{tool}.{param}` accepts {sorted(undocumented)}, which its own "
                    f"description never lists (it documents "
                    f"{sorted(documented_raw)}) — anyone reading the description "
                    "will believe these are unsupported"))

            # A documented value absent from the rejection list is only a suspicion.
            # The rejection list is a *display* list: `sdk_guide` omits "c#" from it
            # and accepts "c#" perfectly well. Send it before calling it broken.
            for value in sorted(set(documented_raw)):
                if _canon(value) in accepted:
                    continue
                if url is None:
                    continue
                if verify_literal(url, tool, param, value) is False:
                    out.append(_finding(
                        BREAKING, "doc-wrong",
                        f"`{tool}.{param}` documents '{value}' but the server "
                        "rejects it — following the description fails"))
    return out


def cross_tool(live):
    """Tools the plugin feeds one shared answer into must accept the same values.

    Found live on 2026-07-27: `sdk_guide` supports TypeScript and `generate_scaffold`
    does not, while the plugin carries a single `programming_language` into both.
    """
    out = []
    tools = live.get("tools", {})
    for param, names in CROSS_TOOL_AGREEMENT:
        sets = {}
        for name in names:
            if name not in tools:
                continue
            vals = accepted_values(tools[name], param)
            if vals:
                sets[name] = _canon_set(vals)
        if len(sets) < 2:
            continue
        union = set().union(*sets.values())
        for name, vals in sorted(sets.items()):
            missing = union - vals
            if missing:
                others = ", ".join(f"`{n}`" for n in sets if n != name)
                out.append(_finding(
                    WATCH, "cross-tool-mismatch",
                    f"`{name}.{param}` does not accept {sorted(missing)}, which "
                    f"{others} does — a bootcamper who picks one of those is routed "
                    f"into a tool that cannot serve them"))
    return out


def audit_static_contract(live):
    """Check tests/test_mcp_call_contracts.py's constants against the live server.

    The offline test is only as good as the day it was verified. If the live server
    disagrees with its hardcoded contract, the test is not merely stale — it is
    certifying something false, the failure mode its own docstring warns about.
    """
    out = []
    if not CONTRACT_TEST.is_file():
        return out
    text = CONTRACT_TEST.read_text(encoding="utf-8", errors="replace")
    tools = live.get("tools", {})

    match = re.search(r'CONTRACT_VERIFIED_ON\s*=\s*"(\d{4})-(\d{2})-(\d{2})"', text)
    if match:
        verified = _dt.date(*(int(g) for g in match.groups()))
        age = (_dt.date.today() - verified).days
        if age > CONTRACT_STALE_DAYS:
            out.append(_finding(WATCH, "contract-stale",
                                f"CONTRACT_VERIFIED_ON is {verified} ({age} days old, "
                                f"limit {CONTRACT_STALE_DAYS}) — re-verify and bump"))

    match = re.search(r"VALID_WORKFLOW_ACTIONS\s*=\s*\{([^}]*)\}", text)
    if match and "mapping_workflow" in tools:
        pinned = set(re.findall(r'"([a-z_]+)"', match.group(1)))
        live_actions = accepted_values(tools["mapping_workflow"], "action") or set()
        if live_actions and pinned != live_actions:
            out.append(_finding(
                BREAKING, "static-contract-wrong",
                f"tests pin VALID_WORKFLOW_ACTIONS={sorted(pinned)} but the server "
                f"says {sorted(live_actions)} — the offline test is certifying a "
                "contract that no longer holds"))

    block = re.search(r"REQUIRED_PARAMS\s*=\s*\{(.*?)\n\}", text, re.S)
    if block:
        for tool, params in re.findall(r'"([a-z_]+)":\s*\(([^)]*)\)', block.group(1)):
            pinned = set(re.findall(r'"([a-z_]+)"', params))
            if tool not in tools:
                out.append(_finding(
                    BREAKING, "static-contract-wrong",
                    f"tests pin REQUIRED_PARAMS for `{tool}`, which the server no "
                    "longer offers"))
                continue
            live_req = set(tools[tool].get("required", []))
            # mapping_workflow really does require data.workspace_dir, documented in
            # prose rather than in `required` — so only flag a pinned parameter the
            # server neither requires nor mentions anywhere in its description.
            desc = tools[tool].get("description", "")
            unmet = {p for p in pinned - live_req if p not in desc}
            if unmet:
                out.append(_finding(
                    WATCH, "static-contract-drift",
                    f"tests pin `{tool}` as requiring {sorted(unmet)}, but the live "
                    "schema neither requires it nor mentions it in the description"))
    return out


# ------------------------------------------------------------------------- report


def load_baseline():
    if BASELINE.is_file():
        return json.loads(BASELINE.read_text(encoding="utf-8"))
    return None


def save_baseline(snap):
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(
        json.dumps(snap, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")


def render(findings, as_json=False):
    if as_json:
        print(json.dumps(findings, indent=2))
        return
    if not findings:
        print("MCP: clean — no drift, no conformance violations.")
        return
    order = {BREAKING: 0, WATCH: 1, INFO: 2}
    for f in sorted(findings, key=lambda x: (order.get(x["severity"], 9), x["code"])):
        print(f"[{f['severity']:8}] {f['code']:22} {f['message']}")
    counts = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    print("\n" + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))


def collect(live, url=None):
    return (diff_baseline(live, load_baseline())
            + conformance(live, url)
            + server_quality(live, url)
            + cross_tool(live)
            + audit_static_contract(live))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", default="check",
                    choices=("check", "update", "snapshot"))
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--json", action="store_true", help="machine-readable findings")
    ap.add_argument("--no-content", action="store_true",
                    help="skip the get_capabilities content probe")
    args = ap.parse_args(argv)

    try:
        live = snapshot(args.url, args.timeout, probe_content=not args.no_content)
    except (urllib.error.URLError, OSError, ValueError, RuntimeError) as exc:
        # A probe failure is not a plugin defect. Exit 2, distinctly, so a network
        # blip is never filed as a finding.
        print(f"PROBE FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if args.command == "snapshot":
        print(json.dumps(live, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    if args.command == "update":
        # Settle every plugin literal the enumeration does not cover, so the
        # offline suite inherits the verdict instead of guessing.
        record_verified_extras(live, args.url, args.timeout)
        save_baseline(live)
        print(f"baseline written: {BASELINE.relative_to(REPO_ROOT)} "
              f"({len(live['tools'])} tools)")
        return 0

    findings = collect(live, args.url)
    render(findings, args.json)
    return 1 if any(f["severity"] == BREAKING for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
