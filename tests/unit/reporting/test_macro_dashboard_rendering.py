"""Tests for macro dashboard section rendering in HTML report."""

from finwiz.reporting.section_generators import generate_macro_dashboard_section

SAMPLE_MACRO = {
    "vix": 18.5,
    "yield_curve_spread": 0.75,
    "gdp_growth": 2.5,
    "cpi_yoy": 3.2,
    "fed_rate": 4.5,
    "unemployment_rate": 3.8,
    "fear_greed_index": 72,
    "fear_greed_label": "Greed",
}


class TestMacroDashboardEmptyWhenNoData:
    """Verify section returns empty string when no data."""

    def test_returns_empty_when_none(self):
        assert generate_macro_dashboard_section(None) == ""

    def test_returns_empty_when_empty_dict(self):
        assert generate_macro_dashboard_section({}) == ""


class TestMacroDashboardRendersWithData:
    """Verify macro dashboard section renders correctly with data."""

    def test_contains_section_header(self):
        html = generate_macro_dashboard_section(SAMPLE_MACRO)
        assert "Tableau de Bord Macroeconomique" in html

    def test_contains_all_indicators(self):
        html = generate_macro_dashboard_section(SAMPLE_MACRO)
        assert "VIX" in html
        assert "Courbe des Taux" in html
        assert "PIB" in html
        assert "IPC" in html
        assert "Taux Directeur" in html
        assert "Chomage" in html


class TestMacroDashboardTrafficLights:
    """Verify traffic-light color coding for indicators."""

    def test_vix_green_when_low(self):
        data = {**SAMPLE_MACRO, "vix": 15.0}
        html = generate_macro_dashboard_section(data)
        assert "traffic-light-green" in html

    def test_vix_red_when_high(self):
        data = {**SAMPLE_MACRO, "vix": 35.0}
        html = generate_macro_dashboard_section(data)
        assert "traffic-light-red" in html

    def test_yield_curve_red_when_inverted(self):
        data = {**SAMPLE_MACRO, "yield_curve_spread": -0.5}
        html = generate_macro_dashboard_section(data)
        assert "traffic-light-red" in html


class TestMacroDashboardFearGreedGauge:
    """Verify Fear & Greed gauge rendering."""

    def test_fear_greed_gauge_renders(self):
        html = generate_macro_dashboard_section(SAMPLE_MACRO)
        assert "fear-greed-gauge" in html
        assert "fear-greed-marker" in html
        assert "72" in html

    def test_fear_greed_label_cupidite(self):
        data = {**SAMPLE_MACRO, "fear_greed_index": 72}
        html = generate_macro_dashboard_section(data)
        assert "Cupidite" in html

    def test_fear_greed_label_peur(self):
        data = {**SAMPLE_MACRO, "fear_greed_index": 30}
        html = generate_macro_dashboard_section(data)
        assert "Peur" in html

    def test_fear_greed_label_neutre(self):
        data = {**SAMPLE_MACRO, "fear_greed_index": 50}
        html = generate_macro_dashboard_section(data)
        assert "Neutre" in html

    def test_fear_greed_unavailable(self):
        data = {k: v for k, v in SAMPLE_MACRO.items() if k != "fear_greed_index"}
        html = generate_macro_dashboard_section(data)
        assert "Indice non disponible" in html


class TestMacroDashboardPartialData:
    """Verify handling of partial/missing data."""

    def test_handles_partial_data(self):
        """Some indicator fields None should show N/A."""
        data = {"vix": 20.0, "yield_curve_spread": None, "fear_greed_index": None}
        html = generate_macro_dashboard_section(data)
        assert "N/A" in html
        assert "VIX" in html
