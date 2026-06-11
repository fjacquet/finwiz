"""Shared Jinja2 environment factory used by all report generators."""

from finwiz.reporting.base_report_generator import create_report_jinja_env


class TestCreateReportJinjaEnv:
    def test_env_is_configured_for_reports(self, tmp_path):
        env = create_report_jinja_env(tmp_path)
        assert env.autoescape  # security: HTML auto-escaping stays on
        assert env.trim_blocks and env.lstrip_blocks
