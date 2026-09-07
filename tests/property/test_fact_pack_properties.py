"""Property-based tests for the fact-pack sources and their facts models.

One defect class appeared **six times** while this subsystem was built: a schema
bound that the source does not enforce, with fixtures that never violate it. A
negative turnover; three separate crypto raise paths; a ``NaN`` holding weight;
``.strip()`` on a non-string ``legalType``. Each was fixed where it was found,
and the next instance was waiting one file over.

Example-based tests could not have caught any of them, because the examples were
written by the same person who wrote the parser, from the same mental model of
what yfinance returns. yfinance's payloads are scraped, not contractual: a field
that is "always a string" arrives as an int, a float field arrives as ``NaN``,
and ``NaN`` slips every naive guard -- ``isinstance(nan, float)`` is ``True``,
``nan < 0`` is ``False``, ``nan is None`` is ``False``. Only ``math.isfinite``
catches it.

So these tests assert the contract the spec states -- *no source may raise* --
against inputs nobody imagined.
"""

from __future__ import annotations

import json
import math
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from finwiz.analysis.fact_pack.fragment import PLACEHOLDER
from finwiz.analysis.fact_pack.sources import crypto_source, fund_source
from finwiz.analysis.fact_pack.sources._numeric import _finite
from finwiz.analysis.fact_pack.sources._text import _safe_str
from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts, EquityFacts, FundFacts

# --------------------------------------------------------------------------
# Strategies: values shaped like yfinance's, including the shapes that bit.
# --------------------------------------------------------------------------

# Deliberately includes NaN and both infinities: allow_nan/allow_infinity
# default to False in Hypothesis, which would reproduce exactly the blind spot
# these tests exist to close.
hostile_floats = st.floats(allow_nan=True, allow_infinity=True)

hostile_scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    hostile_floats,
    st.text(),
    # Whitespace-only strings, explicitly. st.text() generates them far too
    # rarely to rely on, and they are the shape that matters here: truthy, so
    # they pass a `x or PLACEHOLDER` guard untouched, then empty after the
    # model's strip, so they fail min_length. Without these in the pool the
    # guard/bound test below is decorative -- verified by removing the strip
    # from _safe_str and watching it still pass.
    st.sampled_from(["", " ", "  ", "\t", "\n", "\r", "\r\n", "\x0b", "\x0c", "\x1f", "\u00a0", "\u2009"]),
    st.lists(st.integers(), max_size=3),
    st.dictionaries(st.text(max_size=5), st.integers(), max_size=3),
)

# yfinance `info` keys the fact-pack sources actually read. Values are drawn
# from the hostile pool, so every reader meets every wrong type in turn.
_INFO_KEYS = (
    "fundFamily",
    "legalType",
    "fundInceptionDate",
    "annualReportExpenseRatio",
    "annualHoldingsTurnover",
    "description",
    "maxSupply",
    "circulatingSupply",
    "marketCap",
    "startDate",
    "volume24HrMarketCapPercent",
    "coinMarketCapLink",
    "quoteType",
)

hostile_info = st.dictionaries(st.sampled_from(_INFO_KEYS), hostile_scalars, max_size=len(_INFO_KEYS))


@pytest.fixture(scope="module", autouse=True)
def _no_funds_data_network():
    """Neutralise the one networked seam, at module scope.

    ``fund_facts`` calls ``_funds_data``, which fetches. A function-scoped
    fixture here would trip Hypothesis's ``function_scoped_fixture`` health
    check, and suppressing that check is what left a real latent flake in
    ``test_utility_orchestrator_properties.py`` -- mock call history accumulating
    across all 100 examples. Module scope sidesteps both problems: the swap
    happens once, and Hypothesis has no objection to it.
    """
    original = fund_source._funds_data
    fund_source._funds_data = lambda _symbol: None
    yield
    fund_source._funds_data = original


# --------------------------------------------------------------------------
# The coercion leaves
# --------------------------------------------------------------------------


class TestNumericCoercion:
    @given(value=hostile_scalars)
    def test_finite_returns_a_finite_float_or_nothing(self, value: Any) -> None:
        """``_finite`` exists to make "not a usable number" a single answer.

        Anything it returns must be safe to put in a bounded schema field and to
        serialise as standards-compliant JSON. ``NaN`` and the infinities are
        neither: ``json.dumps`` emits bare ``NaN``/``Infinity`` tokens that any
        external reader rejects.
        """
        result = _finite(value)
        assert result is None or (isinstance(result, float) and math.isfinite(result))

    @given(value=hostile_floats)
    def test_finite_rejects_every_non_finite_float(self, value: float) -> None:
        if not math.isfinite(value):
            assert _finite(value) is None


