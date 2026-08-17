"""Tests for asset-class-aware strategic analysis (ETF/crypto framing, not just stock).

Strategic research (SWOT/Porter) used to be gated to
``asset_class == "stock"`` at two separate call sites (`stages/__init__.py` and
the legacy `_run_qualitative_and_strategic_in_parallel` helper), which
structurally excluded 38 of 64 holdings — every ETF and crypto — from any
strategic posture coverage. This module removes the gate and gives ETFs and
crypto a framing that fits them, while preserving the per-framework output
caps (Task 4) that keep the model inside its parseable-JSON budget in every
branch — losing those caps in an asset-class branch is what opened the
circuit breaker and killed 31 holdings.
"""

from __future__ import annotations

import pytest


class TestSwotAssetClassFraming:
    def test_etf_swot_asks_about_fees_and_concentration(self):
        from finwiz.analysis.strategic_research import _swot_prompt

        etf = _swot_prompt("VUSA.L", "", "", "", "16 août 2026", asset_class="etf")
        assert "concentration" in etf.lower()
        assert "frais" in etf.lower()

    def test_crypto_swot_asks_about_protocol_and_regulation(self):
        from finwiz.analysis.strategic_research import _swot_prompt

        crypto = _swot_prompt("BTC-USD", "", "", "", "16 août 2026", asset_class="crypto")
        assert "protocole" in crypto.lower()
        assert "réglementaire" in crypto.lower()


class TestPorterAssetClassFraming:
    def test_etf_porter_maps_forces_to_provider_competition_and_fees(self):
        """For ETFs, Porter's forces map to provider competition and fee pressure."""
        from finwiz.analysis.strategic_research import _porter_prompt

        etf = _porter_prompt("VUSA.L", "", "", "", "16 août 2026", asset_class="etf")
        assert "frais" in etf.lower()
        assert "émetteur" in etf.lower() or "fournisseur d'indice" in etf.lower()

    def test_crypto_porter_maps_forces_to_protocol_ecosystem(self):
        from finwiz.analysis.strategic_research import _porter_prompt

        crypto = _porter_prompt("BTC-USD", "", "", "", "16 août 2026", asset_class="crypto")
        assert "protocole" in crypto.lower()
        assert "réglementaire" in crypto.lower()


class TestCapsSurviveEveryAssetClassBranch:
    """Correction C: Task 4's output caps must not be lost when the prompt
    builders branch on asset_class. The brief's own tests only assert framing
    words for etf/crypto — nothing asserted the caps survived per branch.
    """

    @pytest.mark.parametrize("asset_class", ["stock", "etf", "crypto"])
    def test_swot_caps_present_for_every_asset_class(self, asset_class):
        from finwiz.analysis.strategic_research import _swot_prompt

        prompt = _swot_prompt("TICK", "Sector", "Industry", "", "16 août 2026", asset_class=asset_class)
        assert "4 puces" in prompt
        assert "400 caractères" in prompt

    @pytest.mark.parametrize("asset_class", ["stock", "etf", "crypto"])
    def test_porter_caps_present_for_every_asset_class(self, asset_class):
        from finwiz.analysis.strategic_research import _porter_prompt

        prompt = _porter_prompt("TICK", "Sector", "Industry", "", "16 août 2026", asset_class=asset_class)
        assert "250 caractères" in prompt
        assert "400 caractères" in prompt

    @pytest.mark.parametrize("asset_class", ["etf", "crypto"])
    def test_caps_interpolate_constants_not_hardcoded_for_non_stock_classes(self, asset_class, mocker):
        """Mirrors test_strategic_prompts.py::test_prompts_interpolate_constants_not_hardcoded,
        which only ever exercised the (default) stock branch.
        """
        import finwiz.analysis.strategic_research as strategic_research
        from finwiz.analysis.strategic_research import _porter_prompt, _swot_prompt

        mocker.patch.object(strategic_research, "MAX_BULLETS_SWOT", 9)
        mocker.patch.object(strategic_research, "MAX_RATIONALE_CHARS", 444)

        swot = _swot_prompt("TICK", "Sector", "Industry", "", "16 août 2026", asset_class=asset_class)
        assert "9 puces" in swot, "SWOT should interpolate MAX_BULLETS_SWOT"

        porter = _porter_prompt("TICK", "Sector", "Industry", "", "16 août 2026", asset_class=asset_class)
        assert "444 caractères" in porter, "Porter should interpolate MAX_RATIONALE_CHARS"


class TestAssetClassThreadsThroughGatherFunctions:
    """asset_class must reach the prompt builders through
    _safe_strategic -> gather_strategic_analysis[_sync] -> the three prompt
    functions (Correction B)."""

    async def test_gather_strategic_analysis_forwards_asset_class_to_prompts(self, mocker):
        import finwiz.analysis.strategic_research as strategic_research

        mocker.patch.object(strategic_research, "perplexity_with_retry", new=mocker.AsyncMock(return_value=None))
        swot_spy = mocker.spy(strategic_research, "_swot_prompt")
        porter_spy = mocker.spy(strategic_research, "_porter_prompt")

        await strategic_research.gather_strategic_analysis(ticker="VUSA.L", asset_class="etf")

        assert swot_spy.call_args.kwargs["asset_class"] == "etf"
        assert porter_spy.call_args.kwargs["asset_class"] == "etf"

    def test_gather_strategic_analysis_sync_forwards_asset_class(self, mocker):
        import finwiz.analysis.strategic_research as strategic_research

        mocker.patch.object(strategic_research, "perplexity_with_retry", new=mocker.AsyncMock(return_value=None))
        swot_spy = mocker.spy(strategic_research, "_swot_prompt")

        strategic_research.gather_strategic_analysis_sync(ticker="BTC-USD", asset_class="crypto")

        assert swot_spy.call_args.kwargs["asset_class"] == "crypto"

    def test_gather_strategic_analysis_sync_defaults_to_stock(self, mocker):
        import finwiz.analysis.strategic_research as strategic_research

        mocker.patch.object(strategic_research, "perplexity_with_retry", new=mocker.AsyncMock(return_value=None))
        swot_spy = mocker.spy(strategic_research, "_swot_prompt")

        strategic_research.gather_strategic_analysis_sync(ticker="AAPL")

        assert swot_spy.call_args.kwargs["asset_class"] == "stock"

    def test_safe_strategic_forwards_asset_class(self, mocker):
        from finwiz.analysis.stages.qualify import _safe_strategic

        gather_mock = mocker.patch(
            "finwiz.analysis.strategic_research.gather_strategic_analysis_sync",
            return_value=None,
        )

        _safe_strategic("VUSA.L", "Sector", "Industry", "desc", asset_class="etf")

        assert gather_mock.call_args.kwargs["asset_class"] == "etf"

    def test_safe_strategic_defaults_to_stock(self, mocker):
        from finwiz.analysis.stages.qualify import _safe_strategic

        gather_mock = mocker.patch(
            "finwiz.analysis.strategic_research.gather_strategic_analysis_sync",
            return_value=None,
        )

        _safe_strategic("AAPL", "Sector", "Industry", "desc")

        assert gather_mock.call_args.kwargs["asset_class"] == "stock"
