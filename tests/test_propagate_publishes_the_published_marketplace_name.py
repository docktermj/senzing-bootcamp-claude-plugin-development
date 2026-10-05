"""The propagate mirror publishes the marketplace under its published name (#449).

Claude Code keys marketplaces by name and refuses one name with two sources, so the development
repo could not be added on a machine that already had the published plugin: both declared
`senzing-bootcamp`. The dev marketplace is now `senzing-bootcamp-dev`, and `propagate.sh`
rewrites it back on the way out.

⛔ **The rewrite is the change, not a follow-up.** A dev name that reached the public repo would
change the plugin ID (`senzing-bootcamp@senzing-bootcamp`) for every existing install. So this
module runs `propagate.sh` itself, against this repository, into a throwaway destination, and
checks what lands there: the published `marketplace.json` name, the install commands in
`docs/README.md`, and that no dev marketplace name survives in **any** propagated file, not
only the `.md` and `.json` files the rewrite pass reads.

⚠️ **`senzing-bootcamp-dev` is a prefix of longer names**, like the `-development` slug suffix
`propagate.sh` already warns about. The rewrite matches it only where no name character
(`[A-Za-z0-9_-]`) follows. `TheRewriteIsAnchored` runs the shipped script over a small fixture
tree to show a longer name such as `senzing-bootcamp-devtools` is left alone, and that the
plugin's own name, `senzing-bootcamp` in `plugin.json` (the slash-command namespace), is never
touched. Its negative control removes the rewrite and shows the dev name then survives.

⚠️ **Where `bash`, `git`, `rsync` or `python3` is absent, the module SKIPS and says so**
(INV-308). `propagate.sh` declares `rsync` a hard dependency and exits without it, so its
absence is a property of the test machine, not of the mirror. Nothing here establishes that
`claude plugin marketplace add` accepts the two marketplaces side by side: that needs the
`claude` CLI and the network, and is checked by hand in the pull request.

Source issue: #449.

Stdlib only; no network, no second checkout.

Run:  python3 -m unittest discover -s tests
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROPAGATE_REL = ".claude/skills/propagate-to-public/propagate.sh"
SCRIPT = REPO_ROOT / PROPAGATE_REL
PUBLIC_ORIGIN = "https://github.com/Senzing/senzing-bootcamp-claude-plugin.git"

DEV_NAME = "senzing-bootcamp-dev"
PUBLISHED_NAME = "senzing-bootcamp"
PLUGIN_NAME = "senzing-bootcamp"
#: The dev marketplace name as a whole name: not followed by a name character.
DEV_NAME_RE = re.compile(re.escape(DEV_NAME).encode() + rb"(?![A-Za-z0-9_-])")

#: The commands `docs/README.md` carries, in dev and as published.
DEV_COMMANDS = (
    "claude plugin install senzing-bootcamp@senzing-bootcamp-dev",
    "claude plugin update senzing-bootcamp@senzing-bootcamp-dev",
    "claude plugin uninstall senzing-bootcamp@senzing-bootcamp-dev",
    "claude plugin marketplace remove senzing-bootcamp-dev",
)
PUBLISHED_COMMANDS = tuple(c.replace(DEV_NAME, PUBLISHED_NAME) for c in DEV_COMMANDS)

HAVE_TOOLS = all(shutil.which(tool) for tool in ("bash", "git", "rsync", "python3"))
SKIP_REASON = (
    "bash, git, rsync and python3 are needed to run propagate.sh, so this guard COULD NOT RUN "
    "-- distinct from having run and found nothing (INV-308)")


def _env(home):
    """The caller's environment with its git configuration shut out."""
    return dict(os.environ, HOME=str(home), GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def _public_checkout(path):
    """An empty git repo whose origin passes propagate.sh's destination guard."""
    path.mkdir(parents=True)
    env = _env(path.parent)
    subprocess.run(["git", "init", "-q", str(path)], check=True, capture_output=True, env=env)
    subprocess.run(["git", "-C", str(path), "remote", "add", "origin", PUBLIC_ORIGIN],
                   check=True, capture_output=True, env=env)
    return path


def _propagate(script, dest):
    """Run a propagate.sh into `dest`; return the completed process."""
    return subprocess.run(["bash", str(script), str(dest)], capture_output=True,
                          env=_env(dest.parent))


def _files(root):
    """Every file under `root`, outside `.git/`, as root-relative POSIX paths."""
    found = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d != ".git"]
        for fn in fns:
            found.append((Path(dp) / fn).relative_to(root).as_posix())
    return sorted(found)


