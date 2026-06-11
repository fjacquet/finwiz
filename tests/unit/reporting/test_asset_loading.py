"""CSS/JS asset files load correctly through the legacy function APIs."""

from finwiz.reporting.css.css_elements import (
    get_action_styles,
    get_base_styles,
    get_cost_styles,
    get_risk_styles,
    get_table_styles,
    get_trade_styles,
)
from finwiz.reporting.css.css_layouts import (
    get_execution_styles,
    get_interactive_styles,
    get_responsive_styles,
    get_scenario_styles,
)
from finwiz.reporting.css_styles import get_report_css
from finwiz.reporting.js.javascript_code import get_rebalancing_javascript


class TestReportCssAsset:
    def test_returns_nonempty_css(self):
        css = get_report_css()
        assert len(css) > 5000  # the stylesheet is ~330 lines
        assert ":root" in css  # design-token variables block
        assert "@media" in css  # responsive queries preserved

    def test_is_cached_across_calls(self):
        assert get_report_css() is get_report_css()  # functools.cache — no re-read per report


class TestCssElementsAssets:
    def test_base_styles_nonempty(self):
        css = get_base_styles()
        assert len(css) > 100
        assert "executive-summary" in css  # distinctive class from base styles

    def test_base_styles_cached(self):
        assert get_base_styles() is get_base_styles()

    def test_table_styles_nonempty(self):
        css = get_table_styles()
        assert len(css) > 100
        assert "portfolio-table" in css  # distinctive class from table styles

    def test_table_styles_cached(self):
        assert get_table_styles() is get_table_styles()

    def test_action_styles_nonempty(self):
        css = get_action_styles()
        assert len(css) > 100
        assert "action-buy" in css  # distinctive class from action styles

    def test_action_styles_cached(self):
        assert get_action_styles() is get_action_styles()

    def test_trade_styles_nonempty(self):
        css = get_trade_styles()
        assert len(css) > 100
        assert "trade-rationale" in css  # distinctive class from trade styles

    def test_trade_styles_cached(self):
        assert get_trade_styles() is get_trade_styles()

    def test_risk_styles_nonempty(self):
        css = get_risk_styles()
        assert len(css) > 100
        assert "risk-scores" in css  # distinctive class from risk styles

    def test_risk_styles_cached(self):
        assert get_risk_styles() is get_risk_styles()

    def test_cost_styles_nonempty(self):
        css = get_cost_styles()
        assert len(css) > 100
        assert "cost-breakdown" in css  # distinctive class from cost styles

    def test_cost_styles_cached(self):
        assert get_cost_styles() is get_cost_styles()


class TestCssLayoutsAssets:
    def test_scenario_styles_nonempty(self):
        css = get_scenario_styles()
        assert len(css) > 100
        assert "scenario-card" in css  # distinctive class from scenario styles

    def test_scenario_styles_cached(self):
        assert get_scenario_styles() is get_scenario_styles()

    def test_execution_styles_nonempty(self):
        css = get_execution_styles()
        assert len(css) > 100
        assert "execution-stats" in css  # distinctive class from execution styles

    def test_execution_styles_cached(self):
        assert get_execution_styles() is get_execution_styles()

    def test_interactive_styles_nonempty(self):
        css = get_interactive_styles()
        assert len(css) > 100
        assert "execute-btn" in css  # distinctive class from interactive styles

    def test_interactive_styles_cached(self):
        assert get_interactive_styles() is get_interactive_styles()

    def test_responsive_styles_nonempty(self):
        css = get_responsive_styles()
        assert len(css) > 100
        assert "@media" in css  # responsive queries in layout styles

    def test_responsive_styles_cached(self):
        assert get_responsive_styles() is get_responsive_styles()


class TestJavascriptAsset:
    def test_returns_nonempty_js(self):
        js = get_rebalancing_javascript()
        assert len(js) > 500
        assert "executeTradeDialog" in js  # distinctive function from JS

    def test_js_cached(self):
        assert get_rebalancing_javascript() is get_rebalancing_javascript()
