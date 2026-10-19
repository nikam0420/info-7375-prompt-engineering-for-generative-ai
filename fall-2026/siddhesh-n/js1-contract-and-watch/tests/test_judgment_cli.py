"""The Claude Code CLI judgment backend, with CONSTRUCTED fake `claude` processes.

No real `claude` process is started here; every "CLI output" below is a
hand-written fixture returned by an injected runner.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import resume
import test_evaluation_and_demo as eval_tests
from test_evaluation_and_demo import FakeJudge, fill_labels
from test_judgment import PID, POSTING, good
from watcher import ROOT, claude_cli, cli
from watcher import evaluation as ev
from watcher.judgment import build_user_message, claude_views, load_prompt

MODEL = "claude-opus-5-5"
AUTH_OK = {"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty",
           "email": "constructed@example.com", "orgName": "Constructed Org", "subscriptionType": "pro"}


def cli_result(text, session_id, **overrides):
    obj = {"type": "result", "subtype": "success", "is_error": False, "result": text, "session_id": session_id,
           "num_turns": 1, "duration_ms": 10, "duration_api_ms": 9, "total_cost_usd": 0.0,
           "usage": {"input_tokens": 1, "output_tokens": 1}, "modelUsage": {MODEL: {"inputTokens": 1}}}
    obj.update(overrides)
    return obj


class FakeRunner:
    """Stands in for subprocess: answers --version and auth status, and records each judgment call."""

    def __init__(self, text=None, *, auth=AUTH_OK, exit_code=0, stdout=None, raise_on_call=None, **overrides):
        self.text = json.dumps(good()) if text is None else text
        self.auth, self.exit_code, self.stdout = auth, exit_code, stdout
        self.raise_on_call, self.overrides = raise_on_call, overrides
        self.calls = []
        self.probes = []

    def __call__(self, argv, stdin, cwd, env, timeout):
        if argv[1:] == ["--version"]:
            self.probes.append(argv)
            return 0, b"9.9.9 (Claude Code, constructed)\n", b""
        if argv[1:] == ["auth", "status"]:
            self.probes.append(argv)
            return 0, json.dumps(self.auth).encode(), b""
        self.calls.append({"argv": argv, "stdin": stdin, "cwd": cwd, "cwd_listing": os.listdir(cwd),
                           "env": env, "timeout": timeout})
        if self.raise_on_call:
            raise self.raise_on_call
        if self.stdout is not None:
            return self.exit_code, self.stdout, b""
        sid = argv[argv.index("--session-id") + 1]
        obj = {**cli_result(self.text, sid), **self.overrides}
        return self.exit_code, json.dumps(obj).encode(), b"constructed stderr"


class CLIBackendTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def judge(self, runner, model=MODEL, effort="medium", label=None):
        return claude_cli.obtain_judgment_cli(resume(), POSTING, prompt_version="baseline", purpose="test",
                                              model=model, effort=effort, runner=runner, outputs_dir=self.out,
                                              call_label=label)

    def saved(self):
        return [json.loads(p.read_text()) for p in sorted(self.out.rglob("*.json"))]

    def assert_unavailable(self, j):
        self.assertEqual(j["status"], "unavailable")
        self.assertNotIn("verdict", j)

    def test_valid_judgment_saved_with_exact_prompts_raw_output_and_metadata(self):
        r = FakeRunner()
        j = self.judge(r)
        self.assertEqual(j["status"], "available")
        self.assertEqual(j["backend"], "claude-code-cli")
        self.assertEqual(j["model_reported"], [MODEL])
        [rec] = self.saved()
        system, sha = load_prompt("baseline")
        rv, pv = claude_views(resume(), POSTING)
        self.assertEqual(rec["system_prompt"], system)
        self.assertEqual(rec["prompt_sha256"], sha)
        self.assertEqual(rec["user_message"], build_user_message(rv, pv))
        self.assertEqual(rec["argv"], r.calls[0]["argv"])
        self.assertTrue(rec["request_started_at"] and rec["response_received_at"])
        self.assertEqual(rec["cli_version"], "9.9.9 (Claude Code, constructed)")
        self.assertEqual(rec["auth"]["authMethod"], "claude.ai")
        self.assertNotIn("constructed@example.com", json.dumps(rec), "account email must not be saved")
        self.assertNotIn("Constructed Org", json.dumps(rec))
        self.assertTrue(rec["validation"]["valid"])
        raw = next(self.out.rglob("*.stdout.bin")).read_bytes()
        self.assertEqual(json.loads(raw)["session_id"], rec["session_id_requested"])
        self.assertEqual(next(self.out.rglob("*.stderr.bin")).read_bytes(), b"constructed stderr")

    def test_only_fixed_prompt_and_views_are_sent(self):
        r = FakeRunner()
        self.judge(r)
        call = r.calls[0]
        argv = call["argv"]
        system, _ = load_prompt("baseline")
        rv, pv = claude_views(resume(), POSTING)
        self.assertEqual(call["stdin"].decode(), build_user_message(rv, pv))
        self.assertEqual(argv[argv.index("--system-prompt") + 1], system)
        sent = json.dumps(argv) + call["stdin"].decode()
        for private in ("Test Person", "test.person@example.com", "202-555-0147"):
            self.assertNotIn(private, sent)
        self.assertNotIn("Uses SQL", json.dumps(argv), "posting text goes on stdin, not argv")

    def test_tools_disabled_and_no_conversation_reuse(self):
        r = FakeRunner()
        self.judge(r)
        argv = r.calls[0]["argv"]
        self.assertEqual(argv[:2], ["claude", "-p"])
        self.assertEqual(argv[argv.index("--tools") + 1], "")
        self.assertEqual(argv[argv.index("--disallowedTools") + 1], "*")
        self.assertEqual(argv[argv.index("--max-turns") + 1], "1")
        self.assertEqual(argv[argv.index("--output-format") + 1], "json")
        self.assertEqual(argv[argv.index("--model") + 1], MODEL)
        self.assertEqual(argv[argv.index("--effort") + 1], "medium")
        for flag in ("--no-session-persistence", "--strict-mcp-config", "--restricted", "--safe-mode",
                     "--disable-slash-commands"):
            self.assertIn(flag, argv)
        for flag in claude_cli.FORBIDDEN_FLAGS + ("--append-system-prompt", "--add-dir", "--mcp-config",
                                                  "--json-schema", "--bare"):
            self.assertNotIn(flag, argv)

    def test_each_repetition_is_a_new_process_session_and_empty_dir(self):
        r = FakeRunner()
        for k in range(3):
            self.judge(r, label=f"call{k}")
        sids = [c["argv"][c["argv"].index("--session-id") + 1] for c in r.calls]
        self.assertEqual(len(set(sids)), 3)
        self.assertEqual(len({c["cwd"] for c in r.calls}), 3)
        for c in r.calls:
            self.assertEqual(c["cwd_listing"], [], "working dir must be empty")
            self.assertNotEqual(Path(c["cwd"]).resolve(), ROOT.resolve())
            self.assertFalse(Path(c["cwd"]).exists(), "temporary working dir is removed afterwards")
        self.assertEqual(len(self.saved()), 3)

    def test_effort_none_omits_flag(self):
        r = FakeRunner()
        self.judge(r, effort=None)
        self.assertNotIn("--effort", r.calls[0]["argv"])

    def test_api_key_and_nested_session_env_removed(self):
        env = {"ANTHROPIC_API_KEY": "sk-constructed", "ANTHROPIC_BASE_URL": "https://x.example",
               "CLAUDE_CODE_USE_BEDROCK": "1", "CLAUDECODE": "1", "CLAUDE_CONFIG_DIR": "/constructed",
               "PATH": os.environ.get("PATH", "")}
        r = FakeRunner()
        with mock.patch.dict(os.environ, env, clear=True):
            self.judge(r)
        child = r.calls[0]["env"]
        for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "CLAUDE_CODE_USE_BEDROCK", "CLAUDECODE"):
            self.assertNotIn(k, child)
        self.assertEqual(child["CLAUDE_CONFIG_DIR"], "/constructed")
        [rec] = self.saved()
        self.assertIn("ANTHROPIC_API_KEY", rec["env_removed"])
        self.assertNotIn("sk-constructed", json.dumps(rec))

    def test_strict_validator_applied_without_repair(self):
        text = json.dumps(good())
        for bad in ("```json\n" + text + "\n```", "Here you go: " + text, json.dumps(good(resume_fields=[])),
                    json.dumps(good(posting_id=PID + 1)), json.dumps(good(confidence=1)), ""):
            with self.subTest(bad=bad[:30]):
                j = self.judge(FakeRunner(bad))
                self.assert_unavailable(j)
                rec = json.loads(Path(j["raw_record"]).read_text())
                self.assertFalse(rec["validation"]["valid"])
                self.assertTrue(rec["validation"]["errors"])
                self.assertEqual(rec["output_text"], bad, "the raw text is saved as returned")

    def test_cli_envelope_failures_unavailable(self):
        cases = {
            "nonzero exit": FakeRunner(exit_code=1),
            "is_error": FakeRunner(is_error=True),
            "max turns": FakeRunner(subtype="error_max_turns"),
            "two turns": FakeRunner(num_turns=2),
            "tool attempted": FakeRunner(permission_denials=[{"tool_name": "Read"}]),
            "wrong session": FakeRunner(session_id="00000000-0000-0000-0000-000000000000"),
            "fallback model": FakeRunner(modelUsage={"claude-sonnet-5-5": {}}),
            "no model info": FakeRunner(modelUsage={}),
            "not json": FakeRunner(stdout=b"Error: something went wrong"),
            "not result": FakeRunner(stdout=json.dumps({"type": "system"}).encode()),
            "no text": FakeRunner(result=None),
        }
        expected = {"nonzero exit": "exited with code 1", "is_error": "is_error", "max turns": "subtype",
                    "two turns": "turns", "tool attempted": "permission denials", "wrong session": "session_id",
                    "fallback model": "not among models", "no model info": "not among models",
                    "not json": "not JSON", "not result": "type", "no text": "no text result"}
        for name, r in cases.items():
            with self.subTest(name):
                j = self.judge(r)
                self.assert_unavailable(j)
                self.assertIn(expected[name], j["reason"])
                self.assertEqual(len(r.calls), 1)

    def test_alias_model_not_matched_but_reported(self):
        j = self.judge(FakeRunner(), model="opus")
        self.assertEqual(j["status"], "available")
        self.assertEqual(j["model_reported"], [MODEL])

    def test_not_account_login_means_no_judgment_call(self):
        for auth in ({**AUTH_OK, "authMethod": "api_key"}, {**AUTH_OK, "loggedIn": False},
                     {"loggedIn": False, "authMethod": "none"}):
            with self.subTest(auth=auth["authMethod"]):
                r = FakeRunner(auth=auth)
                self.assert_unavailable(self.judge(r))
                self.assertEqual(r.calls, [])

    def test_process_failure_unavailable_and_logged(self):
        r = FakeRunner(raise_on_call=claude_cli.ClaudeCLIError("constructed timeout"))
        j = self.judge(r)
        self.assert_unavailable(j)
        self.assertIn("constructed timeout", json.loads(Path(j["raw_record"]).read_text())["transport_error"])

    def test_missing_executable_means_no_call(self):
        with mock.patch("watcher.claude_cli.shutil.which", return_value=None), \
             mock.patch("watcher.claude_cli.default_runner") as runner:
            j = claude_cli.obtain_judgment_cli(resume(), POSTING, prompt_version="baseline", purpose="test",
                                               model=MODEL, effort=None, outputs_dir=self.out)
        self.assert_unavailable(j)
        runner.assert_not_called()
        self.assertEqual(self.saved(), [])

    def test_default_runner_passes_stdin_and_cwd(self):
        py = shutil.which("python3")
        code, out, _ = claude_cli.default_runner(
            [py, "-c", "import os,sys; print(os.getcwd()); print(sys.stdin.read())"], b"constructed-stdin",
            self.tmp.name, dict(os.environ), 30)
        self.assertEqual(code, 0)
        self.assertIn(b"constructed-stdin", out)
        self.assertIn(Path(self.tmp.name).resolve().name.encode(), out)


class CLIWiringTests(unittest.TestCase):
    def test_backend_option_dispatches_to_cli_and_defaults_to_api(self):
        args = cli.build_parser().parse_args(["consistency-run", "--backend", "cli", "--effort", "none"])
        with mock.patch("watcher.claude_cli.obtain_judgment_cli", return_value={"status": "unavailable"}) as c, \
             mock.patch("watcher.claude.obtain_judgment") as api:
            cli._claude_judge(args, resume())(POSTING, purpose="p", call_label="x")
        api.assert_not_called()
        self.assertEqual(c.call_args.kwargs["effort"], None)
        self.assertEqual(c.call_args.kwargs["call_label"], "x")
        self.assertEqual(cli.build_parser().parse_args(["consistency-run"]).backend, "api")


class CLIEvaluationGateTests(unittest.TestCase):
    """Reuses the constructed-sample setup from test_evaluation_and_demo; only the backend gate is new."""

    setUp = eval_tests.EvalTests.setUp
    tearDown = eval_tests.EvalTests.tearDown

    def test_cli_backend_runs_without_api_key_and_records_backend(self):
        fill_labels(self.eval_dir, "dev")
        judge = FakeJudge()
        with mock.patch.dict(os.environ, {}, clear=False), mock.patch("watcher.evaluation.shutil.which",
                                                                      return_value="/constructed/claude"):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            r = ev.run_consistency("baseline", judge_fn=judge, eval_dir=self.eval_dir, n_postings=1, calls=2,
                                   backend="cli")
        self.assertEqual(r["backend"], "cli")
        self.assertEqual(len(judge.calls), 2)

    def test_cli_backend_refused_without_executable_or_labels(self):
        judge = FakeJudge()
        with self.assertRaises(ev.EvaluationGateError):  # labels incomplete
            ev.run_consistency("baseline", judge_fn=judge, eval_dir=self.eval_dir, backend="cli")
        fill_labels(self.eval_dir, "dev")
        with mock.patch("watcher.evaluation.shutil.which", return_value=None), \
             self.assertRaises(ev.EvaluationGateError):
            ev.run_experiment("baseline", "dev", resume=resume(), judge_fn=judge, eval_dir=self.eval_dir,
                              prompts_dir=self.prompts, backend="cli")
        with self.assertRaises(ValueError):
            ev.run_consistency("baseline", judge_fn=judge, eval_dir=self.eval_dir, backend="web")
        self.assertEqual(judge.calls, [])



if __name__ == "__main__":
    unittest.main()
