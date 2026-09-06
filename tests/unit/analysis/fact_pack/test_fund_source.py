"""Fund facts from yfinance funds_data. Shapes are the real 2026-09-06 ones."""

import pandas as pd
import pytest

from finwiz.analysis.fact_pack.sources import fund_source, yfinance_source


class _FakeFundsData:
    def __init__(self, operations=None, holdings=None, asset_classes=None, sectors=None):
        self._operations = operations
        self._holdings = holdings
        self._asset_classes = asset_classes if asset_classes is not None else {}
        self._sectors = sectors if sectors is not None else {}

    @property
    def fund_operations(self):
        if isinstance(self._operations, Exception):
            raise self._operations
        return self._operations

    @property
    def top_holdings(self):
        if isinstance(self._holdings, Exception):
            raise self._holdings
        return self._holdings

    @property
    def asset_classes(self):
        return self._asset_classes

    @property
    def sector_weightings(self):
        return self._sectors


class _FakeTicker:
    def __init__(self, funds_data):
        self.funds_data = funds_data


@pytest.fixture
def info():
    return {
        "quoteType": "ETF",
        "fundFamily": "BlackRock Asset Management Ireland - ETF",
        "legalType": "Exchange Traded Fund",
        "fundInceptionDate": 1602460800,
        "longName": "iShares MSCI World SRI UCITS ETF",
    }


@pytest.fixture
def operations():
    # Real shape: index carries the metric names, one column per ticker.
    return pd.DataFrame(
        {"2B7K.DE": [0.002, 0.0, 143259.6], "Category Average": [0.0031, 0.1, 500000.0]},
        index=["Annual Report Expense Ratio", "Annual Holdings Turnover", "Total Net Assets"],
    )


@pytest.fixture
def holdings():
    frame = pd.DataFrame({"Name": ["NVIDIA Corp", "ASML Holding"], "Holding Percent": [0.077756, 0.0421]}, index=["NVDA", "ASML.AS"])
    frame.index.name = "Symbol"
    return frame


