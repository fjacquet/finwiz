"""The crypto branch passes gaps through instead of inventing values."""

import inspect

from finwiz.scoring import portfolio_deep_analyzer


def test_crypto_branch_has_no_fabricated_defaults():
    source = inspect.getsource(portfolio_deep_analyzer)
    crypto_branch = source.split('elif asset_class == "crypto":', 1)[1].split("# Log asset-specific data", 1)[0]

    for fabricated in ("100e9", "1e9", '"age_years": perf_dict.get("age_years", 5)'):
        assert fabricated not in crypto_branch, f"{fabricated} is a fabricated default"


def test_crypto_branch_reads_every_field_without_a_default():
    source = inspect.getsource(portfolio_deep_analyzer)
    crypto_branch = source.split('elif asset_class == "crypto":', 1)[1].split("# Log asset-specific data", 1)[0]

    for field in ("market_cap", "volume_24h", "age_years"):
        assert f'perf_dict.get("{field}")' in crypto_branch
