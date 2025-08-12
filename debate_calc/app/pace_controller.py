"""
Pacing Controller for managing debate timing, rhythm, and UI cadence.
Ensures steady tempo with configurable parameters and jitter handling.
"""

import asyncio
import time
import random
from typing import Optional, Callable, Any
from dataclasses import dataclass
from .settings import PacingProfile, settings


@dataclass
class TurnTiming:
    """Timing information for a single debate turn."""
    start_time: float
    model_latency: float
    padding_time: float
    total_time: float
    jitter_applied: float


class PaceController:
    """Controls the timing and rhythm of debate interactions."""
    
    def __init__(self, pacing_profile: PacingProfile):
        self.profile = pacing_profile
        self.jitter_percentage = settings.jitter_percentage
        self._turn_timings: list[TurnTiming] = []
    
    def _apply_jitter(self, base_time: float) -> float:
        """Apply random jitter to timing to avoid machine-gun tempo."""
        jitter_range = base_time * self.jitter_percentage
        jitter = random.uniform(-jitter_range, jitter_range)
        return max(0.1, base_time + jitter)  # Minimum 0.1 seconds
    
    async def execute_turn(
        self, 
        model_call: Callable[[], Any], 
        speaker_name: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> tuple[Any, TurnTiming]:
        """
        Execute a model turn with proper pacing and timing enforcement.
        
        Args:
            model_call: Async function that calls the model
            speaker_name: Name of the speaker for progress updates
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (model_response, timing_info)
        """
        start_time = time.time()
        
        # Show thinking indicator
        if progress_callback:
            progress_callback(f"{speaker_name} thinking...")
        
        # Execute the model call
        try:
            response = await model_call()
            model_end_time = time.time()
            model_latency = model_end_time - start_time
        except Exception as e:
            # Even on error, respect minimum timing
            model_end_time = time.time()
            model_latency = model_end_time - start_time
            raise e
        
        # Calculate required padding to meet minimum turn time
        min_turn_time = self._apply_jitter(self.profile.min_turn_seconds)
        elapsed_time = model_end_time - start_time
        padding_needed = max(0, min_turn_time - elapsed_time)
        
        # Apply padding if needed
        if padding_needed > 0:
            if progress_callback:
                progress_callback(f"{speaker_name} finalizing...")
            await asyncio.sleep(padding_needed)
        
        total_time = time.time() - start_time
        
        # Record timing information
        timing = TurnTiming(
            start_time=start_time,
            model_latency=model_latency,
            padding_time=padding_needed,
            total_time=total_time,
            jitter_applied=min_turn_time - self.profile.min_turn_seconds
        )
        self._turn_timings.append(timing)
        
        return response, timing
    
    async def inter_turn_gap(self, progress_callback: Optional[Callable[[str], None]] = None) -> None:
        """Apply the inter-turn gap with jitter."""
        gap_time = self._apply_jitter(self.profile.inter_turn_gap_seconds)
        
        if progress_callback:
            progress_callback("Transitioning...")
        
        await asyncio.sleep(gap_time)
    
    def get_typeout_delay(self, text_length: int) -> float:
        """Calculate delay for typing effect based on text length and rate."""
        return text_length / self.profile.typeout_rate_chars_per_sec
    
    async def typeout_effect(
        self, 
        text: str, 
        output_callback: Callable[[str], None],
        chunk_size: int = 1
    ) -> None:
        """
        Apply typing effect to text output at the configured rate.
        
        Args:
            text: Text to type out
            output_callback: Function to call with each text chunk
            chunk_size: Number of characters per chunk
        """
        if not text:
            return
        
        char_delay = 1.0 / self.profile.typeout_rate_chars_per_sec
        
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            output_callback(chunk)
            
            # Don't delay after the last chunk
            if i + chunk_size < len(text):
                await asyncio.sleep(char_delay * len(chunk))
    
    def get_timing_summary(self) -> dict[str, Any]:
        """Get summary of timing statistics for telemetry."""
        if not self._turn_timings:
            return {}
        
        total_model_time = sum(t.model_latency for t in self._turn_timings)
        total_padding_time = sum(t.padding_time for t in self._turn_timings)
        total_debate_time = sum(t.total_time for t in self._turn_timings)
        
        return {
            "total_turns": len(self._turn_timings),
            "total_model_time": total_model_time,
            "total_padding_time": total_padding_time,
            "total_debate_time": total_debate_time,
            "avg_model_latency": total_model_time / len(self._turn_timings),
            "avg_padding_time": total_padding_time / len(self._turn_timings),
            "padding_percentage": (total_padding_time / total_debate_time) * 100 if total_debate_time > 0 else 0,
            "pace_profile": {
                "min_turn_seconds": self.profile.min_turn_seconds,
                "inter_turn_gap_seconds": self.profile.inter_turn_gap_seconds,
                "typeout_rate_chars_per_sec": self.profile.typeout_rate_chars_per_sec,
                "max_tokens_per_turn": self.profile.max_tokens_per_turn
            }
        }
    
    def reset_timings(self) -> None:
        """Reset timing history for a new debate."""
        self._turn_timings.clear()


class SyncPaceController:
    """Synchronous version of PaceController for CLI usage."""
    
    def __init__(self, pacing_profile: PacingProfile):
        self.profile = pacing_profile
        self.jitter_percentage = settings.jitter_percentage
        self._turn_timings: list[TurnTiming] = []
    
    def _apply_jitter(self, base_time: float) -> float:
        """Apply random jitter to timing to avoid machine-gun tempo."""
        jitter_range = base_time * self.jitter_percentage
        jitter = random.uniform(-jitter_range, jitter_range)
        return max(0.1, base_time + jitter)
    
    def execute_turn(
        self, 
        model_call: Callable[[], Any], 
        speaker_name: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> tuple[Any, TurnTiming]:
        """Synchronous version of execute_turn."""
        start_time = time.time()
        
        if progress_callback:
            progress_callback(f"{speaker_name} thinking...")
        
        try:
            response = model_call()
            model_end_time = time.time()
            model_latency = model_end_time - start_time
        except Exception as e:
            model_end_time = time.time()
            model_latency = model_end_time - start_time
            raise e
        
        min_turn_time = self._apply_jitter(self.profile.min_turn_seconds)
        elapsed_time = model_end_time - start_time
        padding_needed = max(0, min_turn_time - elapsed_time)
        
        if padding_needed > 0:
            if progress_callback:
                progress_callback(f"{speaker_name} finalizing...")
            time.sleep(padding_needed)
        
        total_time = time.time() - start_time
        
        timing = TurnTiming(
            start_time=start_time,
            model_latency=model_latency,
            padding_time=padding_needed,
            total_time=total_time,
            jitter_applied=min_turn_time - self.profile.min_turn_seconds
        )
        self._turn_timings.append(timing)
        
        return response, timing
    
    def inter_turn_gap(self, progress_callback: Optional[Callable[[str], None]] = None) -> None:
        """Synchronous inter-turn gap."""
        gap_time = self._apply_jitter(self.profile.inter_turn_gap_seconds)
        
        if progress_callback:
            progress_callback("Transitioning...")
        
        time.sleep(gap_time)
    
    def get_timing_summary(self) -> dict[str, Any]:
        """Get timing summary (same as async version)."""
        if not self._turn_timings:
            return {}
        
        total_model_time = sum(t.model_latency for t in self._turn_timings)
        total_padding_time = sum(t.padding_time for t in self._turn_timings)
        total_debate_time = sum(t.total_time for t in self._turn_timings)
        
        return {
            "total_turns": len(self._turn_timings),
            "total_model_time": total_model_time,
            "total_padding_time": total_padding_time,
            "total_debate_time": total_debate_time,
            "avg_model_latency": total_model_time / len(self._turn_timings),
            "avg_padding_time": total_padding_time / len(self._turn_timings),
            "padding_percentage": (total_padding_time / total_debate_time) * 100 if total_debate_time > 0 else 0
        }
    
    def reset_timings(self) -> None:
        """Reset timing history."""
        self._turn_timings.clear()
