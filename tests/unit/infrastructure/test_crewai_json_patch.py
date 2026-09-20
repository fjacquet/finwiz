"""The JSON-repair monkeypatch must only touch classes that opted in.

It patches BaseModel.model_validate_json process-wide; on the 2026-09-20 run it
fired on every research schema (SwotAnalysis, FiveForcesAnalysis, NewsDigest)
and logged 16 "JSON repair failed" errors for validations the research client
handles itself.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from finwiz.infrastructure.json import crewai_json_patch as patch_module


class _Registered(BaseModel):
    value: int


class _Unregistered(BaseModel):
    value: int


@pytest.fixture
def patched():
    patch_module.apply_json_repair_patch()
    patch_module.register_repairable(_Registered)
    yield
    patch_module.remove_json_repair_patch()
    patch_module._REPAIRABLE.clear()


def test_registered_class_is_repaired(patched) -> None:
    assert _Registered.model_validate_json('{"value": 1,}').value == 1


def test_unregistered_class_bypasses_repair(patched, mocker) -> None:
    spy = mocker.patch.object(patch_module, "repair_json", wraps=patch_module.repair_json)
    with pytest.raises(ValidationError):
        _Unregistered.model_validate_json('{"value": 1,}')
    spy.assert_not_called()


def test_is_repairable_reflects_registration(patched) -> None:
    assert patch_module.is_repairable(_Registered)
    assert not patch_module.is_repairable(_Unregistered)