def _dev_name_sites(root):
    """`path:line` for every whole-name occurrence of the dev marketplace name under `root`."""
    sites = []
    for rel in _files(root):
        data = (root / rel).read_bytes()
        for m in DEV_NAME_RE.finditer(data):
            sites.append("%s:%d" % (rel, data.count(b"\n", 0, m.start()) + 1))
    return sites


def _report(done):
    return "\nstdout:\n%s\nstderr:\n%s" % (done.stdout.decode("utf-8", "replace"),
                                         done.stderr.decode("utf-8", "replace"))


class TheDevRepoDeclaresItsOwnName(unittest.TestCase):
    """The source side: without the rename, the two marketplaces still collide."""

    def test_the_dev_marketplace_is_named_senzing_bootcamp_dev(self):
        data = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text("utf-8"))
        self.assertEqual(data["name"], DEV_NAME,
                         "the dev marketplace shares the published name again, so it cannot be "
                         "added where the published plugin is installed (#449)")

    def test_the_plugin_keeps_its_own_name(self):
        manifest = REPO_ROOT / "plugins" / "senzing-bootcamp" / ".claude-plugin" / "plugin.json"
        self.assertEqual(json.loads(manifest.read_text("utf-8"))["name"], PLUGIN_NAME,
                         "plugin.json's name is the slash-command namespace and ships as-is; "
                         "#449 renames the marketplace only")
        listed = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json")
                            .read_text("utf-8"))["plugins"]
        self.assertEqual([p["name"] for p in listed], [PLUGIN_NAME])

    def test_the_dev_install_docs_name_the_dev_marketplace(self):
        text = (REPO_ROOT / "docs" / "README.md").read_text("utf-8")
        for command in DEV_COMMANDS:
            with self.subTest(command=command):
                self.assertIn(command, text)


