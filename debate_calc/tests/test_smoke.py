"""
Smoke tests and integration tests for the Debate Calculator.
Tests basic functionality and pacing verification.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from debate_calc.app.settings import settings, PacingProfile
from debate_calc.app.pace_controller import PaceController, SyncPaceController
from debate_calc.app.orchestrator import DebateOrchestrator
from debate_calc.app.telemetry import TelemetryLogger


class TestPacingController:
    """Test suite for pacing controller functionality."""
    
    @pytest.fixture
    def slow_profile(self):
        """Slow pacing profile for testing."""
        return PacingProfile(
            min_turn_seconds=0.5,  # Reduced for testing
            inter_turn_gap_seconds=0.2,
            typeout_rate_chars_per_sec=100,
            max_tokens_per_turn=350
        )
    
    @pytest.fixture
    def fast_profile(self):
        """Fast pacing profile for testing."""
        return PacingProfile(
            min_turn_seconds=0.1,
            inter_turn_gap_seconds=0.05,
            typeout_rate_chars_per_sec=200,
            max_tokens_per_turn=250
        )
    
    @pytest.mark.asyncio
    async def test_minimum_turn_duration(self, slow_profile):
        """Test that turns respect minimum duration."""
        controller = PaceController(slow_profile)
        
        # Mock a fast model call
        async def fast_model_call():
            await asyncio.sleep(0.1)  # Faster than minimum
            return "Quick response"
        
        start_time = time.time()
        response, timing = await controller.execute_turn(fast_model_call, "TestSpeaker")
        end_time = time.time()
        
        # Should take at least the minimum time (with some tolerance)
        assert end_time - start_time >= slow_profile.min_turn_seconds - 0.1
        assert timing.total_time >= slow_profile.min_turn_seconds - 0.1
        assert timing.padding_time > 0  # Should have added padding
    
    @pytest.mark.asyncio
    async def test_no_padding_for_slow_calls(self, slow_profile):
        """Test that slow model calls don't get extra padding."""
        controller = PaceController(slow_profile)
        
        # Mock a slow model call
        async def slow_model_call():
            await asyncio.sleep(slow_profile.min_turn_seconds + 0.2)
            return "Slow response"
        
        response, timing = await controller.execute_turn(slow_model_call, "TestSpeaker")
        
        # Should not add padding for already slow calls
        assert timing.padding_time < 0.1  # Minimal or no padding
    
    @pytest.mark.asyncio
    async def test_inter_turn_gap(self, slow_profile):
        """Test inter-turn gap timing."""
        controller = PaceController(slow_profile)
        
        start_time = time.time()
        await controller.inter_turn_gap()
        end_time = time.time()
        
        # Should take approximately the gap time (with jitter tolerance)
        gap_time = end_time - start_time
        expected_min = slow_profile.inter_turn_gap_seconds * 0.8  # Allow for jitter
        expected_max = slow_profile.inter_turn_gap_seconds * 1.2
        assert expected_min <= gap_time <= expected_max
    
    def test_sync_pace_controller(self, slow_profile):
        """Test synchronous pace controller for CLI."""
        controller = SyncPaceController(slow_profile)
        
        def fast_model_call():
            time.sleep(0.1)
            return "Quick response"
        
        start_time = time.time()
        response, timing = controller.execute_turn(fast_model_call, "TestSpeaker")
        end_time = time.time()
        
        # Should respect minimum timing
        assert end_time - start_time >= slow_profile.min_turn_seconds - 0.1
        assert timing.padding_time > 0
    
    @pytest.mark.asyncio
    async def test_typeout_delay_calculation(self, slow_profile):
        """Test typing effect delay calculation."""
        controller = PaceController(slow_profile)
        
        text = "Hello world"
        delay = controller.get_typeout_delay(len(text))
        expected_delay = len(text) / slow_profile.typeout_rate_chars_per_sec
        
        assert abs(delay - expected_delay) < 0.001
    
    def test_timing_summary(self, slow_profile):
        """Test timing summary generation."""
        controller = SyncPaceController(slow_profile)
        
        # Execute a few turns
        def model_call():
            time.sleep(0.1)
            return "Response"
        
        for _ in range(3):
            controller.execute_turn(model_call, "TestSpeaker")
        
        summary = controller.get_timing_summary()
        
        assert summary["total_turns"] == 3
        assert "total_model_time" in summary
        assert "total_padding_time" in summary
        assert "avg_model_latency" in summary
        assert "padding_percentage" in summary


class TestSettingsConfiguration:
    """Test configuration and settings management."""
    
    def test_pace_profile_retrieval(self):
        """Test retrieval of different pace profiles."""
        slow_profile = settings.get_pacing_profile("slow")
        medium_profile = settings.get_pacing_profile("medium")
        fast_profile = settings.get_pacing_profile("fast")
        
        # Slow should be slowest
        assert slow_profile.min_turn_seconds >= medium_profile.min_turn_seconds
        assert medium_profile.min_turn_seconds >= fast_profile.min_turn_seconds
        
        # Fast should have highest typing rate
        assert fast_profile.typeout_rate_chars_per_sec >= medium_profile.typeout_rate_chars_per_sec
        assert medium_profile.typeout_rate_chars_per_sec >= slow_profile.typeout_rate_chars_per_sec
    
    def test_model_configurations(self):
        """Test model configuration retrieval."""
        terrence_config = settings.get_terrence_config()
        neil_config = settings.get_neil_config()
        
        # Should have required fields
        assert terrence_config.api_key
        assert terrence_config.model
        assert terrence_config.temperature <= 0.2  # Terrence should be more deterministic
        
        assert neil_config.api_key
        assert neil_config.model
        assert neil_config.temperature <= 0.3  # Neil slightly more creative
    
    def test_invalid_pace_mode(self):
        """Test handling of invalid pace modes."""
        with pytest.raises(ValueError):
            settings.get_pacing_profile("invalid")


