import os
from pathlib import Path
import subprocess
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[2]


class ToolchainContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "project with spaces"
        (self.root / "scripts").mkdir(parents=True)
        (self.root / "mcp-backend/functions").mkdir(parents=True)
        (self.root / "mcp-website").mkdir()
        (self.root / "scripts/bootstrap-dev.sh").write_text(
            (PROJECT / "scripts/bootstrap-dev.sh").read_text()
            if (PROJECT / "scripts/bootstrap-dev.sh").exists() else ""
        )
        (self.root / ".python-version").write_text("3.11\n")
        (self.root / ".nvmrc").write_text("20\n")
        (self.root / "mcp-backend/functions/requirements-dev.txt").write_text("# fixture\n")
        (self.root / "mcp-website/package-lock.json").write_text("{}\n")
        self.log = self.root / "calls.log"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.python = self._stub("python3.11", '''#!/usr/bin/env python3
import os, pathlib, sys
if "--version" in sys.argv:
 print(os.environ.get("FAKE_PY_VERSION", "Python 3.11.9")); raise SystemExit
if sys.argv[1:3] == ["-m", "venv"]:
 target=pathlib.Path(sys.argv[3]); (target/"bin").mkdir(parents=True, exist_ok=True)
 exe=target/"bin/python"
 exe.write_text("#!/usr/bin/env python3\\nimport os,sys\\n"
  "print(os.environ.get('FAKE_VENV_VERSION','Python 3.11.9')) if '--version' in sys.argv else "
  "open(os.environ['CALL_LOG'],'a').write('venv-python '+repr(sys.argv[1:])+'\\\\n')\\n")
 exe.chmod(0o755)
 open(os.environ['CALL_LOG'],'a').write('create-venv\\n')
''')
        self.node = self._stub("node", '''#!/usr/bin/env python3
import os,sys
print(os.environ.get("FAKE_NODE_VERSION", "v20.18.0"))
''')
        self.npm = self._stub("npm", '''#!/usr/bin/env python3
import os,sys
open(os.environ['CALL_LOG'],'a').write('npm '+repr(sys.argv[1:])+' cwd='+os.getcwd()+'\\n')
''')

    def tearDown(self):
        self.temp.cleanup()

    def _stub(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)
        return path

    def run_bootstrap(self, **extra):
        env = os.environ.copy()
        env.update({"PATH": f"{self.bin}:{env['PATH']}", "PYTHON_BIN": str(self.python),
                    "CALL_LOG": str(self.log), **extra})
        return subprocess.run(["bash", str(self.root / "scripts/bootstrap-dev.sh")],
                              cwd=self.root, env=env, text=True, capture_output=True)

    def calls(self):
        return self.log.read_text() if self.log.exists() else ""

    def test_python_version_is_311(self):
        result = self.run_bootstrap(FAKE_PY_VERSION="Python 3.10.14")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("3.11", result.stderr + result.stdout)
        self.assertEqual(self.calls(), "")

    def test_node_version_is_20(self):
        result = self.run_bootstrap(FAKE_NODE_VERSION="v22.1.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("20", result.stderr + result.stdout)
        self.assertEqual(self.calls(), "")

    def test_bootstrap_creates_venv_installs_hashed_requirements_and_runs_npm_ci(self):
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        calls = self.calls()
        self.assertIn("create-venv", calls)
        self.assertIn("venv-python ['-m', 'pip', 'install', '--require-hashes', '-r',", calls)
        self.assertIn(str(self.root / "mcp-backend/functions/requirements-dev.txt"), calls)
        self.assertIn("npm ['ci'] cwd=" + str((self.root / "mcp-website").resolve()), calls)
        self.assertTrue((self.root / ".venv/bin/python").exists())

    def test_existing_venv_is_preserved_but_wrong_python_is_rejected(self):
        venv_python = self.root / ".venv/bin/python"
        venv_python.parent.mkdir(parents=True)
        venv_python.write_text("#!/usr/bin/env python3\nimport sys; print('Python 3.10.9')\n")
        venv_python.chmod(0o755)
        before = venv_python.read_bytes()
        result = self.run_bootstrap()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("3.11", result.stderr + result.stdout)
        self.assertEqual(venv_python.read_bytes(), before)
        self.assertNotIn("create-venv", self.calls())

    def test_existing_correct_venv_is_preserved_and_used(self):
        venv_python = self.root / ".venv/bin/python"
        venv_python.parent.mkdir(parents=True)
        venv_python.write_text("""#!/usr/bin/env python3
import os,sys
if '--version' in sys.argv: print('Python 3.11.9')
else: open(os.environ['CALL_LOG'],'a').write('existing-venv '+repr(sys.argv[1:])+'\\n')
""")
        venv_python.chmod(0o755)
        before = venv_python.read_bytes()
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(venv_python.read_bytes(), before)
        calls = self.calls()
        self.assertNotIn("create-venv", calls)
        self.assertIn("existing-venv ['-m', 'pip', 'install', '--require-hashes', '-r',", calls)
        self.assertIn("npm ['ci'] cwd=" + str((self.root / "mcp-website").resolve()), calls)

    def test_root_toolchain_versions_match_contract(self):
        self.assertEqual((PROJECT / ".python-version").read_text().strip(), "3.11")
        self.assertEqual((PROJECT / ".nvmrc").read_text().strip(), "20")

    def test_requirements_are_generated_from_inputs(self):
        for name in ("requirements.in", "requirements-dev.in"):
            with self.subTest(input=name):
                self.assertTrue((PROJECT / "mcp-backend/functions" / name).is_file(),
                                f"{name} should be an editable dependency input")

        for name in ("requirements.txt", "requirements-dev.txt"):
            with self.subTest(lock=name):
                content = (PROJECT / "mcp-backend/functions" / name).read_text()
                self.assertRegex(content, r"(?im)^# .*generated|^# .*autogenerated")
                self.assertRegex(content, r"(?im)--hash=sha256:")
                pinned = [line for line in content.splitlines()
                          if line.strip() and not line.lstrip().startswith("#")
                          and "==" in line and not line.lstrip().startswith("--")]
                self.assertTrue(pinned, f"{name} should contain pinned package entries")


if __name__ == "__main__":
    unittest.main()
