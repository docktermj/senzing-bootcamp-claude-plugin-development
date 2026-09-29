"""The How tab must say so when an entity's final state is unsettled (#169).

`renderHow` drew an entity's history from `HOW_RESULTS.RESOLUTION_STEPS[]` and never read
`HOW_RESULTS.FINAL_STATE`. With steps it said "Senzing built this entity in N step(s)" even when
the steps left the records in two groups that no step joins; with no steps it pooled the members
of **every** virtual entity and said the records "resolved **directly** into one entity". Both
sentences are false when the final state carries either of the two signs #154 audits:

- `HOW_RESULTS.FINAL_STATE.NEED_REEVALUATION` is non-zero, or
- `HOW_RESULTS.FINAL_STATE.VIRTUAL_ENTITIES[]` has more than one element.

Observed 2026-09-25 on Senzing SDK 4.4.1: entities 307153, 307169 and 307249 carried both, while
the entity lookup and the export reported one entity each.

Three layers, because the contract is what a non-Python build is generated from (INV-090):

1. an always-run check on the served JavaScript text: `renderHow` reads both signs, and each
   one-entity sentence sits behind the `unsettled` guard;
2. an always-run check on the contract (`visualization-api-reference.md`): the `/api/how` entry
   states the two signs and no longer says the virtual entities describe one resolved entity, and
   the How-action text requires the notice and the per-group rendering;
3. a headless render that drives `renderHow` with fixture responses — both branches, with both
   signs, each sign alone, neither, and no `FINAL_STATE` — and reads the rendered DOM. It follows
   `tests/test_source_encoding_renders_distinctly.py` and skips without Chrome. "Unchanged with
   neither sign" is asserted by rendering the pre-#169 `renderHow` beside the current one on the
   same page and comparing the two outputs, rather than by re-describing the old markup.

Enforces **INV-330** (a How rendering reads the final state, names an unsettled one, and never
presents it as one resolved entity). ⚠️ It pins the reference text and the Python reference and
cannot observe a build generated for another language.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "scripts")
SERVER = os.path.join(SCRIPTS, "senzing_viz_server.py")
CONTRACT = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "skills",
                        "module-03b-truthset-visualization", "visualization-api-reference.md")

BUILT_SENTENCE = "Senzing built this entity in"
DIRECT_SENTENCE = "These records resolved <b>directly</b> into one entity"

#: `renderHow` as it shipped before #169, renamed so it can run beside the current one. It is the
#: baseline for "with neither sign, today's rendering is unchanged": a check that re-described the
#: old markup would pass for any rendering that happened to contain the same sentence.
RENDER_HOW_BEFORE = r"""
function renderHowBefore(data){const hr=(data.result||{}).HOW_RESULTS||{};const steps=hr.RESOLUTION_STEPS||[];
  if(steps.length){
    let h="<div class='verdict'>Senzing built this entity in <b>"+steps.length+"</b> step(s), each merging two groups of records.</div>";
    steps.forEach(function(st,i){const mi=st.MATCH_INFO||{};const mk=mi.MATCH_KEY||"";const rule=mi.ERRULE_CODE||"";
      const v1=st.VIRTUAL_ENTITY_1||{};const v2=st.VIRTUAL_ENTITY_2||{};
      h+="<div class='step'><div><span class='num'>"+(st.STEP||(i+1))+"</span><b>Merged on</b> "+mkChips(mk)+(rule?" · <code>"+esc(rule)+"</code>":"")+"</div>"+
        "<div class='recs' style='margin-top:8px'><div class='rec'><b>Group A</b><br>"+_recordChips(v1.MEMBER_RECORDS)+"</div>"+
        "<div class='rec'><b>Group B</b><br>"+_recordChips(v2.MEMBER_RECORDS)+"</div></div></div>";});
    return h;}
  const ve=((hr.FINAL_STATE||{}).VIRTUAL_ENTITIES)||[];
  var members=[];ve.forEach(function(v){(v.MEMBER_RECORDS||[]).forEach(function(m){members.push(m);});});
  var n=0;members.forEach(function(m){n+=((m.RECORDS||[]).length);});
  return "<div class='verdict'>These records resolved <b>directly</b> into one entity — Senzing found them consistent enough to merge with no intermediate steps.</div>"+
    "<h4>"+n+" record"+(n===1?"":"s")+" in this entity</h4>"+
    "<div class='recs'><div class='rec' style='min-width:auto'>"+_recordChips(members)+"</div></div>";}