class TestTelemetryLogging:
    """Test telemetry and logging functionality."""
    
    @pytest.fixture
    def telemetry(self, tmp_path):
        """Create telemetry logger with temporary file."""
        log_file = tmp_path / "test_telemetry.jsonl"
        return TelemetryLogger(str(log_file))
    
    def test_debate_session_logging(self, telemetry):
        """Test complete debate session logging."""
        # Start debate
        telemetry.log_debate_start("2 + 3", "slow", 12)
        
        # Log some turns
        mock_turn = Mock()
        mock_turn.speaker = "Terrence"
        mock_turn.timestamp = time.time()
        mock_turn.tokens_used = 50
        mock_turn.agreement_flag = None
        mock_turn.timing = Mock()
        mock_turn.timing.model_latency = 1.5
        mock_turn.timing.padding_time = 0.5
        mock_turn.timing.total_time = 2.0
        mock_turn.timing.jitter_applied = 0.1
        
        telemetry.log_turn(mock_turn)
        
        # End debate
        mock_result = Mock()
        mock_result.status = Mock()
        mock_result.status.value = "completed"
        mock_result.final_answer = "5"
        mock_result.rounds = 1
        mock_result.total_time = 5.0
        mock_result.error_message = None
        
        telemetry.log_debate_end(mock_result)
        
        # Verify session summary
        summary = telemetry.get_session_summary()
        assert summary == {}  # Should be empty after debate end
    
    def test_error_logging(self, telemetry):
        """Test error logging functionality."""
        telemetry.log_error("test_error", "This is a test error")
        
        # Should not raise exceptions
        assert True
    
    def test_log_file_analysis(self, telemetry, tmp_path):
        """Test log file analysis functionality."""
        # Create a sample log file
        log_file = tmp_path / "sample.jsonl"
        sample_data = {
            "expression": "2 + 3",
            "pace_mode": "slow",
            "status": "completed",
            "rounds_completed": 2,
            "total_time": 10.5,
            "padding_percentage": 25.0
        }
        
        import json
        with open(log_file, "w") as f:
            f.write(json.dumps(sample_data) + "\n")
        
        stats = TelemetryLogger.analyze_log_file(str(log_file))
        
        assert stats["total_debates"] == 1
        assert stats["completed_debates"] == 1
        assert stats["completion_rate"] == 100.0
        assert "2 + 3" in stats["expressions_analyzed"]


class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test that orchestrator can be initialized."""
        with patch('debate_calc.app.orchestrator.openai.OpenAI'), \
             patch('debate_calc.app.orchestrator.anthropic.Anthropic'):
            orchestrator = DebateOrchestrator()
            assert orchestrator is not None
    
    @pytest.mark.asyncio
    async def test_mock_debate_flow(self):
        """Test complete debate flow with mocked responses."""
        with patch('debate_calc.app.orchestrator.openai.OpenAI'), \
             patch('debate_calc.app.orchestrator.anthropic.Anthropic'):
            
            orchestrator = DebateOrchestrator()
            
            with patch.object(orchestrator, '_call_terrence', new_callable=AsyncMock) as mock_terrence, \
                 patch.object(orchestrator, '_call_neil', new_callable=AsyncMock) as mock_neil:
                
                # Setup realistic mock responses
                mock_terrence.side_effect = [
                    "I calculate 1 + 1 = 2 using basic arithmetic",
                    "<FINAL>2</FINAL>"
                ]
                mock_neil.return_value = "<AGREE>true</AGREE> Correct calculation."
                
                result = await orchestrator.debate("1 + 1", max_rounds=3, pace="fast")
                
                # Verify basic result structure
                assert result is not None
                assert result.expression == "1 + 1"
                assert result.pace_mode == "fast"
                assert len(result.turns) > 0
    
    def test_cli_argument_parsing(self):
        """Test CLI argument parsing (without actually running)."""
        from debate_calc.app.ui_cli import main
        
        # This would require more complex mocking to test fully
        # For now, just verify the module can be imported
        assert main is not None
    
    def test_gui_initialization(self):
        """Test GUI initialization (without actually running)."""
        # Skip if DearPyGui not available
        try:
            # Test if DearPyGui can be imported first
            import dearpygui.dearpygui as dpg
            from debate_calc.app.ui_dpg import DebateGUI
            # Just test that the class can be imported
            assert DebateGUI is not None
        except ImportError as e:
            pytest.skip(f"DearPyGui not available: {e}")
        except SystemExit:
            pytest.skip("DearPyGui import caused system exit")
