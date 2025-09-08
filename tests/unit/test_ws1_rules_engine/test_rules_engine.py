"""
Tests for Rules Engine

This module contains comprehensive tests for the Rules Engine
to ensure proper rule validation and enforcement.
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, time
from unittest.mock import Mock, patch

from src.ws1_rules_engine.rules_engine import RulesEngine, RuleExecutionResult
from src.ws1_rules_engine.audit import AuditTrailManager


class TestRulesEngine:
    """Test Rules Engine implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.audit_manager = AuditTrailManager()
        self.rules_engine = RulesEngine(audit_manager=self.audit_manager)
    
    def test_rules_engine_initialization(self):
        """Test Rules Engine initialization."""
        assert self.rules_engine.constitution.VERSION == "1.3"
        assert self.rules_engine.audit_manager is not None
        assert self.rules_engine.compliance_checker is not None
    
    def test_validate_position_entry_gen_acc_valid(self):
        """Test valid Gen-Acc position entry."""
        result = self.rules_engine.validate_position_entry(
            account_type="gen_acc",
            symbol="SPY",
            strategy="csp",
            quantity=10,
            strike_price=Decimal("450.00"),
            expiry_date=date(2024, 12, 20),
            delta=Decimal("0.42"),
            premium=Decimal("2.50")
        )
        
        assert result["approved"] is True
        assert result["result"] in [RuleExecutionResult.APPROVED.value, RuleExecutionResult.WARNING.value]
        assert len(result.get("violations", [])) == 0
    
    def test_validate_position_entry_gen_acc_invalid_symbol(self):
        """Test Gen-Acc position entry with invalid symbol."""
        result = self.rules_engine.validate_position_entry(
            account_type="gen_acc",
            symbol="AAPL",  # Not permitted for Gen-Acc
            strategy="csp",
            quantity=10,
            strike_price=Decimal("180.00"),
            delta=Decimal("0.42")
        )
        
        assert result["approved"] is False
        assert result["result"] == RuleExecutionResult.REJECTED.value
        assert len(result.get("violations", [])) > 0
    
    def test_validate_position_entry_gen_acc_invalid_delta(self):
        """Test Gen-Acc position entry with invalid delta."""
        result = self.rules_engine.validate_position_entry(
            account_type="gen_acc",
            symbol="SPY",
            strategy="csp",
            quantity=10,
            strike_price=Decimal("450.00"),
            delta=Decimal("0.60")  # Outside Gen-Acc range
        )
        
        assert result["approved"] is False
        assert result["result"] == RuleExecutionResult.REJECTED.value
        violations = result.get("violations", [])
        assert any("delta" in v.lower() for v in violations)
    
    def test_validate_position_entry_rev_acc_valid(self):
        """Test valid Rev-Acc position entry."""
        result = self.rules_engine.validate_position_entry(
            account_type="rev_acc",
            symbol="NVDA",
            strategy="csp",
            quantity=5,
            strike_price=Decimal("800.00"),
            delta=Decimal("0.43")
        )
        
        assert result["approved"] is True
        assert result["result"] in [RuleExecutionResult.APPROVED.value, RuleExecutionResult.WARNING.value]
    
    def test_validate_position_entry_rev_acc_invalid_symbol(self):
        """Test Rev-Acc position entry with invalid symbol."""
        result = self.rules_engine.validate_position_entry(
            account_type="rev_acc",
            symbol="SPY",  # Not permitted for Rev-Acc
            strategy="csp",
            quantity=5,
            delta=Decimal("0.43")
        )
        
        assert result["approved"] is False
        violations = result.get("violations", [])
        assert any("not permitted" in v.lower() for v in violations)
    
    def test_validate_position_entry_com_acc_valid(self):
        """Test valid Com-Acc position entry."""
        result = self.rules_engine.validate_position_entry(
            account_type="com_acc",
            symbol="AAPL",
            strategy="cc",
            quantity=10,
            strike_price=Decimal("190.00"),
            delta=Decimal("0.20")
        )
        
        assert result["approved"] is True
        assert result["result"] in [RuleExecutionResult.APPROVED.value, RuleExecutionResult.WARNING.value]
    
    def test_validate_position_entry_com_acc_invalid_strategy(self):
        """Test Com-Acc position entry with invalid strategy."""
        result = self.rules_engine.validate_position_entry(
            account_type="com_acc",
            symbol="AAPL",
            strategy="csp",  # Com-Acc only supports CC
            quantity=10,
            delta=Decimal("0.20")
        )
        
        assert result["approved"] is False
        violations = result.get("violations", [])
        assert any("covered calls" in v.lower() for v in violations)
    
    def test_validate_position_exit(self):
        """Test position exit validation."""
        result = self.rules_engine.validate_position_exit(
            position_id="pos_123",
            account_type="gen_acc",
            exit_reason="protocol_level_2",
            current_price=Decimal("445.00"),
            pnl=Decimal("-500.00")
        )
        
        assert "result" in result
        assert "approved" in result
        assert "timestamp" in result
    
    def test_validate_roll_decision(self):
        """Test roll decision validation."""
        result = self.rules_engine.validate_roll_decision(
            position_id="pos_123",
            account_type="gen_acc",
            current_strike=Decimal("450.00"),
            new_strike=Decimal("445.00"),
            current_expiry=date(2024, 12, 20),
            new_expiry=date(2025, 1, 17),
            atr_breach_multiple=Decimal("2.5")
        )
        
        assert "result" in result
        assert "approved" in result
        assert result["rule_section"] == "§6.Protocol-Engine.Roll"
    
    def test_validate_account_fork(self):
        """Test account fork validation."""
        result = self.rules_engine.validate_account_fork(
            parent_account_id="acc_123",
            account_type="gen_acc",
            current_balance=Decimal("150000"),
            fork_threshold=Decimal("100000")
        )
        
        assert "result" in result
        assert "approved" in result
        # Should be approved since balance > threshold
        assert result["approved"] is True
    
    def test_validate_hedge_deployment(self):
        """Test hedge deployment validation."""
        result = self.rules_engine.validate_hedge_deployment(
            vix_level=Decimal("55.0"),
            hedge_budget=Decimal("10000"),
            hedge_strategy="spx_puts"
        )
        
        assert "result" in result
        assert "approved" in result
        assert result["rule_section"] == "§5.Hedging"
    
    def test_check_system_state_transition(self):
        """Test system state transition validation."""
        result = self.rules_engine.check_system_state_transition(
            current_state="ACTIVE",
            target_state="SAFE",
            trigger_reason="vix_level_65"
        )
        
        assert "result" in result
        assert "approved" in result
        assert result["rule_section"] == "§9.State-Machine"
    
    def test_get_position_sizing_recommendation(self):
        """Test position sizing recommendation."""
        result = self.rules_engine.get_position_sizing_recommendation(
            account_type="gen_acc",
            available_capital=Decimal("50000"),
            symbol="SPY",
            option_price=Decimal("2.50")
        )
        
        assert "recommended_contracts" in result
        assert "deployment_range" in result
        assert "per_symbol_limit" in result
        assert result["recommended_contracts"] >= 0
    
    def test_get_position_sizing_recommendation_high_capital(self):
        """Test position sizing with high capital."""
        result = self.rules_engine.get_position_sizing_recommendation(
            account_type="gen_acc",
            available_capital=Decimal("1000000"),
            symbol="SPY",
            option_price=Decimal("2.50")
        )
        
        # Should respect per-symbol exposure limit (25%)
        max_per_symbol = float(Decimal("1000000") * Decimal("0.25"))
        contract_value = float(Decimal("2.50") * 100)
        expected_max_contracts = int(max_per_symbol / contract_value)
        
        assert result["recommended_contracts"] <= expected_max_contracts
    
    def test_get_constitution_summary(self):
        """Test Constitution summary retrieval."""
        summary = self.rules_engine.get_constitution_summary()
        
        assert summary["version"] == "1.3"
        assert "account_split_ratios" in summary
        assert "weekly_schedule" in summary
        assert "fork_thresholds" in summary
        assert "protocol_engine_rules" in summary
        assert "hedging_rules" in summary
        assert "llms_rules" in summary
    
    def test_audit_trail_logging(self):
        """Test audit trail logging."""
        # Perform a validation that should be logged
        self.rules_engine.validate_position_entry(
            account_type="gen_acc",
            symbol="SPY",
            strategy="csp",
            quantity=10,
            delta=Decimal("0.42")
        )
        
        # Check audit trail
        audit_records = self.rules_engine.get_audit_trail(limit=1)
        assert len(audit_records) > 0
        
        latest_record = audit_records[0]
        assert "audit_id" in latest_record
        assert "rule_section" in latest_record
        assert "constitution_version" in latest_record
        assert latest_record["constitution_version"] == "1.3"
    
    def test_error_handling(self):
        """Test error handling in validation."""
        # Test with invalid account type
        result = self.rules_engine.validate_position_entry(
            account_type="invalid_account",
            symbol="SPY",
            strategy="csp",
            quantity=10,
            delta=Decimal("0.42")
        )
        
        assert result["approved"] is False
        violations = result.get("violations", [])
        assert any("unknown account type" in v.lower() for v in violations)
    
    def test_validate_trading_decision_comprehensive(self):
        """Test comprehensive trading decision validation."""
        decision_context = {
            "account_type": "gen_acc",
            "action": "open",
            "strategy": "csp",
            "symbol": "SPY",
            "quantity": 10,
            "strike_price": 450.00,
            "delta": 0.42,
            "dte": 30,
            "premium": 2.50,
            "trading_time": "2024-01-15T10:30:00",
            "available_capital": 50000,
            "position_value": 2500,
            "open_interest": 5000,
            "daily_volume": 1000,
            "bid_price": 2.45,
            "ask_price": 2.55,
            "mid_price": 2.50
        }
        
        result = self.rules_engine.validate_trading_decision(decision_context)
        
        assert "result" in result
        assert "approved" in result
        assert "validator_results" in result
        assert "timestamp" in result
        
        # Check that all validators ran
        validator_results = result["validator_results"]
        expected_validators = ["account_type", "position_sizing", "timing", "delta_range", "liquidity"]
        for validator in expected_validators:
            assert validator in validator_results
    
    @patch('src.ws1_rules_engine.rules_engine.logger')
    def test_logging(self, mock_logger):
        """Test logging functionality."""
        self.rules_engine.validate_position_entry(
            account_type="gen_acc",
            symbol="SPY",
            strategy="csp",
            quantity=10,
            delta=Decimal("0.42")
        )
        
        # Verify logging was called
        assert mock_logger.info.called

