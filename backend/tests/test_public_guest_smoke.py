"""Keep the standalone public release probe's privacy assertions honest."""

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "verify-public-guest.py"
spec = importlib.util.spec_from_file_location("verify_public_guest", SCRIPT)
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_public_projection_rejects_nested_internal_fields():
    with pytest.raises(AssertionError, match="source_reference"):
        probe.assert_public_projection({"items": [{"part_number": "TEST", "source_reference": "private"}]})


def test_public_projection_allows_empty_budget_only_as_need_state():
    probe.assert_public_projection({
        "interpreted_need": {"budget_cny": None},
        "items": [{"part_number": "TEST", "evidence_level": "工程估算（候选筛选）"}],
    })
