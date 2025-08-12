"""
Command-line interface for the Debate Calculator.
Provides pace selection, progress indicators, and steady tempo display.
"""

import argparse
import sys
import time
import threading
from typing import Optional

try:
    from .settings import settings, PaceMode
    from .orchestrator import DebateOrchestrator, DebateStatus
    from .telemetry import TelemetryLogger
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from debate_calc.app.settings import settings, PaceMode
    from debate_calc.app.orchestrator import DebateOrchestrator, DebateStatus
    from debate_calc.app.telemetry import TelemetryLogger


class CLIProgressIndicator:
    """Manages progress indicators and status updates for CLI."""
    
    def __init__(self):
        self.current_status = ""
        self.is_thinking = False
        self.thinking_thread: Optional[threading.Thread] = None
        self.stop_thinking = threading.Event()
    
    def update_status(self, status: str) -> None:
        """Update the current status message."""
        self.stop_thinking_animation()
        print(f"\r{' ' * 80}\r{status}", end="", flush=True)
        self.current_status = status
        
        if "thinking" in status.lower():
            self.start_thinking_animation()
    
    def start_thinking_animation(self) -> None:
        """Start animated thinking indicator."""
        if self.is_thinking:
            return
        
        self.is_thinking = True
        self.stop_thinking.clear()
        self.thinking_thread = threading.Thread(target=self._thinking_animation)
        self.thinking_thread.daemon = True
        self.thinking_thread.start()
    
    def stop_thinking_animation(self) -> None:
        """Stop thinking animation."""
        if not self.is_thinking:
            return
        
        self.is_thinking = False
        self.stop_thinking.set()
        if self.thinking_thread:
            self.thinking_thread.join(timeout=1.0)
    
    def _thinking_animation(self) -> None:
        """Animated dots for thinking indicator."""
        dots = ""
        while not self.stop_thinking.is_set():
            for i in range(4):
                if self.stop_thinking.is_set():
                    break
                dots = "." * i
                print(f"\r{self.current_status}{dots}   ", end="", flush=True)
                time.sleep(0.5)
    
    def clear(self) -> None:
        """Clear the current status line."""
        self.stop_thinking_animation()
        print(f"\r{' ' * 80}\r", end="", flush=True)


def format_debate_turn(turn, show_timing: bool = False) -> str:
    """Format a debate turn for display."""
    speaker_color = "\033[94m" if turn.speaker == "Terrence" else "\033[93m"  # Blue for Terrence, Yellow for Neil
    reset_color = "\033[0m"
    
    header = f"{speaker_color}=== {turn.speaker} ==={reset_color}"
    content = turn.content
    
    if show_timing and turn.timing:
        timing_info = (
            f"  [Model: {turn.timing.model_latency:.2f}s, "
            f"Padding: {turn.timing.padding_time:.2f}s, "
            f"Total: {turn.timing.total_time:.2f}s]"
        )
        content += f"\n{timing_info}"
    
    if turn.agreement_flag is not None:
        agreement_color = "\033[92m" if turn.agreement_flag else "\033[91m"  # Green for true, Red for false
        agreement_text = f"{agreement_color}[AGREES: {turn.agreement_flag}]{reset_color}"
        content += f"\n{agreement_text}"
    
    return f"{header}\n{content}\n"


def display_debate_result(result, show_timing: bool = False) -> None:
    """Display the complete debate result."""
    print("\n" + "="*80)
    print(f"DEBATE RESULT: {result.expression}")
    print("="*80)
    
    # Show each turn
    for turn in result.turns:
        print(format_debate_turn(turn, show_timing))
        print("-" * 40)
    
    # Show final result
    status_color = {
        DebateStatus.COMPLETED: "\033[92m",  # Green
        DebateStatus.TIMEOUT: "\033[93m",    # Yellow
        DebateStatus.ERROR: "\033[91m"       # Red
    }.get(result.status, "\033[0m")
    
    print(f"\n{status_color}STATUS: {result.status.value.upper()}\033[0m")
    
    if result.final_answer:
        print(f"\033[92mFINAL ANSWER: {result.final_answer}\033[0m")
    
    if result.error_message:
        print(f"\033[91mERROR: {result.error_message}\033[0m")
    
    # Show summary statistics
    print(f"\nRounds: {result.rounds}")
    print(f"Total Time: {result.total_time:.2f}s")
    print(f"Pace Mode: {result.pace_mode}")
    
    if show_timing and result.timing_summary:
        summary = result.timing_summary
        print(f"\nTiming Summary:")
        print(f"  Model Time: {summary.get('total_model_time', 0):.2f}s")
        print(f"  Padding Time: {summary.get('total_padding_time', 0):.2f}s")
        print(f"  Padding %: {summary.get('padding_percentage', 0):.1f}%")
        print(f"  Avg Model Latency: {summary.get('avg_model_latency', 0):.2f}s")