class TestFundFacts:
    def test_identity_comes_from_info(self, mocker, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        facts, _, _ = fund_source.fund_facts("2B7K.DE", info)
        assert facts.issuer == "BlackRock Asset Management Ireland - ETF"
        assert facts.legal_type == "Exchange Traded Fund"
        assert facts.inception_year == 2020

    def test_expense_ratio_is_read_from_the_ticker_column(self, mocker, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        facts, _, _ = fund_source.fund_facts("2B7K.DE", info)
        assert facts.expense_ratio == pytest.approx(0.002)
        assert facts.turnover == pytest.approx(0.0)

    def test_total_net_assets_is_not_modelled(self, mocker, info, operations, holdings):
        """Its unit is undocumented; an AUM without a unit is worse than none."""
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        facts, _, _ = fund_source.fund_facts("2B7K.DE", info)
        assert not hasattr(facts, "total_net_assets")

    def test_holdings_are_converted_with_symbol_from_the_index(self, mocker, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        facts, _, _ = fund_source.fund_facts("2B7K.DE", info)
        assert [h.symbol for h in facts.top_holdings] == ["NVDA", "ASML.AS"]
        assert facts.top_holdings[0].name == "NVIDIA Corp"
        assert facts.top_holdings[0].weight == pytest.approx(0.077756)
        # Type purity, not a JSON-caching guard: numpy.float64 subclasses float
        # and serialises fine, and Pydantic would coerce it anyway.
        assert type(facts.top_holdings[0].weight) is float

    def test_a_fund_with_no_published_holdings_still_produces_facts(self, mocker, info, operations):
        """AEEM.PA returns an empty frame while 2B7K.DE returns ten rows."""
        empty = pd.DataFrame({"Name": [], "Holding Percent": []})
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, empty)))
        facts, _, _ = fund_source.fund_facts("AEEM.PA", info)
        assert facts.top_holdings == []
        assert facts.expense_ratio == pytest.approx(0.002)

    def test_a_failing_accessor_degrades_that_field_only(self, mocker, info, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(RuntimeError("boom"), holdings)))
        facts, _, _ = fund_source.fund_facts("2B7K.DE", info)
        assert facts.expense_ratio is None
        assert [h.symbol for h in facts.top_holdings] == ["NVDA", "ASML.AS"]

    def test_funds_data_failing_entirely_still_yields_identity_facts(self, mocker, info):
        mocker.patch.object(yfinance_source, "_ticker", side_effect=RuntimeError("network down"))
        facts, _, _ = fund_source.fund_facts("2B7K.DE", info)
        assert facts.issuer == "BlackRock Asset Management Ireland - ETF"
        assert facts.top_holdings == []

    def test_an_info_without_an_issuer_yields_none(self, mocker):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData()))
        facts, citations, sources = fund_source.fund_facts("XXXX.DE", {"quoteType": "ETF"})
        assert facts is None
        assert citations == ()
        assert sources == ()

    def test_the_quote_page_is_the_citation(self, mocker, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        _, citations, sources = fund_source.fund_facts("2B7K.DE", info)
        assert citations == ("https://finance.yahoo.com/quote/2B7K.DE",)
        assert sources == ("yfinance.info", "yfinance.funds_data")


class TestExpenseRatioTripwire:
    """yfinance is authoritative; data/etf_expense_ratios.yaml is a tripwire only."""

    def test_a_disagreement_beyond_5bp_logs_a_warning_naming_both_values(self, mocker, caplog, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        mocker.patch.object(fund_source, "get_fallback_expense_ratio", return_value=0.0100)  # yfinance says 0.002
        with caplog.at_level("WARNING"):
            facts, _, _ = fund_source.fund_facts("2B7K.DE", info)
        assert facts.expense_ratio == pytest.approx(0.002)  # yfinance value wins, untouched
        assert any("0.002" in r.message and "0.01" in r.message for r in caplog.records)

    def test_agreement_within_5bp_stays_silent(self, mocker, caplog, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        mocker.patch.object(fund_source, "get_fallback_expense_ratio", return_value=0.00205)  # 0.002 + 5bp/2
        with caplog.at_level("WARNING"):
            fund_source.fund_facts("2B7K.DE", info)
        assert caplog.records == []

    def test_no_entry_in_the_table_stays_silent(self, mocker, caplog, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        mocker.patch.object(fund_source, "get_fallback_expense_ratio", return_value=None)
        with caplog.at_level("WARNING"):
            fund_source.fund_facts("2B7K.DE", info)
        assert caplog.records == []


@pytest.fixture
def zero_ter_operations():
    """The real 2026-09-06 shape for VUSA.L, CSYZ.DE, GREIT.SW, XB0T.DE, ZSIL.SW:
    yfinance reports a literal 0.0, never a genuine zero-fee fund."""
    return pd.DataFrame(
        {"VUSA.L": [0.0, 0.05, 9000000.0], "Category Average": [0.0031, 0.1, 500000.0]},
        index=["Annual Report Expense Ratio", "Annual Holdings Turnover", "Total Net Assets"],
    )


class TestExpenseRatioFalseZero:
    """yfinance encodes an unknown expense ratio as 0.0, not a missing row --
    the same trap as maxSupply == 0 meaning 'uncapped' for crypto."""

    def test_a_false_zero_is_replaced_by_the_curated_table_value(self, mocker, caplog, info, zero_ter_operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(zero_ter_operations, holdings)))
        mocker.patch.object(fund_source, "get_fallback_expense_ratio", return_value=0.0007)
        with caplog.at_level("WARNING"):
            facts, _, sources = fund_source.fund_facts("VUSA.L", info)
        assert facts.expense_ratio == pytest.approx(0.0007)
        assert any("false zero" in r.message for r in caplog.records)
        assert sources == ("yfinance.info", "yfinance.funds_data", "etf_expense_ratios.yaml")

    def test_a_false_zero_with_no_table_entry_yields_none(self, mocker, caplog, info, zero_ter_operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(zero_ter_operations, holdings)))
        mocker.patch.object(fund_source, "get_fallback_expense_ratio", return_value=None)
        with caplog.at_level("WARNING"):
            facts, _, sources = fund_source.fund_facts("VUSA.L", info)
        assert facts.expense_ratio is None
        assert any("no data/etf_expense_ratios.yaml entry" in r.message for r in caplog.records)
        assert sources == ("yfinance.info", "yfinance.funds_data")

    def test_a_genuine_nonzero_value_is_left_alone(self, mocker, info, operations, holdings):
        """Regression guard: the false-zero fix must not touch real values."""
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        mocker.patch.object(fund_source, "get_fallback_expense_ratio", return_value=None)
        facts, _, sources = fund_source.fund_facts("2B7K.DE", info)
        assert facts.expense_ratio == pytest.approx(0.002)
        assert sources == ("yfinance.info", "yfinance.funds_data")


@pytest.fixture
def negative_turnover_operations():
    """The real 2026-09-06 shape for a portfolio ETF reporting -0.6146 turnover."""
    return pd.DataFrame(
        {"2B7K.DE": [0.002, -0.6146, 143259.6], "Category Average": [0.0031, 0.1, 500000.0]},
        index=["Annual Report Expense Ratio", "Annual Holdings Turnover", "Total Net Assets"],
    )


class TestTurnoverNormalization:
    def test_a_negative_turnover_is_treated_as_unknown(self, mocker, info, negative_turnover_operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(negative_turnover_operations, holdings)))
        facts, _, _ = fund_source.fund_facts("2B7K.DE", info)
        assert facts.turnover is None
        # The rest of the pack is unaffected by one bad field.
        assert facts.expense_ratio == pytest.approx(0.002)


class TestHoldingsWeightNormalization:
    """A NaN or out-of-domain weight is yfinance being scraped, not contractual --
    FundHolding's own `ge=0.0, le=1.0` bound is not enforced by this source, and a
    missing "Holding Percent" arrives as NaN, not None, so the earlier `weight is
    None` guard never catches it. One unusable row must cost that row, not the
    whole holdings table -- see fund_facts's own construction guard for what a
    ValidationError escaping this function used to do to the rest of the pack.
    """

    def test_a_nan_weight_drops_only_that_row(self):
        frame = pd.DataFrame({"Name": ["NVIDIA Corp", "ASML Holding"], "Holding Percent": [0.07, float("nan")]}, index=["NVDA", "ASML.AS"])
        holdings = fund_source._holdings(frame)
        assert [h.symbol for h in holdings] == ["NVDA"]

    def test_a_weight_above_one_drops_its_row(self):
        frame = pd.DataFrame({"Name": ["NVIDIA Corp"], "Holding Percent": [1.5]}, index=["NVDA"])
        assert fund_source._holdings(frame) == []

    def test_a_negative_weight_drops_its_row(self):
        frame = pd.DataFrame({"Name": ["NVIDIA Corp"], "Holding Percent": [-0.1]}, index=["NVDA"])
        assert fund_source._holdings(frame) == []

    def test_a_table_of_entirely_bad_rows_yields_an_empty_list_not_a_raise(self):
        frame = pd.DataFrame({"Name": ["A", "B"], "Holding Percent": [float("nan"), 2.0]}, index=["A", "B"])
        assert fund_source._holdings(frame) == []

    def test_a_broken_holdings_table_does_not_cost_the_rest_of_the_pack(self, mocker, info, operations):
        """The real point: the expense ratio must survive a broken holdings table.

        Before the fix, a NaN weight in `top_holdings` raised a ValidationError
        inside `_holdings`, which escaped into `fund_facts`'s own construction
        `try` and discarded the whole pack -- issuer, expense ratio, everything
        -- degrading the fund to confidence 0.00.
        """
        frame = pd.DataFrame({"Name": ["A", "B"], "Holding Percent": [float("nan"), 2.0]}, index=["A", "B"])
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, frame)))
        facts, _, _ = fund_source.fund_facts("2B7K.DE", info)
        assert facts is not None
        assert facts.top_holdings == []
        assert facts.expense_ratio == pytest.approx(0.002)
        assert facts.issuer == "BlackRock Asset Management Ireland - ETF"


class TestConstructionGuard:
    """Spec §6: no source may raise. This is the backstop for a schema
    constraint this module's own normalization doesn't yet know about."""

    def test_an_unexpected_construction_failure_yields_none_not_a_raise(self, mocker, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        mocker.patch.object(fund_source, "FundFacts", side_effect=ValueError("boom"))
        facts, citations, sources = fund_source.fund_facts("2B7K.DE", info)
        assert facts is None
        assert citations == ()
        assert sources == ()
