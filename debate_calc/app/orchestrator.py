"""
Core orchestrator for managing AI vs AI mathematical debates.
Handles model interactions, agreement detection, and pacing integration.
"""

import re
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

import openai
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from .settings import settings, PaceMode
from .prompts import get_terrence_messages, get_neil_messages, get_terrence_final_prompt
from .pace_controller import PaceController, SyncPaceController, TurnTiming
from .telemetry import TelemetryLogger


class DebateStatus(Enum):
    """Status of the debate process."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class DebateTurn:
    """Information about a single debate turn."""
    speaker: str
    content: str
    timestamp: float
    timing: Optional[TurnTiming] = None
    agreement_flag: Optional[bool] = None
    tokens_used: Optional[int] = None


@dataclass
class DebateResult:
    """Result of a complete debate session."""
    status: DebateStatus
    expression: str
    final_answer: Optional[str] = None
    rounds: int = 0
    turns: List[DebateTurn] = field(default_factory=list)
    total_time: float = 0.0
    error_message: Optional[str] = None
    pace_mode: str = "slow"
    timing_summary: Dict[str, Any] = field(default_factory=dict)


class DebateOrchestrator:
    """Orchestrates debates between Terrence (GPT-5) and Neil (Claude 3.7 Sonnet)."""
    
    # Regex patterns for parsing responses
    AGREE_TAG = re.compile(r"<AGREE>(true|false)</AGREE>", re.IGNORECASE)
    FINAL_TAG = re.compile(r"<FINAL>(.*?)</FINAL>", re.IGNORECASE | re.DOTALL)
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.telemetry = TelemetryLogger() if settings.telemetry_enabled else None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=10)
    )
    async def _call_terrence(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Call Terrence (OpenAI GPT-5) with retry logic."""
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=settings.openai_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=settings.openai_temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if self.telemetry:
                self.telemetry.log_error("terrence_call_failed", str(e))
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=10)
    )
    async def _call_neil(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Call Neil (Anthropic Claude 3.7 Sonnet) with retry logic."""
        try:
            # Convert OpenAI format to Anthropic format
            system_message = None
            conversation_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    conversation_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=settings.anthropic_model,
                system=system_message,
                messages=conversation_messages,
                max_tokens=max_tokens,
                temperature=settings.anthropic_temperature
            )
            return response.content[0].text.strip()
        except Exception as e:
            if self.telemetry:
                self.telemetry.log_error("neil_call_failed", str(e))
            raise
    
    def _extract_agreement(self, response: str) -> Optional[bool]:
        """Extract agreement flag from Neil's response."""
        match = self.AGREE_TAG.search(response)
        if match:
            return match.group(1).lower() == "true"
        return None
    
    def _extract_final_answer(self, response: str) -> Optional[str]:
        """Extract final answer from Terrence's response."""
        match = self.FINAL_TAG.search(response)
        if match:
            return match.group(1).strip()
        return None
    
    async def debate(
        self, 
        expression: str, 
        max_rounds: int = None,
        pace: PaceMode = "slow",
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> DebateResult:
        """
        Conduct a debate between Terrence and Neil about a mathematical expression.
        
        Args:
            expression: Mathematical expression to evaluate
            max_rounds: Maximum number of debate rounds (default from settings)
            pace: Pacing mode (slow/medium/fast)
            progress_callback: Optional callback for progress updates
            
        Returns:
            DebateResult with complete debate information
        """
        if max_rounds is None:
            max_rounds = settings.max_rounds
        
        start_time = time.time()
        pacing_profile = settings.get_pacing_profile(pace)
        pace_controller = PaceController(pacing_profile)
        
        result = DebateResult(
            status=DebateStatus.IN_PROGRESS,
            expression=expression,
            pace_mode=pace
        )
        
        try:
            if self.telemetry:
                self.telemetry.log_debate_start(expression, pace, max_rounds)
            
            conversation_history = []
            
            for round_num in range(max_rounds):
                result.rounds = round_num + 1
                
                # Terrence's turn
                terrence_messages = get_terrence_messages(expression, conversation_history)
                
                async def terrence_call():
                    return await self._call_terrence(terrence_messages, pacing_profile.max_tokens_per_turn)
                
                terrence_response, terrence_timing = await pace_controller.execute_turn(
                    terrence_call, "Terrence", progress_callback
                )
                
                # Record Terrence's turn
                terrence_turn = DebateTurn(
                    speaker="Terrence",
                    content=terrence_response,
                    timestamp=time.time(),
                    timing=terrence_timing,
                    tokens_used=len(terrence_response.split())  # Rough estimate
                )
                result.turns.append(terrence_turn)
                conversation_history.extend([
                    {"role": "assistant", "content": terrence_response}
                ])
                
                if self.telemetry:
                    self.telemetry.log_turn(terrence_turn)
                
                # Check if Terrence provided final answer (shouldn't happen before agreement)
                final_answer = self._extract_final_answer(terrence_response)
                if final_answer:
                    result.final_answer = final_answer
                    result.status = DebateStatus.COMPLETED
                    break
                
                # Inter-turn gap
                await pace_controller.inter_turn_gap(progress_callback)
                
                # Neil's turn
                neil_messages = get_neil_messages(terrence_response, conversation_history[:-1])
                
                async def neil_call():
                    return await self._call_neil(neil_messages, pacing_profile.max_tokens_per_turn)
                
                neil_response, neil_timing = await pace_controller.execute_turn(
                    neil_call, "Neil", progress_callback
                )
                
                # Extract agreement flag
                agreement = self._extract_agreement(neil_response)
                
                # Record Neil's turn
                neil_turn = DebateTurn(
                    speaker="Neil",
                    content=neil_response,
                    timestamp=time.time(),
                    timing=neil_timing,
                    agreement_flag=agreement,
                    tokens_used=len(neil_response.split())
                )
                result.turns.append(neil_turn)
                conversation_history.extend([
                    {"role": "user", "content": f"Neil says: {neil_response}"}
                ])
                
                if self.telemetry:
                    self.telemetry.log_turn(neil_turn)
                
                # Check if Neil agreed
                if agreement is True:
                    # Inter-turn gap before final answer
                    await pace_controller.inter_turn_gap(progress_callback)
                    
                    # Get final answer from Terrence
                    final_prompt = get_terrence_final_prompt(neil_response)
                    final_messages = terrence_messages + [{"role": "user", "content": final_prompt}]
                    
                    async def final_call():
                        return await self._call_terrence(final_messages, pacing_profile.max_tokens_per_turn)
                    
                    final_response, final_timing = await pace_controller.execute_turn(
                        final_call, "Terrence", progress_callback
                    )
                    
                    # Record final turn
                    final_turn = DebateTurn(
                        speaker="Terrence",
                        content=final_response,
                        timestamp=time.time(),
                        timing=final_timing,
                        tokens_used=len(final_response.split())
                    )
                    result.turns.append(final_turn)
                    
                    if self.telemetry:
                        self.telemetry.log_turn(final_turn)
                    
                    # Extract final answer
                    final_answer = self._extract_final_answer(final_response)
                    if final_answer:
                        result.final_answer = final_answer
                        result.status = DebateStatus.COMPLETED
                    else:
                        result.status = DebateStatus.ERROR
                        result.error_message = "Terrence failed to provide final answer after agreement"
                    break
                
                # Continue to next round if no agreement
                if round_num < max_rounds - 1:
                    await pace_controller.inter_turn_gap(progress_callback)
            
            # Check if we hit max rounds without resolution
            if result.status == DebateStatus.IN_PROGRESS:
                result.status = DebateStatus.TIMEOUT
                result.error_message = f"Debate did not reach agreement within {max_rounds} rounds"
        
        except Exception as e:
            result.status = DebateStatus.ERROR
            result.error_message = str(e)
            if self.telemetry:
                self.telemetry.log_error("debate_failed", str(e))
        
        finally:
            result.total_time = time.time() - start_time
            result.timing_summary = pace_controller.get_timing_summary()
            
            if self.telemetry:
                self.telemetry.log_debate_end(result)
        
        return result

    def debate_sync(
        self,
        expression: str,
        max_rounds: int = None,
        pace: PaceMode = "slow",
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> DebateResult:
        """
        Synchronous version of debate for CLI usage.
        """
        if max_rounds is None:
            max_rounds = settings.max_rounds

        start_time = time.time()
        pacing_profile = settings.get_pacing_profile(pace)
        pace_controller = SyncPaceController(pacing_profile)

        result = DebateResult(
            status=DebateStatus.IN_PROGRESS,
            expression=expression,
            pace_mode=pace
        )

        try:
            if self.telemetry:
                self.telemetry.log_debate_start(expression, pace, max_rounds)

            conversation_history = []

            for round_num in range(max_rounds):
                result.rounds = round_num + 1

                # Terrence's turn (synchronous)
                terrence_messages = get_terrence_messages(expression, conversation_history)

                def terrence_call():
                    response = self.openai_client.chat.completions.create(
                        model=settings.openai_model,
                        messages=terrence_messages,
                        max_tokens=pacing_profile.max_tokens_per_turn,
                        temperature=settings.openai_temperature
                    )
                    return response.choices[0].message.content.strip()

                terrence_response, terrence_timing = pace_controller.execute_turn(
                    terrence_call, "Terrence", progress_callback
                )

                # Record and process Terrence's turn (same logic as async version)
                terrence_turn = DebateTurn(
                    speaker="Terrence",
                    content=terrence_response,
                    timestamp=time.time(),
                    timing=terrence_timing,
                    tokens_used=len(terrence_response.split())
                )
                result.turns.append(terrence_turn)
                conversation_history.extend([
                    {"role": "assistant", "content": terrence_response}
                ])

                if self.telemetry:
                    self.telemetry.log_turn(terrence_turn)

                # Check for final answer
                final_answer = self._extract_final_answer(terrence_response)
                if final_answer:
                    result.final_answer = final_answer
                    result.status = DebateStatus.COMPLETED
                    break

                # Inter-turn gap
                pace_controller.inter_turn_gap(progress_callback)

                # Neil's turn (synchronous)
                neil_messages = get_neil_messages(terrence_response, conversation_history[:-1])

                def neil_call():
                    # Convert to Anthropic format
                    system_message = None
                    conversation_messages = []

                    for msg in neil_messages:
                        if msg["role"] == "system":
                            system_message = msg["content"]
                        else:
                            conversation_messages.append({
                                "role": msg["role"],
                                "content": msg["content"]
                            })

                    response = self.anthropic_client.messages.create(
                        model=settings.anthropic_model,
                        system=system_message,
                        messages=conversation_messages,
                        max_tokens=pacing_profile.max_tokens_per_turn,
                        temperature=settings.anthropic_temperature
                    )
                    return response.content[0].text.strip()

                neil_response, neil_timing = pace_controller.execute_turn(
                    neil_call, "Neil", progress_callback
                )

                # Process Neil's response (same logic as async)
                agreement = self._extract_agreement(neil_response)

                neil_turn = DebateTurn(
                    speaker="Neil",
                    content=neil_response,
                    timestamp=time.time(),
                    timing=neil_timing,
                    agreement_flag=agreement,
                    tokens_used=len(neil_response.split())
                )
                result.turns.append(neil_turn)
                conversation_history.extend([
                    {"role": "user", "content": f"Neil says: {neil_response}"}
                ])

                if self.telemetry:
                    self.telemetry.log_turn(neil_turn)

                # Check for agreement and get final answer
                if agreement is True:
                    pace_controller.inter_turn_gap(progress_callback)

                    final_prompt = get_terrence_final_prompt(neil_response)
                    final_messages = terrence_messages + [{"role": "user", "content": final_prompt}]

                    def final_call():
                        response = self.openai_client.chat.completions.create(
                            model=settings.openai_model,
                            messages=final_messages,
                            max_tokens=pacing_profile.max_tokens_per_turn,
                            temperature=settings.openai_temperature
                        )
                        return response.choices[0].message.content.strip()

                    final_response, final_timing = pace_controller.execute_turn(
                        final_call, "Terrence", progress_callback
                    )

                    final_turn = DebateTurn(
                        speaker="Terrence",
                        content=final_response,
                        timestamp=time.time(),
                        timing=final_timing,
                        tokens_used=len(final_response.split())
                    )
                    result.turns.append(final_turn)

                    if self.telemetry:
                        self.telemetry.log_turn(final_turn)

                    final_answer = self._extract_final_answer(final_response)
                    if final_answer:
                        result.final_answer = final_answer
                        result.status = DebateStatus.COMPLETED
                    else:
                        result.status = DebateStatus.ERROR
                        result.error_message = "Terrence failed to provide final answer after agreement"
                    break

                # Continue to next round
                if round_num < max_rounds - 1:
                    pace_controller.inter_turn_gap(progress_callback)

            # Check timeout
            if result.status == DebateStatus.IN_PROGRESS:
                result.status = DebateStatus.TIMEOUT
                result.error_message = f"Debate did not reach agreement within {max_rounds} rounds"

        except Exception as e:
            result.status = DebateStatus.ERROR
            result.error_message = str(e)
            if self.telemetry:
                self.telemetry.log_error("debate_failed", str(e))

        finally:
            result.total_time = time.time() - start_time
            result.timing_summary = pace_controller.get_timing_summary()

            if self.telemetry:
                self.telemetry.log_debate_end(result)

        return result