def run_interactive_mode(orchestrator: DebateOrchestrator, pace: PaceMode, show_timing: bool) -> None:
    """Run interactive mode for continuous calculations."""
    print(f"\n\033[94mDebate Calculator - Interactive Mode\033[0m")
    print(f"Pace: {pace.upper()}")
    print("Enter mathematical expressions (or 'quit' to exit)")
    print("-" * 50)
    
    progress = CLIProgressIndicator()
    
    while True:
        try:
            progress.clear()
            expression = input("\nExpression: ").strip()
            
            if expression.lower() in ['quit', 'exit', 'q']:
                break
            
            if not expression:
                continue
            
            print(f"\nStarting debate for: {expression}")
            print("=" * 50)
            
            # Run debate with progress callback
            result = orchestrator.debate_sync(
                expression=expression,
                pace=pace,
                progress_callback=progress.update_status
            )
            
            progress.clear()
            display_debate_result(result, show_timing)
            
        except KeyboardInterrupt:
            progress.clear()
            print("\n\nDebate interrupted by user.")
            break
        except Exception as e:
            progress.clear()
            print(f"\n\033[91mError: {e}\033[0m")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI vs AI Mathematical Debate Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  debate-calc "2 + 3 * 4"
  debate-calc "sqrt(16)" --pace fast
  debate-calc --interactive --pace medium --timing
  debate-calc "1 + 1" --max-rounds 5 --timing
        """
    )
    
    parser.add_argument(
        "expression",
        nargs="?",
        help="Mathematical expression to evaluate"
    )
    
    parser.add_argument(
        "--pace",
        choices=["slow", "medium", "fast"],
        default=settings.default_pace_mode,
        help=f"Debate pacing mode (default: {settings.default_pace_mode})"
    )
    
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=settings.max_rounds,
        help=f"Maximum debate rounds (default: {settings.max_rounds})"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode for multiple calculations"
    )
    
    parser.add_argument(
        "--timing",
        action="store_true",
        help="Show detailed timing information"
    )
    
    parser.add_argument(
        "--analyze-logs",
        metavar="LOG_FILE",
        help="Analyze telemetry log file and show statistics"
    )
    
    args = parser.parse_args()
    
    # Handle log analysis
    if args.analyze_logs:
        stats = TelemetryLogger.analyze_log_file(args.analyze_logs)
        if "error" in stats:
            print(f"Error: {stats['error']}")
            sys.exit(1)
        
        print("Telemetry Analysis")
        print("=" * 50)
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            elif isinstance(value, list):
                print(f"{key}: {len(value)} unique")
            else:
                print(f"{key}: {value}")
        sys.exit(0)
    
    # Validate arguments
    if not args.interactive and not args.expression:
        parser.error("Expression required unless using --interactive mode")
    
    # Initialize orchestrator
    try:
        orchestrator = DebateOrchestrator()
    except Exception as e:
        print(f"Failed to initialize debate orchestrator: {e}")
        print("Please check your API keys in .env file")
        sys.exit(1)
    
    pace = args.pace
    
    # Run interactive mode
    if args.interactive:
        run_interactive_mode(orchestrator, pace, args.timing)
        return
    
    # Run single calculation
    print(f"Debate Calculator - Expression: {args.expression}")
    print(f"Pace: {pace.upper()}, Max Rounds: {args.max_rounds}")
    print("=" * 60)
    
    progress = CLIProgressIndicator()
    
    try:
        result = orchestrator.debate_sync(
            expression=args.expression,
            max_rounds=args.max_rounds,
            pace=pace,
            progress_callback=progress.update_status
        )
        
        progress.clear()
        display_debate_result(result, args.timing)
        
        # Exit with appropriate code
        if result.status == DebateStatus.COMPLETED:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        progress.clear()
        print("\n\nDebate interrupted by user.")
        sys.exit(130)
    except Exception as e:
        progress.clear()
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
