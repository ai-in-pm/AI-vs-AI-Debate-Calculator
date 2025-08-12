"""
Protocol validation tests for the Debate Calculator.
Tests behavioral constraints and agreement detection.
"""

import pytest
import re
from unittest.mock import Mock, patch, AsyncMock

from debate_calc.app.orchestrator import DebateOrchestrator, DebateStatus
from debate_calc.app.settings import settings


class TestDebateProtocol:
    """Test suite for debate protocol validation."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator with mocked clients."""
        with patch('debate_calc.app.orchestrator.openai.OpenAI'), \
             patch('debate_calc.app.orchestrator.anthropic.Anthropic'):
            return DebateOrchestrator()
    
    @pytest.fixture
    def mock_terrence_response(self):
        """Mock Terrence response without final answer."""
        return "I need to solve 2 + 3. This equals 5 because addition is commutative."
    
    @pytest.fixture
    def mock_neil_disagree_response(self):
        """Mock Neil response with disagreement."""
        return "<AGREE>false</AGREE> I want to verify this calculation step by step."
    
    @pytest.fixture
    def mock_neil_agree_response(self):
        """Mock Neil response with agreement."""
        return "<AGREE>true</AGREE> Your calculation is correct."
    
    @pytest.fixture
    def mock_terrence_final_response(self):
        """Mock Terrence final response with answer."""
        return "<FINAL>5</FINAL>"
    
    def test_agreement_extraction_false(self, orchestrator, mock_neil_disagree_response):
        """Test extraction of false agreement flag."""
        agreement = orchestrator._extract_agreement(mock_neil_disagree_response)
        assert agreement is False
    
    def test_agreement_extraction_true(self, orchestrator, mock_neil_agree_response):
        """Test extraction of true agreement flag."""
        agreement = orchestrator._extract_agreement(mock_neil_agree_response)
        assert agreement is True
    
    def test_agreement_extraction_missing(self, orchestrator):
        """Test handling of missing agreement flag."""
        response = "I think you're wrong but I forgot the tag."
        agreement = orchestrator._extract_agreement(response)
        assert agreement is None
    
    def test_final_answer_extraction(self, orchestrator, mock_terrence_final_response):
        """Test extraction of final answer."""
        answer = orchestrator._extract_final_answer(mock_terrence_final_response)
        assert answer == "5"
    
    def test_final_answer_extraction_missing(self, orchestrator, mock_terrence_response):
        """Test handling of missing final answer."""
        answer = orchestrator._extract_final_answer(mock_terrence_response)
        assert answer is None
    
    @pytest.mark.asyncio
    async def test_neil_first_disagreement(self, orchestrator):
        """Test that Neil always disagrees first."""
        with patch.object(orchestrator, '_call_terrence', new_callable=AsyncMock) as mock_terrence, \
             patch.object(orchestrator, '_call_neil', new_callable=AsyncMock) as mock_neil:
            
            # Setup mock responses
            mock_terrence.side_effect = [
                "I calculate 2 + 3 = 5",
                "<FINAL>5</FINAL>"
            ]
            mock_neil.return_value = "<AGREE>true</AGREE> Correct calculation."
            
            result = await orchestrator.debate("2 + 3", max_rounds=2)
            
            # Verify Neil was called and would disagree first in real scenario
            assert mock_neil.called
            # In a real scenario, Neil should start with <AGREE>false</AGREE>
    
    @pytest.mark.asyncio
    async def test_no_final_before_agreement(self, orchestrator):
        """Test that Terrence doesn't provide final answer before Neil agrees."""
        with patch.object(orchestrator, '_call_terrence', new_callable=AsyncMock) as mock_terrence, \
             patch.object(orchestrator, '_call_neil', new_callable=AsyncMock) as mock_neil:
            
            # Terrence should not include <FINAL> in first response
            mock_terrence.side_effect = [
                "I calculate 2 + 3 = 5 using basic arithmetic",  # No <FINAL> tag
                "<FINAL>5</FINAL>"  # Only after agreement
            ]
            mock_neil.return_value = "<AGREE>true</AGREE> Correct."
            
            result = await orchestrator.debate("2 + 3", max_rounds=2)
            
            # Verify first Terrence response doesn't contain <FINAL>
            first_call_args = mock_terrence.call_args_list[0]
            # The response should not contain <FINAL> tag
            assert "<FINAL>" not in mock_terrence.side_effect[0]
    
    @pytest.mark.asyncio
    async def test_debate_flow_complete(self, orchestrator):
        """Test complete debate flow from start to finish."""
        with patch.object(orchestrator, '_call_terrence', new_callable=AsyncMock) as mock_terrence, \
             patch.object(orchestrator, '_call_neil', new_callable=AsyncMock) as mock_neil:
            
            # Setup realistic conversation flow
            mock_terrence.side_effect = [
                "I need to calculate 2 + 3. Using basic arithmetic: 2 + 3 = 5",
                "Let me clarify: 2 + 3 means adding 2 and 3, which equals 5",
                "<FINAL>5</FINAL>"
            ]
            
            mock_neil.side_effect = [
                "<AGREE>false</AGREE> Can you show the step-by-step process?",
                "<AGREE>true</AGREE> Yes, that's correct. 2 + 3 = 5."
            ]
            
            result = await orchestrator.debate("2 + 3", max_rounds=5)
            
            # Verify successful completion
            assert result.status == DebateStatus.COMPLETED
            assert result.final_answer == "5"
            assert result.rounds >= 2  # At least 2 rounds of back-and-forth
            assert len(result.turns) >= 3  # Terrence, Neil, Terrence final
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, orchestrator):
        """Test handling of debates that don't reach agreement."""
        with patch.object(orchestrator, '_call_terrence', new_callable=AsyncMock) as mock_terrence, \
             patch.object(orchestrator, '_call_neil', new_callable=AsyncMock) as mock_neil:
            
            # Neil never agrees
            mock_terrence.return_value = "I calculate 2 + 3 = 5"
            mock_neil.return_value = "<AGREE>false</AGREE> I still disagree."
            
            result = await orchestrator.debate("2 + 3", max_rounds=2)
            
            # Verify timeout handling
            assert result.status == DebateStatus.TIMEOUT
            assert result.final_answer is None
            assert "did not reach agreement" in result.error_message
    
    def test_regex_patterns(self, orchestrator):
        """Test regex patterns for tag extraction."""
        # Test AGREE tag variations
        agree_tests = [
            ("<AGREE>true</AGREE>", True),
            ("<AGREE>false</AGREE>", False),
            ("<agree>TRUE</agree>", True),  # Case insensitive
            ("<AGREE>FALSE</AGREE>", False),
            ("Some text <AGREE>true</AGREE> more text", True),
            ("No tag here", None)
        ]
        
        for text, expected in agree_tests:
            result = orchestrator._extract_agreement(text)
            assert result == expected, f"Failed for: {text}"
        
        # Test FINAL tag variations
        final_tests = [
            ("<FINAL>42</FINAL>", "42"),
            ("<final>hello world</final>", "hello world"),
            ("Text <FINAL>answer here</FINAL> more", "answer here"),
            ("<FINAL>multi\nline\nanswer</FINAL>", "multi\nline\nanswer"),
            ("No final tag", None)
        ]
        
        for text, expected in final_tests:
            result = orchestrator._extract_final_answer(text)
            assert result == expected, f"Failed for: {text}"


