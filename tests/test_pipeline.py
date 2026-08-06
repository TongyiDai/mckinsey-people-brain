import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def sample(self):
        body = "人才组织 AI 转型。" * 200
        return [
            {"firm": "McKinsey", "title": "AI talent strategy", "source_url": "https://www.mckinsey.com/a/?utm_source=test#x", "status": "ok", "body_text": body, "body_chars": len(body), "fetched_at_utc": "2026-08-06T00:00:00Z"},
            {"firm": "McKinsey", "title": "short duplicate", "source_url": "https://www.mckinsey.com/a/", "status": "no_body", "body_text": "", "body_chars": 0},
            {"firm": "BCG", "title": "restricted page", "source_url": "https://www.bcg.com/b", "status": "restricted", "body_text": "", "body_chars": 0, "failure_reason": "403"},
        ]

    def test_validate_and_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run"
            run.mkdir()
            (run / "fetched.json").write_text(json.dumps(self.sample(), ensure_ascii=False), encoding="utf-8")
            validate = subprocess.run([sys.executable, str(ROOT / "scripts/validate_records.py"), str(run / "fetched.json"), "--min-body-chars", "800"], capture_output=True, text=True)
            self.assertEqual(validate.returncode, 0)
            build = subprocess.run([sys.executable, str(ROOT / "scripts/build_agent_db.py"), "--run-dir", str(run), "--min-body-chars", "800"], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stderr)
            manifest = json.loads((run / "agent-db/manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["record_count"], 2)
            self.assertTrue((run / "agent-db/agent-db.sqlite").exists())


if __name__ == "__main__":
    unittest.main()