"""


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def render_how_source():
    """The text of `renderHow`, from its declaration to the next top-level function."""
    text = read(SERVER)
    start = text.find("function renderHow(")
    if start < 0:
        return ""
    end = re.compile(r"\n(?:async\s+)?function\s").search(text, start + 1)
    return text[start:end.start() if end else len(text)]


# --------------------------------------------------------------------------- #
# 1. The served JavaScript text (always runs)
# --------------------------------------------------------------------------- #
class RenderHowReadsBothSigns(unittest.TestCase):
    def setUp(self):
        self.src = render_how_source()
        self.assertTrue(self.src, "renderHow not found in senzing_viz_server.py")

    def test_it_reads_need_reevaluation_from_final_state(self):
        self.assertRegex(
            self.src, r"FINAL_STATE\|\|\{\}\)\.NEED_REEVALUATION",
            "renderHow never reads HOW_RESULTS.FINAL_STATE.NEED_REEVALUATION, so an unsettled "
            "entity renders as a settled one")

    def test_it_counts_the_virtual_entities(self):
        self.assertIn("FINAL_STATE||{}).VIRTUAL_ENTITIES", self.src)
        self.assertRegex(
            self.src, r"\bve\.length\s*>\s*1",
            "renderHow never checks whether FINAL_STATE holds more than one virtual entity")

    def test_the_guard_is_built_from_both_signs(self):
        self.assertRegex(self.src, r"typeof nr\s*===\s*\"number\"\s*&&\s*nr\s*!==\s*0",
                         "NEED_REEVALUATION must count as a sign whenever it is a non-zero "
                         "integer, the type the response schema gives it")
        self.assertRegex(self.src, r"const unsettled\s*=\s*signs\.length\s*>\s*0")

    def test_the_built_verdict_is_conditional_on_neither_sign(self):
        self.assertRegex(
            self.src,
            r"unsettled\s*\?\s*notice\s*:\s*\"<div class='verdict'>" + re.escape(BUILT_SENTENCE),
            "the with-steps verdict must be replaced by the notice when a sign is present")
        self.assertEqual(1, self.src.count(BUILT_SENTENCE),
                         "a second, unguarded copy of the built-in-N-steps verdict exists")

    def test_the_direct_sentence_is_conditional_on_neither_sign(self):
        self.assertRegex(
            self.src,
            r"unsettled\s*\?\s*notice\s*\+\s*grouped\s*:\s*\"<div class='verdict'>"
            + re.escape(DIRECT_SENTENCE),
            "the no-steps 'resolved directly into one entity' sentence must be replaced by the "
            "notice and the per-group rendering when a sign is present")
        self.assertEqual(1, self.src.count(DIRECT_SENTENCE),
                         "a second, unguarded copy of the resolved-directly sentence exists")


# --------------------------------------------------------------------------- #
# 2. The contract (always runs)
# --------------------------------------------------------------------------- #
class ContractStatesTheTwoSigns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(CONTRACT)
        start = cls.text.find("**`GET /api/how?entity_id=<id>`:**")
        end = cls.text.find("**`GET /api/dashboard`", start)
        cls.how_entry = cls.text[start:end] if start >= 0 and end > start else ""
        start = cls.text.find("**(INV-330) How? when the final state is unsettled.**")
        end = cls.text.find("\n## ", start)
        cls.how_action = cls.text[start:end] if start >= 0 and end > start else ""

    def test_the_how_entry_exists(self):
        self.assertTrue(self.how_entry, "the /api/how entry was not found in the contract")

    def test_the_how_entry_no_longer_describes_one_resolved_entity(self):
        self.assertNotIn("describes the resolved entity", self.how_entry,
                         "the contract still says FINAL_STATE.VIRTUAL_ENTITIES[] describes one "
                         "resolved entity, so every other-language build repeats the false claim")
        self.assertRegex(self.how_entry, r"more than\s+one\*\*\s+virtual entity")

    def test_the_how_entry_states_both_signs(self):
        self.assertIn("`HOW_RESULTS.FINAL_STATE.NEED_REEVALUATION` is non-zero", self.how_entry)
        self.assertRegex(self.how_entry,
                         r"`HOW_RESULTS\.FINAL_STATE\.VIRTUAL_ENTITIES\[\]` has more than one\s+"
                         r"element")
        self.assertIn("Either one alone is enough", self.how_entry)

    def test_the_how_entry_gives_the_flag_no_meaning_and_marks_the_negative(self):
        self.assertIn("Attach no meaning to `NEED_REEVALUATION`", self.how_entry)
        # `[:]`, not a literal colon: the marker scanner reads tests/ too, and would take this
        # pattern for a malformed marker.
        marker = re.search(r"<!-- MCP-NEGATIVE[:] (.*?) -->", self.how_entry)
        self.assertIsNotNone(marker, "the absence of a documented meaning carries no "
                                     "MCP-NEGATIVE marker (INV-194/INV-213)")
        self.assertIn("owner: get_sdk_reference(topic='response_schemas'", marker.group(1))

    def test_the_how_action_requires_the_notice_and_the_groups(self):
        self.assertTrue(self.how_action, "the How-action rendering text for an unsettled final "
                                         "state was not found in the contract")
        self.assertIn("unsettled-state notice", self.how_action)
        self.assertIn("MUST NOT claim one entity", self.how_action)
        self.assertIn("the notice replaces the step-count verdict", self.how_action)
        self.assertIn("**its own group**", self.how_action)
        self.assertIn("never pooled into one list", self.how_action)
        self.assertIn("Escaping", self.how_action)


# --------------------------------------------------------------------------- #
# 3. The rendered DOM (needs headless Chrome)
# --------------------------------------------------------------------------- #
def find_chrome():
    for name in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    return None


def load_server():
    sys.path.insert(0, SCRIPTS)
    spec = importlib.util.spec_from_file_location("viz_server_how_state_test", SERVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["viz_server_how_state_test"] = module
    spec.loader.exec_module(module)
    return module


def member(ds, rid, internal_id):
    return {"INTERNAL_ID": internal_id, "RECORDS": [{"DATA_SOURCE": ds, "RECORD_ID": rid}]}


#: The first group's records. `<i>` in a record ID and a virtual-entity ID is data, and must reach
#: the page as text: the notice and the groups follow the contract's escaping rule.
GROUP_1 = {"VIRTUAL_ENTITY_ID": "V1-S2",
           "MEMBER_RECORDS": [member("CUSTOMERS", "1001", 1), member("CUSTOMERS", "1002", 2),
                              member("REFERENCE", "2001", 3)]}
GROUP_2 = {"VIRTUAL_ENTITY_ID": "V<i>9</i>",
           "MEMBER_RECORDS": [member("WATCHLIST", "<i>3001</i>", 4), member("WATCHLIST", "3002", 5)]}

STEPS = [
    {"STEP": 1, "MATCH_INFO": {"MATCH_KEY": "+NAME+ADDRESS", "ERRULE_CODE": "CNAME_CFF"},
     "VIRTUAL_ENTITY_1": {"MEMBER_RECORDS": [member("CUSTOMERS", "1001", 1)]},
     "VIRTUAL_ENTITY_2": {"MEMBER_RECORDS": [member("CUSTOMERS", "1002", 2)]}},
    {"STEP": 2, "MATCH_INFO": {"MATCH_KEY": "+NAME+PHONE", "ERRULE_CODE": "CNAME_CFF"},
     "VIRTUAL_ENTITY_1": {"MEMBER_RECORDS": [member("WATCHLIST", "<i>3001</i>", 4)]},
     "VIRTUAL_ENTITY_2": {"MEMBER_RECORDS": [member("WATCHLIST", "3002", 5)]}},
]

#: sign name -> FINAL_STATE. `None` means the response carries no FINAL_STATE at all.
FINAL_STATES = {
    "both": {"NEED_REEVALUATION": 1, "VIRTUAL_ENTITIES": [GROUP_1, GROUP_2]},
    "nr": {"NEED_REEVALUATION": 1, "VIRTUAL_ENTITIES": [GROUP_1]},
    "ve": {"NEED_REEVALUATION": 0, "VIRTUAL_ENTITIES": [GROUP_1, GROUP_2]},
    "neither": {"NEED_REEVALUATION": 0, "VIRTUAL_ENTITIES": [GROUP_1]},
    "nofinal": None,
}
SIGNED = ("both", "nr", "ve")
SETTLED = ("neither", "nofinal")


def fixtures():
    out = {}
    for branch, steps in (("steps", STEPS), ("nosteps", [])):
        for sign, final in FINAL_STATES.items():
            how = {"RESOLUTION_STEPS": steps}
            if final is not None:
                how["FINAL_STATE"] = final
            out["%s_%s" % (branch, sign)] = {"HOW_RESULTS": how}
    return out


@unittest.skipUnless(find_chrome(), "no headless Chrome/Chromium available")
class HowTabRendersTheFinalStateItIsGiven(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_server()
        cls.cases = fixtures()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.chrome = find_chrome()
        cls.dom = cls.render()
        cls.after = dict(re.findall(r'<section id="howcase-([\w-]+)">(.*?)</section>',
                                    cls.dom, re.S))
        cls.before = dict(re.findall(r'<section id="howbefore-([\w-]+)">(.*?)</section>',
                                     cls.dom, re.S))

    @classmethod
    def render(cls):
        sources = ["CUSTOMERS", "REFERENCE", "WATCHLIST"]
        payload = {
            "stats": {"records_total": 1, "entities_total": 1, "multi_record_entities": 0,
                      "cross_source_entities": 0, "relationships_total": 0,
                      "data_sources_total": len(sources),
                      "histogram": {"1": 1, "2": 0, "3": 0, "4+": 0},
                      "bucket_entities": {"1": [], "2": [], "3": [], "4+": []},
                      "sample_entities": []},
            "graph": {"nodes": [{"entity_id": 307153, "entity_name": "Fixture",
                                 "record_count": 1, "data_sources": ["CUSTOMERS"]}],
                      "edges": []},
            "merges": {"entities": []}, "records": {},
            "overlap": {"sources": sources, "matrix": [[1] * len(sources) for _ in sources]},
            "matchkeys": {"keys": []}, "features": {"features": []},
        }
        # Every case is rendered twice — by the current renderHow and by the pre-#169 one — and
        # one case is also driven through explain(), the path the How? button takes, so the
        # modal wiring is exercised and not only the function.
        shim = (
            "<script>const __DATA__=" + cls.module._script_json(payload) + ";"
            "const __HOW__=" + cls.module._script_json(cls.cases) + ";"
            + RENDER_HOW_BEFORE +
            "window.fetch=function(u){var p=u.split('?')[0].replace('/api/','');"
            "if(p==='how'){return Promise.resolve({json:function(){"
            "return Promise.resolve({entity_id:307153,result:__HOW__.nosteps_both});}});}"
            "if(p==='search'){return Promise.resolve({json:function(){"
            "return Promise.resolve({results:[]});}});}"
            "return Promise.resolve({json:function(){return Promise.resolve(__DATA__[p]);}});};"
            "window.addEventListener('load',function(){setTimeout(async function(){"
            "var out=document.createElement('div');out.id='howcases';"
            "function put(id,fn,d){var s=document.createElement('section');s.id=id;"
            "try{s.innerHTML=fn(d);}catch(e){s.textContent='THREW: '+e;}out.appendChild(s);}"
            "Object.keys(__HOW__).forEach(function(k){"
            "put('howcase-'+k,renderHow,{result:__HOW__[k]});"
            "put('howbefore-'+k,renderHowBefore,{result:__HOW__[k]});});"
            "try{await explain('how',307153,'Fixture');}catch(e){}"
            "var m=document.createElement('section');m.id='howcase-modal';"
            "m.innerHTML=document.getElementById('modal').innerHTML;out.appendChild(m);"
            "document.body.appendChild(out);},0);});</script>"
        )
        page = cls.module.render_page("How state", data_shim=shim, sources=sources)
        path = Path(cls.tmp.name) / "how_state.html"
        path.write_text(page, encoding="utf-8")
        result = subprocess.run(
            [cls.chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--window-size=1400,900", "--virtual-time-budget=20000",
             "--dump-dom", path.as_uri()],
            capture_output=True, text=True, timeout=180,
        )
        return result.stdout

    def html(self, case):
        self.assertIn(case, self.after, "case %s did not render at all" % case)
        body = self.after[case]
        self.assertFalse(body.startswith("THREW"), "renderHow threw on %s: %s" % (case, body))
        return body

    @staticmethod
    def groups(body):
        return re.findall(r'<div class="rec how-group"[^>]*>(.*?)</div>', body, re.S)

    def test_every_case_rendered(self):
        self.assertEqual(sorted(list(self.cases) + ["modal"]), sorted(self.after))

    # -- a sign present: the notice, and no one-entity claim ------------------ #

    def test_a_sign_shows_the_notice_naming_only_the_signs_present(self):
        for branch in ("steps", "nosteps"):
            for sign in SIGNED:
                case = "%s_%s" % (branch, sign)
                with self.subTest(case=case):
                    body = self.html(case)
                    self.assertIn('class="verdict how-unsettled"', body)
                    names_nr = "<code>FINAL_STATE.NEED_REEVALUATION</code> is <b>1</b>" in body
                    names_ve = ("<code>FINAL_STATE.VIRTUAL_ENTITIES</code> lists <b>2</b> "
                                "virtual entities") in body
                    self.assertEqual(sign in ("both", "nr"), names_nr,
                                     "NEED_REEVALUATION named wrongly in %s" % case)
                    self.assertEqual(sign in ("both", "ve"), names_ve,
                                     "the virtual-entity count named wrongly in %s" % case)

    def test_a_sign_removes_every_one_entity_claim(self):
        for branch in ("steps", "nosteps"):
            for sign in SIGNED:
                case = "%s_%s" % (branch, sign)
                with self.subTest(case=case):
                    body = self.html(case)
                    self.assertNotIn(BUILT_SENTENCE, body)
                    self.assertNotIn("resolved <b>directly</b>", body)
                    self.assertNotIn("in this entity</h4>", body)

    def test_the_notice_gives_the_flag_no_meaning(self):
        """INV-080/INV-149: no route documents what NEED_REEVALUATION means or how to clear it."""
        for case in ("steps_both", "nosteps_both"):
            with self.subTest(case=case):
                notice = re.search(r'<div class="verdict how-unsettled">(.*?)</div>',
                                   self.html(case), re.S)
                self.assertIsNotNone(notice, "no unsettled-state notice rendered in %s" % case)
                text = notice.group(1).replace("NEED_REEVALUATION", "").lower()
                for word in ("reevaluat", "re-evaluat", "stale", "pending", "fix", "should"):
                    self.assertNotIn(word, text, "the notice interprets the flag (%r)" % word)

    def test_with_steps_the_steps_still_render(self):
        for sign in SIGNED + SETTLED:
            with self.subTest(sign=sign):
                self.assertEqual(2, self.html("steps_" + sign).count('<div class="step">'))

    # -- no steps: each virtual entity is its own group ----------------------- #

    def test_no_steps_with_two_virtual_entities_shows_two_groups(self):
        for sign in ("both", "ve"):
            with self.subTest(sign=sign):
                groups = self.groups(self.html("nosteps_" + sign))
                self.assertEqual(2, len(groups), "the virtual entities were pooled")
                self.assertIn("CUSTOMERS:1001", groups[0])
                self.assertIn("REFERENCE:2001", groups[0])
                self.assertNotIn("WATCHLIST", groups[0])
                self.assertIn("WATCHLIST:3002", groups[1])
                self.assertNotIn("CUSTOMERS", groups[1])
                self.assertIn("3 records", groups[0])
                self.assertIn("2 records", groups[1])

    def test_no_steps_with_one_flagged_virtual_entity_shows_that_one_group(self):
        groups = self.groups(self.html("nosteps_nr"))
        self.assertEqual(1, len(groups))
        self.assertIn("V1-S2", groups[0])

    def test_data_sourced_text_is_escaped(self):
        for case in ("nosteps_both", "nosteps_ve", "steps_both"):
            with self.subTest(case=case):
                body = self.html(case)
                self.assertNotIn("<i>", body, "a record or virtual-entity ID reached the page "
                                              "as markup")
                self.assertIn("&lt;i&gt;3001&lt;/i&gt;", body)
        self.assertIn("V&lt;i&gt;9&lt;/i&gt;", self.html("nosteps_both"))

    # -- neither sign: today's rendering, unchanged -------------------------- #

    def test_neither_sign_renders_exactly_as_before(self):
        for branch in ("steps", "nosteps"):
            for sign in SETTLED:
                case = "%s_%s" % (branch, sign)
                with self.subTest(case=case):
                    self.assertEqual(self.before.get(case), self.html(case),
                                     "%s changed although neither sign is present" % case)
                    self.assertNotIn("how-unsettled", self.html(case))

    def test_the_settled_sentences_still_render(self):
        self.assertIn(BUILT_SENTENCE + " <b>2</b> step(s)", self.html("steps_neither"))
        self.assertIn(DIRECT_SENTENCE, self.html("nosteps_neither"))

    # -- the How? button path ------------------------------------------------- #

    def test_the_how_modal_carries_the_notice_and_the_groups(self):
        body = self.after.get("modal", "")
        self.assertIn('class="verdict how-unsettled"', body,
                      "explain('how') did not render the notice in the modal")
        self.assertEqual(2, len(self.groups(body)))
        self.assertNotIn("resolved <b>directly</b>", body)


if __name__ == "__main__":
    unittest.main()