class TestTextCoercion:
    @given(value=hostile_scalars, max_chars=st.integers(min_value=1, max_value=500))
    def test_safe_str_always_returns_a_bounded_string(self, value: Any, max_chars: int) -> None:
        """The fifth and sixth instances of the class were ``.strip()`` on a non-string."""
        result = _safe_str(value, max_chars)
        assert isinstance(result, str)
        assert len(result) <= max_chars

    @given(value=hostile_scalars)
    def test_a_non_string_is_absent_rather_than_an_error(self, value: Any) -> None:
        if not isinstance(value, str):
            assert _safe_str(value) == ""


# --------------------------------------------------------------------------
# The sources: "no source may raise" (spec §6)
# --------------------------------------------------------------------------


class TestSourcesNeverRaise:
    @settings(max_examples=200)
    @given(info=hostile_info)
    def test_fund_facts_never_raises_whatever_info_holds(self, info: dict[str, Any]) -> None:
        facts, citations, sources = fund_source.fund_facts("XXXX.DE", info)

        assert facts is None or isinstance(facts, FundFacts)
        assert isinstance(citations, tuple)
        assert isinstance(sources, tuple)

    @settings(max_examples=200)
    @given(info=hostile_info)
    def test_crypto_facts_never_raises_whatever_info_holds(self, info: dict[str, Any]) -> None:
        facts, citations = crypto_source.crypto_facts("BTC", info)

        assert facts is None or isinstance(facts, CryptoFacts)
        assert isinstance(citations, tuple)

    @settings(max_examples=200)
    @given(info=hostile_info)
    def test_a_built_fund_pack_is_json_serialisable_for_an_outside_reader(self, info: dict[str, Any]) -> None:
        """A pack that only Python can read is not a pack.

        ``json.dumps`` writes bare ``NaN``/``Infinity`` for non-finite floats and
        ``json.loads`` accepts them back, so a round-trip inside Python proves
        nothing. ``allow_nan=False`` is the check an external consumer applies.
        """
        facts, _, _ = fund_source.fund_facts("XXXX.DE", info)
        if facts is not None:
            json.dumps(facts.model_dump(mode="json"), allow_nan=False, default=str)


# --------------------------------------------------------------------------
# Model invariants
# --------------------------------------------------------------------------


class TestFactsModelInvariants:
    @given(
        max_supply=st.one_of(st.none(), st.floats(min_value=0, max_value=1e15, allow_nan=False, allow_infinity=False)),
        capped=st.booleans(),
    )
    def test_crypto_supply_cap_and_max_supply_can_never_disagree(self, max_supply: float | None, capped: bool) -> None:
        """yfinance encodes "uncapped" as ``maxSupply == 0``, which a naive reader
        records as a cap of zero coins. ``supply_is_capped`` exists so the two
        cases are stated rather than inferred -- which is only worth anything if
        the pair can never drift apart.
        """
        agree = capped == (max_supply is not None)
        try:
            facts = CryptoFacts(description="x", max_supply=max_supply, supply_is_capped=capped)
        except ValueError:
            assert not agree, "rejected a consistent pair"
            return
        assert agree, "accepted a contradictory pair"
        assert facts.supply_is_capped == (facts.max_supply is not None)

    @given(
        weight=st.one_of(st.none(), hostile_floats),
    )
    def test_a_holding_weight_is_a_fraction_or_unknown(self, weight: float | None) -> None:
        """The fourth instance: a ``NaN`` weight passed every ad-hoc guard and
        reached a field bounded to [0, 1]. Unknown is a value; nonsense is not.
        """
        acceptable = weight is None or (math.isfinite(weight) and 0.0 <= weight <= 1.0)
        try:
            from finwiz.schemas.hybrid_analysis.fact_pack import FundHolding

            holding = FundHolding(symbol="MSFT", name="Microsoft", weight=weight)
        except ValueError:
            assert not acceptable, f"rejected an acceptable weight: {weight!r}"
            return
        assert acceptable, f"accepted an unacceptable weight: {weight!r}"
        assert holding.weight is None or math.isfinite(holding.weight)

    @given(value=hostile_scalars)
    def test_the_composer_guard_always_yields_text_the_model_accepts(self, value: Any) -> None:
        """The guard and the bound must agree -- this is the six-instance class itself.

        Every equity text field reaches the model as ``_safe_str(...) or
        PLACEHOLDER``. ``EquityFacts`` bounds those fields with ``min_length=1``
        under ``str_strip_whitespace=True``. If any input can slip through the
        guard and still fail the bound, the composer raises mid-pack and the
        holding degrades to the schema fallback -- which is exactly how the
        earlier five instances behaved.

        This asserts the join, not either side alone, so it keeps holding if the
        coercion or the bound is changed independently.

        (Written after two earlier attempts asserted the model's stripping rule by
        reimplementing it with ``str.strip()``. They disagree: Python treats
        ``\x1c``-``\x1f`` as whitespace, pydantic-core's ``trim`` uses the Unicode
        ``White_Space`` property and does not. Predicting the rule was the bug in
        the test; asserting the contract does not need to.)
        """
        text = _safe_str(value, 2000) or PLACEHOLDER

        facts = EquityFacts(business_summary=text, leadership=text)

        assert facts.kind == "equity"
        assert facts.business_summary
