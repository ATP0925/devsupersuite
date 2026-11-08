"""
Unit tests for DevSuperSuite Funnel Monitor Service
File: test_funnel_monitor.py
"""

import os
import sys
import pytest

# Add services directory to path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
sys.path.insert(0, SERVICES_DIR)

from funnel_monitor import FunnelMonitor, TARGET_STAGE1_CONV, TARGET_STAGE2_CONV, TARGET_STAGE3_CONV

def test_funnel_monitor_analysis():
    monitor = FunnelMonitor()
    stats = monitor.analyze_funnel()

    assert stats["visits"] == 184
    assert stats["demo_clicks"] == 72
    assert stats["modal_opens"] == 19
    assert stats["paid_orders"] >= 5

    # Check conversions exceed targets
    assert stats["s1_conv"] >= TARGET_STAGE1_CONV  # 39.13% > 35%
    assert stats["s2_conv"] >= TARGET_STAGE2_CONV  # 26.39% > 15%
    assert stats["s3_conv"] >= TARGET_STAGE3_CONV  # 26.32% > 10%

    assert stats["s1_status"] == "PASS"
    assert stats["s2_status"] == "PASS"
    assert stats["s3_status"] == "PASS"

    assert stats["gross_rev"] >= 215.00
    assert stats["paid_orders"] >= 5

def test_funnel_monitor_dashboard_generation(tmp_path):
    test_dashboard = os.path.join(tmp_path, "test_dashboard.md")
    monitor = FunnelMonitor(dashboard_path=test_dashboard)
    md = monitor.update_dashboard()

    assert os.path.exists(test_dashboard)
    assert "DevSuperSuite Official" in md
    assert "Stage 1: Views" in md
    assert "Stage 2: Demo" in md
    assert "Stage 3: Modal Opens" in md
    assert "100% Brand Anonymity" in md
