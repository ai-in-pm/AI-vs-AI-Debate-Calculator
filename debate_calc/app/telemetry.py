"""
Telemetry and logging system for debate performance analysis.
Tracks timing, turn statistics, and performance metrics.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from .settings import settings, PaceMode


@dataclass
class TurnMetrics:
    """Metrics for a single debate turn."""
    speaker: str
    timestamp: float
    model_latency: float
    padding_time: float
    total_time: float
    tokens_used: int
    agreement_flag: Optional[bool] = None
    jitter_applied: float = 0.0


@dataclass
class DebateMetrics:
    """Complete metrics for a debate session."""
    expression: str
    pace_mode: str
    max_rounds: int
    start_time: float
    end_time: float
    total_time: float
    status: str
    final_answer: Optional[str]
    rounds_completed: int
    total_turns: int
    total_model_time: float
    total_padding_time: float
    padding_percentage: float
    error_message: Optional[str] = None
    turns: List[TurnMetrics] = None


class TelemetryLogger:
    """Handles logging and metrics collection for debate sessions."""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or "debate_telemetry.jsonl"
        self.logger = self._setup_logger()
        self.current_debate: Optional[Dict[str, Any]] = None
        self.turn_metrics: List[TurnMetrics] = []
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logging for telemetry."""
        logger = logging.getLogger("debate_telemetry")
        logger.setLevel(getattr(logging, settings.log_level.upper()))
        
        # Avoid duplicate handlers
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def log_debate_start(self, expression: str, pace: PaceMode, max_rounds: int) -> None:
        """Log the start of a new debate session."""
        self.current_debate = {
            "expression": expression,
            "pace_mode": pace,
            "max_rounds": max_rounds,
            "start_time": time.time(),
            "turns": []
        }
        self.turn_metrics.clear()
        
        self.logger.info(f"Debate started: {expression} (pace: {pace}, max_rounds: {max_rounds})")
    
    def log_turn(self, turn) -> None:
        """Log metrics for a single debate turn."""
        if not self.current_debate:
            self.logger.warning("Attempted to log turn without active debate")
            return
        
        # Extract timing information
        timing = turn.timing
        metrics = TurnMetrics(
            speaker=turn.speaker,
            timestamp=turn.timestamp,
            model_latency=timing.model_latency if timing else 0.0,
            padding_time=timing.padding_time if timing else 0.0,
            total_time=timing.total_time if timing else 0.0,
            tokens_used=turn.tokens_used or 0,
            agreement_flag=turn.agreement_flag,
            jitter_applied=timing.jitter_applied if timing else 0.0
        )
        
        self.turn_metrics.append(metrics)
        self.current_debate["turns"].append(asdict(metrics))
        
        self.logger.debug(
            f"Turn logged: {turn.speaker} - "
            f"model_latency={metrics.model_latency:.2f}s, "
            f"padding={metrics.padding_time:.2f}s, "
            f"tokens={metrics.tokens_used}"
        )
    
    def log_debate_end(self, result) -> None:
        """Log the completion of a debate session."""
        if not self.current_debate:
            self.logger.warning("Attempted to log debate end without active debate")
            return
        
        end_time = time.time()
        
        # Calculate aggregate metrics
        total_model_time = sum(m.model_latency for m in self.turn_metrics)
        total_padding_time = sum(m.padding_time for m in self.turn_metrics)
        total_debate_time = result.total_time
        
        padding_percentage = (
            (total_padding_time / total_debate_time) * 100 
            if total_debate_time > 0 else 0
        )
        
        # Create complete debate metrics
        debate_metrics = DebateMetrics(
            expression=self.current_debate["expression"],
            pace_mode=self.current_debate["pace_mode"],
            max_rounds=self.current_debate["max_rounds"],
            start_time=self.current_debate["start_time"],
            end_time=end_time,
            total_time=total_debate_time,
            status=result.status.value,
            final_answer=result.final_answer,
            rounds_completed=result.rounds,
            total_turns=len(self.turn_metrics),
            total_model_time=total_model_time,
            total_padding_time=total_padding_time,
            padding_percentage=padding_percentage,
            error_message=result.error_message,
            turns=self.turn_metrics
        )
        
        # Log to file
        self._write_metrics_to_file(debate_metrics)
        
        # Log summary
        self.logger.info(
            f"Debate completed: {result.status.value} - "
            f"rounds={result.rounds}, "
            f"total_time={total_debate_time:.2f}s, "
            f"padding={padding_percentage:.1f}%"
        )
        
        if result.final_answer:
            self.logger.info(f"Final answer: {result.final_answer}")
        
        if result.error_message:
            self.logger.error(f"Debate error: {result.error_message}")
        
        # Reset for next debate
        self.current_debate = None
        self.turn_metrics.clear()
    
    def log_error(self, error_type: str, error_message: str) -> None:
        """Log an error during debate execution."""
        self.logger.error(f"{error_type}: {error_message}")
        
        # Add to current debate if active
        if self.current_debate:
            if "errors" not in self.current_debate:
                self.current_debate["errors"] = []
            self.current_debate["errors"].append({
                "type": error_type,
                "message": error_message,
                "timestamp": time.time()
            })
    
    def _write_metrics_to_file(self, metrics: DebateMetrics) -> None:
        """Write debate metrics to JSONL file for analysis."""
        try:
            # Convert to dict and write as JSON line
            metrics_dict = asdict(metrics)
            
            # Ensure log directory exists
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics_dict) + "\n")
                
        except Exception as e:
            self.logger.error(f"Failed to write metrics to file: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current debate session."""
        if not self.current_debate or not self.turn_metrics:
            return {}
        
        total_model_time = sum(m.model_latency for m in self.turn_metrics)
        total_padding_time = sum(m.padding_time for m in self.turn_metrics)
        total_time = sum(m.total_time for m in self.turn_metrics)
        
        return {
            "expression": self.current_debate["expression"],
            "pace_mode": self.current_debate["pace_mode"],
            "turns_completed": len(self.turn_metrics),
            "total_model_time": total_model_time,
            "total_padding_time": total_padding_time,
            "total_time": total_time,
            "padding_percentage": (total_padding_time / total_time) * 100 if total_time > 0 else 0,
            "avg_model_latency": total_model_time / len(self.turn_metrics),
            "avg_padding_time": total_padding_time / len(self.turn_metrics)
        }
    
    @staticmethod
    def analyze_log_file(log_file: str) -> Dict[str, Any]:
        """Analyze a telemetry log file and return aggregate statistics."""
        try:
            debates = []
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        debates.append(json.loads(line))
            
            if not debates:
                return {"error": "No debates found in log file"}
            
            # Calculate aggregate statistics
            total_debates = len(debates)
            completed_debates = sum(1 for d in debates if d["status"] == "completed")
            avg_rounds = sum(d["rounds_completed"] for d in debates) / total_debates
            avg_time = sum(d["total_time"] for d in debates) / total_debates
            avg_padding = sum(d["padding_percentage"] for d in debates) / total_debates
            
            pace_distribution = {}
            for debate in debates:
                pace = debate["pace_mode"]
                pace_distribution[pace] = pace_distribution.get(pace, 0) + 1
            
            return {
                "total_debates": total_debates,
                "completed_debates": completed_debates,
                "completion_rate": (completed_debates / total_debates) * 100,
                "avg_rounds": avg_rounds,
                "avg_time_seconds": avg_time,
                "avg_padding_percentage": avg_padding,
                "pace_distribution": pace_distribution,
                "expressions_analyzed": list(set(d["expression"] for d in debates))
            }
            
        except Exception as e:
            return {"error": f"Failed to analyze log file: {e}"}
