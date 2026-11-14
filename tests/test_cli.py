import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


def run(*args):
    return subprocess.run([sys.executable, "-m", "htmd.cli", *map(str, args)], cwd=ROOT,
                          env=ENV, text=True, capture_output=True)


def test_validate_all_examples():
    result = run("validate", "--profile", "view", "examples")
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("OK ") == 7


def test_parse_json():
    result = run("parse", "examples/concepts/device.htmd")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["htmd"] == "0.1"


def test_graph_json():
    result = run("graph", "examples")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["nodes"] and data["edges"]


def test_render_html():
    result = run("render", "--profile", "view", "--full", "examples/ui/device-panel.htmd")
    assert result.returncode == 0, result.stderr
    assert "<!doctype html>" in result.stdout
    assert "<button" in result.stdout


def test_invalid_document_returns_nonzero(tmp_path):
    bad = tmp_path / "bad.htmd"
    bad.write_text('<tool src="./script.py" />')
    result = run("validate", bad)
    assert result.returncode == 1
    assert "E_DIRECTIVE" in result.stderr


def test_render_output_error_returns_diagnostic(tmp_path):
    result = run('render', 'examples/concepts/device.htmd', '-o', tmp_path / 'missing' / 'out.html')
    assert result.returncode == 1
    assert 'ERROR' in result.stderr
    assert 'Traceback' not in result.stderr


def test_malformed_url_does_not_crash_validation(tmp_path):
    bad = tmp_path / 'bad.htmd'
    bad.write_text('<view>\n<a href="https://[">x</a>\n</view>', encoding='utf-8')
    result = run('validate', '--profile', 'view', bad)
    assert result.returncode == 1
    assert 'E_VIEW' in result.stderr
    assert 'Traceback' not in result.stderr