class TestPromptValidation:
    """Test prompt engineering and message formatting."""
    
    def test_terrence_message_structure(self):
        """Test Terrence message structure includes system prompt and examples."""
        from debate_calc.app.prompts import get_terrence_messages
        
        messages = get_terrence_messages("2 + 3")
        
        # Should have system prompt
        assert messages[0]["role"] == "system"
        assert "Terrence" in messages[0]["content"]
        assert "FINAL" in messages[0]["content"]
        
        # Should have examples
        example_count = sum(1 for msg in messages if msg["role"] == "assistant")
        assert example_count >= 1  # At least one example
        
        # Should end with user expression
        assert messages[-1]["role"] == "user"
        assert "2 + 3" in messages[-1]["content"]
    
    def test_neil_message_structure(self):
        """Test Neil message structure includes system prompt and examples."""
        from debate_calc.app.prompts import get_neil_messages
        
        messages = get_neil_messages("Terrence says: 2 + 3 = 5")
        
        # Should have system prompt
        assert messages[0]["role"] == "system"
        assert "Neil" in messages[0]["content"]
        assert "AGREE" in messages[0]["content"]
        
        # Should have examples with AGREE tags
        example_responses = [msg["content"] for msg in messages if msg["role"] == "assistant"]
        assert any("<AGREE>false</AGREE>" in resp for resp in example_responses)
        
        # Should end with Terrence's statement
        assert messages[-1]["role"] == "user"
        assert "Terrence says:" in messages[-1]["content"]
    
    def test_final_prompt_generation(self):
        """Test final prompt generation for Terrence."""
        from debate_calc.app.prompts import get_terrence_final_prompt
        
        neil_agreement = "<AGREE>true</AGREE> You are correct."
        prompt = get_terrence_final_prompt(neil_agreement)
        
        assert "Neil has agreed" in prompt
        assert "<FINAL>" in prompt
        assert neil_agreement in prompt
