"""
Tests for Constitution v1.3

This module contains comprehensive tests for the Constitution v1.3
implementation to ensure all rules are correctly encoded and enforced.
"""

import pytest
from decimal import Decimal
from datetime import time, date

from src.ws1_rules_engine.constitution import ConstitutionV13


class TestConstitutionV13:
    """Test Constitution v1.3 implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.constitution = ConstitutionV13()
    
    def test_constitution_version(self):
        """Test Constitution version."""
        assert self.constitution.VERSION == "1.3"
    
    def test_global_parameters(self):
        """Test global parameters."""
        params = self.constitution.global_params
        
        # Test capital deployment ranges
        assert params.MIN_CAPITAL_DEPLOYMENT == Decimal("0.95")
        assert params.MAX_CAPITAL_DEPLOYMENT == Decimal("1.00")
        
        # Test per-symbol exposure
        assert params.MAX_PER_SYMBOL_EXPOSURE == Decimal("0.25")
        
        # Test margin usage
        assert params.MAX_MARGIN_USE == Decimal("0.50")
        
        # Test order slicing
        assert params.ORDER_SLICE_THRESHOLD == 50
    
    def test_account_split_ratios(self):
        """Test account split ratios."""
        ratios = self.constitution.get_account_split_ratios()
        
        assert ratios["gen_acc"] == Decimal("0.50")
        assert ratios["rev_acc"] == Decimal("0.30")
        assert ratios["com_acc"] == Decimal("0.20")
        
        # Test ratios sum to 1.0
        total = sum(ratios.values())
        assert total == Decimal("1.00")
    
    def test_weekly_schedule(self):
        """Test weekly trading schedule."""
        schedule = self.constitution.get_weekly_schedule()
        
        # Test Gen-Acc schedule
        gen_schedule = schedule["gen_acc"]
        assert gen_schedule["day"] == "monday"
        assert gen_schedule["start_time"] == time(9, 30)
        assert gen_schedule["end_time"] == time(16, 0)
        
        # Test Rev-Acc schedule
        rev_schedule = schedule["rev_acc"]
        assert rev_schedule["day"] == "wednesday"
        assert rev_schedule["start_time"] == time(9, 30)
        assert rev_schedule["end_time"] == time(16, 0)
        
        # Test Com-Acc schedule
        com_schedule = schedule["com_acc"]
        assert com_schedule["day"] == "friday"
        assert com_schedule["start_time"] == time(9, 30)
        assert com_schedule["end_time"] == time(16, 0)
    
    def test_gen_acc_rules(self):
        """Test Gen-Acc specific rules."""
        rules = self.constitution.gen_acc_rules
        
        # Test instruments
        expected_instruments = ["SPY", "QQQ", "IWM", "DIA"]
        assert rules.PERMITTED_INSTRUMENTS == expected_instruments
        
        # Test delta ranges
        assert rules.DELTA_MIN == Decimal("0.40")
        assert rules.DELTA_MAX == Decimal("0.45")
        
        # Test DTE ranges
        assert rules.DTE_NORMAL == (21, 45)
        assert rules.DTE_STRESS_TEST == (7, 21)
        
        # Test fork threshold
        assert rules.FORK_THRESHOLD == Decimal("100000")
    
    def test_rev_acc_rules(self):
        """Test Rev-Acc specific rules."""
        rules = self.constitution.rev_acc_rules
        
        # Test instruments (NVDA/TSLA only)
        expected_instruments = ["NVDA", "TSLA"]
        assert rules.PERMITTED_INSTRUMENTS == expected_instruments
        
        # Test delta ranges
        assert rules.DELTA_MIN == Decimal("0.40")
        assert rules.DELTA_MAX == Decimal("0.45")
        
        # Test DTE range
        assert rules.DTE_MIN == 21
        assert rules.DTE_MAX == 45
        
        # Test fork threshold
        assert rules.FORK_THRESHOLD == Decimal("100000")
    
    def test_com_acc_rules(self):
        """Test Com-Acc specific rules."""
        rules = self.constitution.com_acc_rules
        
        # Test instruments (Mag-7)
        expected_instruments = ["AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "TSLA", "META"]
        assert rules.PERMITTED_INSTRUMENTS == expected_instruments
        
        # Test delta ranges
        assert rules.DELTA_MIN == Decimal("0.15")
        assert rules.DELTA_MAX == Decimal("0.25")
        
        # Test DTE (exactly 5)
        assert rules.DTE == 5
        
        # Test earnings coverage
        assert rules.EARNINGS_COVERAGE_MAX == Decimal("0.50")
        
        # Test profit taking
        assert rules.PROFIT_TAKE_THRESHOLD == Decimal("0.50")
    
    def test_protocol_engine_rules(self):
        """Test Protocol Engine rules."""
        rules = self.constitution.get_protocol_engine_rules()
        
        # Test ATR triggers
        assert rules["atr_triggers"]["level_1"] == 1.0
        assert rules["atr_triggers"]["level_2"] == 2.0
        assert rules["atr_triggers"]["level_3"] == 3.0
        
        # Test monitoring frequencies
        frequencies = rules["monitoring_frequencies"]
        assert frequencies["level_0"] == 300  # 5 minutes
        assert frequencies["level_1"] == 60   # 1 minute
        assert frequencies["level_2"] == 30   # 30 seconds
        assert frequencies["level_3"] == 1    # Real-time
    
    def test_hedging_rules(self):
        """Test hedging rules."""
        rules = self.constitution.get_hedging_rules()
        
        # Test hedge budget
        assert rules["hedge_budget"]["min_pct"] == 0.05
        assert rules["hedge_budget"]["max_pct"] == 0.10
        
        # Test VIX triggers
        vix_triggers = rules["vix_triggers"]
        assert vix_triggers["hedged_week"] == 50.0
        assert vix_triggers["safe_mode"] == 65.0
        assert vix_triggers["kill_switch"] == 80.0
        
        # Test instruments
        assert rules["instruments"]["primary"] == "SPX"
        assert rules["instruments"]["secondary"] == "VIX"
    
    def test_llms_rules(self):
        """Test LLMS rules."""
        rules = self.constitution.get_llms_rules()
        
        # Test duration ranges
        duration = rules["duration_ranges"]
        assert duration["growth_months"] == (12, 18)
        assert duration["hedge_months"] == (6, 12)
        
        # Test allocation
        allocation = rules["allocation"]
        assert allocation["reinvestment_pct"] == 0.25
        assert allocation["growth_hedge_split"]["growth"] == 0.70
        assert allocation["growth_hedge_split"]["hedge"] == 0.30
        
        # Test delta ranges
        delta_ranges = rules["delta_ranges"]
        assert delta_ranges["growth"] == (0.60, 0.80)
        assert delta_ranges["hedge"] == (0.20, 0.40)
    
    def test_fork_thresholds(self):
        """Test fork thresholds."""
        thresholds = self.constitution.get_fork_thresholds()
        
        assert thresholds["gen_acc"] == Decimal("100000")
        assert thresholds["rev_acc"] == Decimal("100000")
        # Com-Acc doesn't fork
        assert "com_acc" not in thresholds
    
    def test_delta_ranges(self):
        """Test delta range retrieval."""
        # Test Gen-Acc CSP
        delta_min, delta_max = self.constitution.get_delta_ranges("gen_acc", "csp")
        assert delta_min == Decimal("0.40")
        assert delta_max == Decimal("0.45")
        
        # Test Com-Acc CC
        delta_min, delta_max = self.constitution.get_delta_ranges("com_acc", "cc")
        assert delta_min == Decimal("0.15")
        assert delta_max == Decimal("0.25")
        
        # Test invalid combination
        with pytest.raises(ValueError):
            self.constitution.get_delta_ranges("gen_acc", "invalid_strategy")
    
    def test_dte_ranges(self):
        """Test DTE range retrieval."""
        # Test Gen-Acc
        ranges = self.constitution.get_dte_ranges("gen_acc")
        assert ranges["normal"] == (21, 45)
        assert ranges["stress_test"] == (7, 21)
        
        # Test Com-Acc
        ranges = self.constitution.get_dte_ranges("com_acc")
        assert ranges["normal"] == (5, 5)  # Exactly 5 DTE
        
        # Test invalid account type
        with pytest.raises(ValueError):
            self.constitution.get_dte_ranges("invalid_account")
    
    def test_liquidity_requirements(self):
        """Test liquidity requirements."""
        requirements = self.constitution.get_liquidity_requirements()
        
        assert requirements["min_open_interest"] == 1000
        assert requirements["min_daily_volume"] == 500
        assert requirements["max_spread_pct"] == 0.05
        assert requirements["max_order_size_pct"] == 0.10
    
    def test_circuit_breaker_levels(self):
        """Test circuit breaker levels."""
        levels = self.constitution.get_circuit_breaker_levels()
        
        assert levels["vix_hedged_week"] == 50.0
        assert levels["vix_safe_mode"] == 65.0
        assert levels["vix_kill_switch"] == 80.0
        assert levels["max_daily_loss_pct"] == 0.05
        assert levels["max_position_loss_pct"] == 0.05
    
    def test_rule_compliance_validation(self):
        """Test rule compliance validation."""
        # Test valid context
        valid_context = {
            "account_type": "gen_acc",
            "strategy": "csp",
            "delta": 0.42,
            "dte": 30
        }
        
        result = self.constitution.validate_rule_compliance("§2.Gen-Acc", valid_context)
        assert result["valid"] is True
        assert len(result["violations"]) == 0
        
        # Test invalid context
        invalid_context = {
            "account_type": "gen_acc",
            "strategy": "csp",
            "delta": 0.60,  # Outside range
            "dte": 30
        }
        
        result = self.constitution.validate_rule_compliance("§2.Gen-Acc", invalid_context)
        assert result["valid"] is False
        assert len(result["violations"]) > 0
    
    def test_position_sizing_rules(self):
        """Test position sizing rules."""
        rules = self.constitution.get_position_sizing_rules("gen_acc")
        
        assert "capital_deployment" in rules
        assert "per_symbol_exposure" in rules
        assert "margin_usage" in rules
        
        # Test that all account types have sizing rules
        for account_type in ["gen_acc", "rev_acc", "com_acc"]:
            rules = self.constitution.get_position_sizing_rules(account_type)
            assert rules is not None
    
    def test_changelog(self):
        """Test Constitution changelog."""
        changelog = self.constitution.changelog
        
        assert len(changelog) > 0
        assert "1.3" in [entry["version"] for entry in changelog]
        
        # Test latest version is 1.3
        latest = max(changelog, key=lambda x: x["version"])
        assert latest["version"] == "1.3"

