from pathlib import Path

from io_loaders import load_tiers
from normalize import normalize_tier

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_load_tiers():
    tiers, errors = load_tiers(FIXTURES / "tiers.csv")
    assert errors == []
    assert sorted(tiers) == ["proj_fin_a", "proj_fin_b", "proj_fin_c"]
    assert normalize_tier(tiers["proj_fin_a"]) == {
        "tier": "tier_1", "rpm_limit": 2, "tpm_limit": 40000,
    }