@unittest.skipUnless(HAVE_TOOLS, SKIP_REASON)
class ThePropagatedTreeCarriesThePublishedName(unittest.TestCase):
    """This repository, as propagate.sh publishes it."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dest = _public_checkout(Path(cls._tmp.name) / "public")
        cls.done = _propagate(SCRIPT, cls.dest)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def setUp(self):
        self.assertEqual(self.done.returncode, 0, "propagate.sh failed" + _report(self.done))

    def test_the_published_marketplace_is_named_senzing_bootcamp(self):
        data = json.loads((self.dest / ".claude-plugin" / "marketplace.json").read_text("utf-8"))
        self.assertEqual(data["name"], PUBLISHED_NAME,
                         "the published marketplace was renamed, which changes the plugin ID "
                         "for every existing install")
        self.assertEqual(data["owner"]["name"], "Senzing")

    def test_no_dev_marketplace_name_survives_anywhere(self):
        self.assertEqual(_dev_name_sites(self.dest), [],
                         "the dev marketplace name reached the public tree")

    def test_the_published_install_docs_name_the_published_marketplace(self):
        text = (self.dest / "docs" / "README.md").read_text("utf-8")
        for command in PUBLISHED_COMMANDS:
            with self.subTest(command=command):
                self.assertIn(command, text)

    def test_the_plugin_name_is_published_unchanged(self):
        manifest = self.dest / "plugins" / "senzing-bootcamp" / ".claude-plugin" / "plugin.json"
        self.assertEqual(json.loads(manifest.read_text("utf-8"))["name"], PLUGIN_NAME)


#: A minimal dev tree for the anchoring checks: each file holds the dev name in a different
#: position, beside longer names that must survive.
FIXTURE = {
    ".claude-plugin/marketplace.json":
        '{\n  "name": "senzing-bootcamp-dev",\n  "owner": {\n    "name": "docktermj"\n  },\n'
        '  "plugins": [{ "name": "senzing-bootcamp" }]\n}\n',
    "plugins/senzing-bootcamp/.claude-plugin/plugin.json": '{\n  "name": "senzing-bootcamp"\n}\n',
    "plugins/senzing-bootcamp/notes.md":
        "Run `/senzing-bootcamp:start-bootcamp`.\n"
        "Longer names stay: senzing-bootcamp-devtools, senzing-bootcamp-dev_x, "
        "senzing-bootcamp-dev-2.\n"
        "The marketplace is senzing-bootcamp-dev.\n",
    "docs/README.md": "\n".join(DEV_COMMANDS) + "\nends with senzing-bootcamp-dev",
    "README.md": "See docktermj/senzing-bootcamp-claude-plugin-development\n",
}


@unittest.skipUnless(HAVE_TOOLS, SKIP_REASON)
class TheRewriteIsAnchored(unittest.TestCase):
    """The shipped rewrite over a fixture tree, where every position is known."""

    def _run(self, script_text):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        dev = Path(tmp.name) / "dev"
        for rel, text in {**FIXTURE, PROPAGATE_REL: script_text}.items():
            (dev / rel).parent.mkdir(parents=True, exist_ok=True)
            (dev / rel).write_bytes(text.encode("utf-8"))
        dest = _public_checkout(Path(tmp.name) / "public")
        done = _propagate(dev / PROPAGATE_REL, dest)
        self.assertEqual(done.returncode, 0, "propagate.sh failed" + _report(done))
        return dest, done

    @classmethod
    def _script(cls):
        return SCRIPT.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")

    def test_the_whole_name_is_rewritten_in_every_position(self):
        dest, _ = self._run(self._script())
        self.assertEqual(_dev_name_sites(dest), [])
        self.assertEqual(json.loads((dest / ".claude-plugin" / "marketplace.json")
                                    .read_text("utf-8"))["name"], PUBLISHED_NAME)
        readme = (dest / "docs" / "README.md").read_text("utf-8")
        self.assertEqual(readme, "\n".join(PUBLISHED_COMMANDS) + "\nends with senzing-bootcamp")
        self.assertIn("The marketplace is senzing-bootcamp.\n",
                      (dest / "plugins/senzing-bootcamp/notes.md").read_text("utf-8"))

    def test_longer_names_and_the_plugin_name_are_left_alone(self):
        dest, _ = self._run(self._script())
        notes = (dest / "plugins/senzing-bootcamp/notes.md").read_text("utf-8")
        for name in ("senzing-bootcamp-devtools", "senzing-bootcamp-dev_x", "senzing-bootcamp-dev-2",
                     "/senzing-bootcamp:start-bootcamp"):
            with self.subTest(name=name):
                self.assertIn(name, notes, "the rewrite is not anchored: it changed %s" % name)
        self.assertEqual(json.loads((dest / "plugins/senzing-bootcamp/.claude-plugin/plugin.json")
                                    .read_text("utf-8"))["name"], PLUGIN_NAME)
        market = json.loads((dest / ".claude-plugin" / "marketplace.json").read_text("utf-8"))
        self.assertEqual([p["name"] for p in market["plugins"]], [PLUGIN_NAME])

    def test_a_second_run_publishes_the_same_tree(self):
        dest, _ = self._run(self._script())
        first = {rel: (dest / rel).read_bytes() for rel in _files(dest)}
        again = _propagate(dest.parent / "dev" / PROPAGATE_REL, dest)
        self.assertEqual(again.returncode, 0, _report(again))
        self.assertEqual({rel: (dest / rel).read_bytes() for rel in _files(dest)}, first)

    def test_negative_control_without_the_rewrite_the_dev_name_survives(self):
        text = self._script()
        lines = ("    t = MKT_RE.sub(MKT_NEW, t)\n",
                 "        t = t.replace('\"name\": \"%s\"' % MKT_OLD, '\"name\": \"%s\"' % MKT_NEW)\n")
        for line in lines:
            self.assertEqual(text.count(line), 1,
                             "propagate.sh no longer carries %r once; the control mutates nothing"
                             % line.strip())
            text = text.replace(line, "")
        dest, _ = self._run(text)
        sites = _dev_name_sites(dest)
        for rel in (".claude-plugin/marketplace.json", "docs/README.md",
                    "plugins/senzing-bootcamp/notes.md"):
            with self.subTest(file=rel):
                self.assertTrue(any(s.startswith(rel + ":") for s in sites),
                                "%s lost the dev name with the rewrite removed: %s" % (rel, sites))


if __name__ == "__main__":
    unittest.main()
