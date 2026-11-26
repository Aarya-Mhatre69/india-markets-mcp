"""Keep the MCP registry manifest in step with the package, so a release can't drift."""

import json
import re
from pathlib import Path

from india_markets_mcp import __version__

ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_versions_agree():
    manifest = json.loads(read("server.json"))
    project = re.search(r'^version = "([^"]+)"', read("pyproject.toml"), re.M).group(1)
    assert __version__ == project
    assert manifest["version"] == project
    assert [p["version"] for p in manifest["packages"]] == [project]


def test_readme_carries_ownership_marker():
    # The registry looks for this line in the README published to PyPI.
    name = json.loads(read("server.json"))["name"]
    assert f"<!-- mcp-name: {name} -->" in read("README.md")


def test_manifest_fits_registry_limits():
    manifest = json.loads(read("server.json"))
    assert 1 <= len(manifest["description"]) <= 100
    assert 1 <= len(manifest["title"]) <= 100
