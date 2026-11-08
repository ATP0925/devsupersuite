"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_cap_table_safe_model.py
Target: cap_table_safe_model_engine.py (Startup Cap Table, SAFE Note Modeling & Venture Dilution Waterfall Engine)
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Treasury & Corporate Finance Only (cfo@devsupersuite.com).
"""

import os
import sys
import json
import subprocess
import pytest

# Add services directory to sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
sys.path.insert(0, SERVICES_DIR)

from cap_table_safe_model_engine import (
    CapTableSafeModelEngine,
    INITIAL_FOUNDER_COMMON_SHARES,
    INITIAL_ESOP_OPTION_SHARES,
    INITIAL_TOTAL_SHARES,
    DEFAULT_SAFE_TRANCHES,
    DEFAULT_SERIES_A_PRE_MONEY,
    DEFAULT_SERIES_A_NEW_INVESTMENT,
    DEFAULT_TARGET_POST_ESOP_PCT,
    CAP_TABLE_LEDGER_FILE,
    DEFAULT_CAP_REPORT_FILE
)

@pytest.fixture
def cap_engine(tmp_path):
    """Initializes Cap Table SAFE Engine with isolated temporary ledger."""
    test_ledger = os.path.join(tmp_path, "test_cap_table_model.json")
    return CapTableSafeModelEngine(ledger_path=test_ledger)

def test_01_baseline_cap_table_initialization(cap_engine):
    """Verifies baseline capitalization: 8,750,000 Founder Common (87.5%) + 1,250,000 ESOP (12.5%)."""
    base = cap_engine.get_baseline_cap_table()

    assert base["total_authorized_shares"] == INITIAL_TOTAL_SHARES
    assert len(base["shareholders"]) == 2

    founder_row = base["shareholders"][0]
    assert founder_row["holder"] == "Founding Operating Partners"
    assert founder_row["shares"] == INITIAL_FOUNDER_COMMON_SHARES
    assert founder_row["ownership_pct"] == 87.50

    esop_row = base["shareholders"][1]
    assert esop_row["holder"] == "Unallocated Employee Stock Option Plan"
    assert esop_row["shares"] == INITIAL_ESOP_OPTION_SHARES
    assert esop_row["ownership_pct"] == 12.50

def test_02_post_money_safe_tranches_modeling(cap_engine):
    """Verifies Y Combinator standard Post-Money SAFE modeling across $10M, $15M, and $25M valuation caps."""
    safe = cap_engine.model_safe_round()

    assert safe["total_safe_capital_raised_usd"] == 5000000.00
    assert safe["cumulative_safe_ownership_pct"] == 30.00
    assert safe["retained_common_and_esop_pct"] == 70.00
    assert len(safe["tranches"]) == 3

    # Tranche 1: $1.0M on $10.0M cap = 10.00%
    tr1 = safe["tranches"][0]
    assert tr1["tranche_id"] == "SAFE-TR-01"
    assert tr1["investment_amount_usd"] == 1000000.0
    assert tr1["post_money_cap_usd"] == 10000000.0
    assert tr1["target_ownership_pct"] == 10.00
    assert tr1["effective_price_per_share"] == 1.0000

    # Tranche 2: $1.5M on $15.0M cap = 10.00%
    tr2 = safe["tranches"][1]
    assert tr2["target_ownership_pct"] == 10.00
    assert tr2["effective_price_per_share"] == 1.5000

    # Tranche 3: $2.5M on $25.0M cap = 10.00%
    tr3 = safe["tranches"][2]
    assert tr3["target_ownership_pct"] == 10.00
    assert tr3["effective_price_per_share"] == 2.5000

def test_03_safe_conversion_price_mechanics(cap_engine):
    """Verifies that each SAFE converts at the lower of its valuation cap price vs discount price."""
    priced = cap_engine.simulate_priced_round(
        pre_money_valuation=DEFAULT_SERIES_A_PRE_MONEY,
        new_investment_usd=DEFAULT_SERIES_A_NEW_INVESTMENT
    )

    conversions = priced["safe_conversions"]
    assert len(conversions) == 3

    for sc in conversions:
        # For a $40M pre-money round, all valuation caps ($10M, $15M, $25M) produce lower prices than discount
        assert sc["effective_conversion_pps"] == min(sc["cap_price_per_share"], sc["discount_price_per_share"])
        assert sc["winning_mechanism"] == "VALUATION_CAP"
        assert sc["shares_issued"] == 1000000  # $1M / $1.00 = 1M, $1.5M / $1.50 = 1M, $2.5M / $2.50 = 1M

def test_04_priced_round_dilution_waterfall(cap_engine):
    """Verifies Series A priced round dilution waterfall: $40M pre-money + $10M new = $50M post-money."""
    priced = cap_engine.simulate_priced_round()

    assert priced["pre_money_valuation_usd"] == 40000000.00
    assert priced["new_capital_raised_usd"] == 10000000.00
    assert priced["post_money_valuation_usd"] == 50000000.00

    # Verify total post-round ownership sums to exactly 100.00%
    total_pct = sum(r["ownership_pct"] for r in priced["cap_table"])
    assert total_pct == pytest.approx(100.00, abs=0.01)

    # Verify Founders maintain majority voting control (>50%)
    founder_row = priced["cap_table"][0]
    assert founder_row["ownership_pct"] >= 50.00
    assert founder_row["equity_value_usd"] > 25000000.00

    # Verify Lead Series A Investor
    lead_row = priced["cap_table"][-1]
    assert "Lead Series A" in lead_row["holder"]
    assert lead_row["ownership_pct"] > 15.00
    assert lead_row["invested_capital_usd"] == 10000000.00

def test_05_investor_returns_and_moic(cap_engine):
    """Verifies Multiple on Invested Capital (MOIC) and paper gains for early SAFE investors."""
    priced = cap_engine.simulate_priced_round()

    cap_table = {r["holder"]: r for r in priced["cap_table"]}

    # SAFE 1: $1.0M invested at $10M cap -> $3.0M equity value (3.00x MOIC)
    safe1 = cap_table["Angel Syndicate & Early Technologists"]
    assert safe1["moic"] == 3.00
    assert safe1["equity_value_usd"] == 3000000.00

    # SAFE 2: $1.5M invested at $15M cap -> $3.0M equity value (2.00x MOIC)
    safe2 = cap_table["Developer Tooling Seed Venture Partners"]
    assert safe2["moic"] == 2.00
    assert safe2["equity_value_usd"] == 3000000.00

    # SAFE 3: $2.5M invested at $25M cap -> $3.0M equity value (1.20x MOIC)
    safe3 = cap_table["AI Infrastructure & Enterprise Growth Fund"]
    assert safe3["moic"] == 1.20
    assert safe3["equity_value_usd"] == 3000000.00

def test_06_esop_option_pool_dilution_and_top_up(cap_engine):
    """Verifies unallocated ESOP option pool is topped up to exactly target 10.00% post-round."""
    priced = cap_engine.simulate_priced_round(target_post_esop_pct=10.0)

    esop_row = next(r for r in priced["cap_table"] if "ESOP" in r["holder"])
    assert esop_row["ownership_pct"] == 10.00
    assert esop_row["equity_value_usd"] == 5000007.00
    assert priced["esop_top_up_shares"] > 0

def test_07_cap_table_markdown_generation_and_brand_anonymity(cap_engine, tmp_path):
    """Generates cap table markdown report and asserts strict 100% Brand Anonymity."""
    test_rep = os.path.join(tmp_path, "test_cap_report.md")
    test_led = os.path.join(tmp_path, "test_ledger.json")

    saved = cap_engine.save_report_and_ledger(report_path=test_rep, ledger_path=test_led)
    assert os.path.exists(saved["report_path"])
    assert os.path.exists(saved["ledger_path"])

    with open(saved["report_path"], "r", encoding="utf-8") as f:
        content = f.read()

    # Brand authority checks
    assert "DevSuperSuite Treasury & Corporate Finance" in content
    assert "cfo@devsupersuite.com" in content
    assert "$50,000,000.00 USD" in content
    assert "Founding Operating Partners" in content

    # Zero PII Leaks: forbidden personal founder tokens
    forbidden = ["Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"]
    for word in forbidden:
        assert word not in content, f"Brand Anonymity violation: found '{word}' in cap table report."

def test_08_cli_execution():
    """Verifies CLI execution with --model-safe-round, --audit-cap-table, and --summary flags."""
    script_path = os.path.join(SERVICES_DIR, "cap_table_safe_model_engine.py")

    cmd = [
        sys.executable, script_path,
        "--model-safe-round",
        "--audit-cap-table",
        "--simulate-priced-round",
        "--summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "Cap Table & Dilution Report" in res.stdout
    assert "Persistence Cap Table Ledger" in res.stdout
    assert "Founder Common Equity:            8,750,000 Shares (87.50%)" in res.stdout
    assert "Total SAFE Capital Raised:        $5,000,000.00 USD" in res.stdout
    assert "Series A Post-Money Valuation:    $50,000,000.00 USD" in res.stdout
