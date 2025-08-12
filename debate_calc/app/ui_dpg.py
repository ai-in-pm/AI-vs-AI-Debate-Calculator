"""
Dear PyGui GUI interface for the Debate Calculator.
Features typing effects, threading, pace controls, and visual cadence indicators.
"""

import sys
import os
import asyncio
import threading
import time
import queue
from typing import Optional, Dict, Any

# DearPyGui Import with Comprehensive Error Handling
def import_dearpygui():
    """Try multiple strategies to import DearPyGui with detailed diagnostics."""
    import_errors = []

    # Strategy 1: Direct import
    try:
        import dearpygui.dearpygui as dpg
        print("✅ DearPyGui imported successfully")
        return dpg
    except ImportError as e:
        import_errors.append(f"Direct import failed: {e}")

        # Check if it's the specific _dearpygui issue
        if "_dearpygui" in str(e):
            print("🔍 Detected _dearpygui compiled module issue")
            print("This usually means:")
            print("  - DearPyGui package is installed but compiled components are missing")
            print("  - Python version compatibility issue (DearPyGui may not support Python 3.13)")
            print("  - Missing Visual C++ Redistributables")

    # Strategy 2: Check package installation
    try:
        import pkg_resources
        dpg_dist = pkg_resources.get_distribution("dearpygui")
        print(f"📦 DearPyGui package found: version {dpg_dist.version} at {dpg_dist.location}")

        # Check if the compiled module exists
        import dearpygui
        dpg_path = dearpygui.__file__
        dpg_dir = os.path.dirname(dpg_path)
        compiled_module = os.path.join(dpg_dir, "_dearpygui.pyd")  # Windows
        if not os.path.exists(compiled_module):
            compiled_module = os.path.join(dpg_dir, "_dearpygui.so")  # Linux

        if os.path.exists(compiled_module):
            print(f"✅ Compiled module found: {compiled_module}")
        else:
            print(f"❌ Compiled module missing: {compiled_module}")
            print("This indicates an incomplete installation")

    except Exception as e:
        import_errors.append(f"Package inspection failed: {e}")

    # Strategy 3: Try local path (if available)
    dearpygui_path = r"D:\science_projects\agent_vs_agent\DearPyGui-master"
    if os.path.exists(dearpygui_path):
        print(f"🔍 Local DearPyGui source found: {dearpygui_path}")
        if dearpygui_path not in sys.path:
            sys.path.insert(0, dearpygui_path)
        try:
            import dearpygui.dearpygui as dpg
            print("✅ DearPyGui imported from local source")
            return dpg
        except ImportError as e:
            import_errors.append(f"Local source import failed: {e}")

    # All strategies failed - provide comprehensive guidance
    print("\n❌ DearPyGui import failed completely")
    print("\n📋 Diagnostic Information:")
    for i, error in enumerate(import_errors, 1):
        print(f"   {i}. {error}")

    print("\n🔧 Recommended Solutions (in order):")
    print("   1. Install Visual C++ Redistributable:")
    print("      https://aka.ms/vs/17/release/vc_redist.x64.exe")
    print("   2. Try different DearPyGui version:")
    print("      pip uninstall dearpygui && pip install 'dearpygui==1.11.1'")
    print("   3. Use Python 3.11 or 3.12 instead of 3.13:")
    print("      DearPyGui may not support Python 3.13 yet")
    print("   4. Use CLI interface instead:")
    print("      python -m debate_calc.app.ui_cli")
    print("   5. Run the DearPyGui fix script:")
    print("      .\\fix_dearpygui.ps1")

    # Don't exit - let the caller handle this gracefully
    raise ImportError("DearPyGui not available - see solutions above")

# Try to import DearPyGui, but make it optional
try:
    dpg = import_dearpygui()
    DEARPYGUI_AVAILABLE = True
except ImportError:
    dpg = None
    DEARPYGUI_AVAILABLE = False
    print("\n⚠️  GUI interface disabled - DearPyGui not available")
    print("✅ CLI interface remains fully functional")

try:
    from .settings import settings, PaceMode
    from .orchestrator import DebateOrchestrator, DebateStatus, DebateResult
    from .pace_controller import PaceController
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from debate_calc.app.settings import settings, PaceMode
    from debate_calc.app.orchestrator import DebateOrchestrator, DebateStatus, DebateResult
    from debate_calc.app.pace_controller import PaceController


class DebateGUI:
    """Main GUI application for the Debate Calculator."""

    def __init__(self):
        if not DEARPYGUI_AVAILABLE:
            raise ImportError("DearPyGui not available - cannot create GUI")

        self.orchestrator = DebateOrchestrator()
        self.current_debate: Optional[threading.Thread] = None
        self.debate_active = False
        self.message_queue = queue.Queue()
        self.typing_queue = queue.Queue()

        # GUI state
        self.expression_input = None
        self.pace_selector = None
        self.start_button = None
        self.transcript_text = None
        self.final_answer_text = None
        self.status_text = None
        self.progress_bar = None
        self.spinner_visible = False

        # Debate state
        self.current_result: Optional[DebateResult] = None
        self.start_time = 0.0

        self._setup_gui()
    
    def _setup_gui(self) -> None:
        """Initialize the Dear PyGui interface."""
        dpg.create_context()
        
        # Setup fonts and theme
        self._setup_theme()
        
        # Create main window
        with dpg.window(label="AI vs AI Debate Calculator", tag="main_window"):
            # Header section
            dpg.add_text("Mathematical Expression Debate Calculator", color=(100, 150, 255))
            dpg.add_text("Terrence (GPT-5) vs Neil (Claude 3.7 Sonnet)", color=(150, 150, 150))
            dpg.add_separator()
            
            # Input section
            with dpg.group(horizontal=True):
                dpg.add_text("Expression:")
                self.expression_input = dpg.add_input_text(
                    default_value="1 + 1",
                    width=300,
                    hint="Enter mathematical expression"
                )
            
            # Pace selection
            with dpg.group(horizontal=True):
                dpg.add_text("Pace:")
                self.pace_selector = dpg.add_combo(
                    items=["slow", "medium", "fast"],
                    default_value=settings.default_pace_mode,
                    width=100
                )
            
            # Control buttons
            with dpg.group(horizontal=True):
                self.start_button = dpg.add_button(
                    label="Start Debate",
                    callback=self._start_debate,
                    width=120
                )
                dpg.add_button(
                    label="Clear",
                    callback=self._clear_transcript,
                    width=80
                )
            
            dpg.add_separator()
            
            # Status section
            with dpg.group(horizontal=True):
                dpg.add_text("Status:")
                self.status_text = dpg.add_text("Ready", color=(100, 255, 100))
                
                # Spinner for thinking indicator
                self.spinner = dpg.add_loading_indicator(
                    style=1,
                    radius=10,
                    thickness=3,
                    show=False
                )
            
            # Progress section
            with dpg.group(horizontal=True):
                dpg.add_text("Progress:")
                self.progress_bar = dpg.add_progress_bar(
                    default_value=0.0,
                    width=200
                )
                dpg.add_text("Round: 0/12", tag="round_counter")
                dpg.add_text("Time: 0s", tag="time_counter")
            
            dpg.add_separator()
            
            # Transcript section
            dpg.add_text("Debate Transcript:", color=(200, 200, 100))
            self.transcript_text = dpg.add_input_text(
                multiline=True,
                readonly=True,
                width=-1,
                height=300,
                default_value="Debate transcript will appear here...\n"
            )
            
            # Final answer section
            dpg.add_text("Final Answer:", color=(100, 255, 100))
            self.final_answer_text = dpg.add_input_text(
                readonly=True,
                width=-1,
                default_value="",
                hint="Final answer will appear here after agreement"
            )
        
        # Setup viewport
        dpg.create_viewport(
            title="Debate Calculator",
            width=800,
            height=700,
            resizable=True
        )
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        
        # Start message processing
        self._start_message_processor()
    
    def _setup_theme(self) -> None:
        """Setup GUI theme and styling."""
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 5, category=dpg.mvThemeCat_Core)
        
        dpg.bind_theme(global_theme)
    
    def _start_message_processor(self) -> None:
        """Start the message processing thread for UI updates."""
        def process_messages():
            while True:
                try:
                    # Process typing effects
                    try:
                        while True:
                            char = self.typing_queue.get_nowait()
                            current_text = dpg.get_value(self.transcript_text)
                            dpg.set_value(self.transcript_text, current_text + char)
                    except queue.Empty:
                        pass
                    
                    # Process status messages
                    try:
                        while True:
                            message = self.message_queue.get_nowait()
                            self._handle_message(message)
                    except queue.Empty:
                        pass
                    
                    time.sleep(0.05)  # 20 FPS update rate
                    
                except Exception as e:
                    print(f"Message processor error: {e}")
        
        processor_thread = threading.Thread(target=process_messages, daemon=True)
        processor_thread.start()
    
    def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle different types of messages from the debate thread."""
        msg_type = message.get("type")
        
        if msg_type == "status":
            dpg.set_value(self.status_text, message["text"])
            color = message.get("color", (255, 255, 255))
            dpg.configure_item(self.status_text, color=color)
            
            # Show/hide spinner based on status
            if "thinking" in message["text"].lower():
                dpg.configure_item(self.spinner, show=True)
            else:
                dpg.configure_item(self.spinner, show=False)
        
        elif msg_type == "progress":
            progress = message.get("progress", 0.0)
            dpg.set_value(self.progress_bar, progress)
        
        elif msg_type == "round_update":
            round_num = message.get("round", 0)
            max_rounds = message.get("max_rounds", 12)
            dpg.set_value("round_counter", f"Round: {round_num}/{max_rounds}")
        
        elif msg_type == "time_update":
            elapsed = message.get("elapsed", 0.0)
            dpg.set_value("time_counter", f"Time: {elapsed:.1f}s")
        
        elif msg_type == "turn_start":
            speaker = message.get("speaker", "")
            self._add_turn_header(speaker)
        
        elif msg_type == "turn_content":
            content = message.get("content", "")
            self._add_typing_content(content)
        
        elif msg_type == "final_answer":
            answer = message.get("answer", "")
            dpg.set_value(self.final_answer_text, answer)
            dpg.configure_item(self.final_answer_text, color=(100, 255, 100))
        
        elif msg_type == "debate_complete":
            self._on_debate_complete(message.get("result"))
    
    def _add_turn_header(self, speaker: str) -> None:
        """Add a speaker header to the transcript."""
        current_text = dpg.get_value(self.transcript_text)
        header = f"\n{'='*20} {speaker} {'='*20}\n"
        dpg.set_value(self.transcript_text, current_text + header)
    
    def _add_typing_content(self, content: str) -> None:
        """Add content with typing effect."""
        # Get current pace for typing rate
        pace = dpg.get_value(self.pace_selector)
        pacing_profile = settings.get_pacing_profile(pace)
        
        # Calculate delay between characters
        char_delay = 1.0 / pacing_profile.typeout_rate_chars_per_sec
        
        # Queue characters for typing effect
        for char in content:
            self.typing_queue.put(char)
            time.sleep(char_delay)
        
        # Add newline at end
        self.typing_queue.put("\n")
    
    def _start_debate(self) -> None:
        """Start a new debate in a background thread."""
        if self.debate_active:
            return
        
        expression = dpg.get_value(self.expression_input).strip()
        if not expression:
            self._send_message("status", "Please enter a mathematical expression", (255, 100, 100))
            return
        
        pace = dpg.get_value(self.pace_selector)
        
        # Update UI state
        self.debate_active = True
        dpg.configure_item(self.start_button, enabled=False, label="Debating...")
        self._clear_transcript()
        dpg.set_value(self.final_answer_text, "")
        self.start_time = time.time()
        
        # Start debate thread
        self.current_debate = threading.Thread(
            target=self._run_debate_thread,
            args=(expression, pace),
            daemon=True
        )
        self.current_debate.start()
        
        # Start time updater
        self._start_time_updater()
    
    def _run_debate_thread(self, expression: str, pace: PaceMode) -> None:
        """Run the debate in a background thread."""
        try:
            self._send_message("status", "Initializing debate...", (100, 150, 255))

            # Create async event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Create a custom progress callback that handles turn display
                async def enhanced_progress_callback(status: str):
                    self._debate_progress_callback(status)

                    # Check if this is a turn completion and display content
                    if hasattr(self.orchestrator, '_current_turn_content'):
                        content = self.orchestrator._current_turn_content
                        speaker = self.orchestrator._current_speaker

                        if content and speaker:
                            self._send_message("turn_start", speaker=speaker)
                            await self._async_typing_effect(content, pace)

                            # Clear the temporary content
                            self.orchestrator._current_turn_content = None
                            self.orchestrator._current_speaker = None

                result = loop.run_until_complete(
                    self._run_enhanced_debate(expression, pace, enhanced_progress_callback)
                )

                self._send_message("debate_complete", result=result)

            finally:
                loop.close()

        except Exception as e:
            self._send_message("status", f"Error: {e}", (255, 100, 100))
            self._on_debate_complete(None)

    async def _run_enhanced_debate(self, expression: str, pace: PaceMode, progress_callback) -> DebateResult:
        """Enhanced debate runner with turn-by-turn display."""
        pacing_profile = settings.get_pacing_profile(pace)
        pace_controller = PaceController(pacing_profile)

        result = await self.orchestrator.debate(
            expression=expression,
            pace=pace,
            progress_callback=lambda status: asyncio.create_task(progress_callback(status))
        )

        # Display turns as they complete
        for i, turn in enumerate(result.turns):
            self._send_message("turn_start", speaker=turn.speaker)
            await self._async_typing_effect(turn.content, pace)

            # Update round counter
            round_num = (i // 2) + 1
            self._send_message("round_update", round=round_num, max_rounds=settings.max_rounds)

            # Update progress
            progress = (i + 1) / len(result.turns)
            self._send_message("progress", progress=progress)

            # Small delay between turns for visual separation
            await asyncio.sleep(0.5)

        return result

    async def _async_typing_effect(self, content: str, pace: PaceMode) -> None:
        """Async typing effect for smooth character-by-character display."""
        pacing_profile = settings.get_pacing_profile(pace)
        char_delay = 1.0 / pacing_profile.typeout_rate_chars_per_sec

        for char in content:
            self.typing_queue.put(char)
            await asyncio.sleep(char_delay)

        # Add newlines for separation
        self.typing_queue.put("\n\n")
    
    def _debate_progress_callback(self, status: str) -> None:
        """Callback for debate progress updates."""
        color = (255, 255, 100) if "thinking" in status.lower() else (100, 255, 100)
        self._send_message("status", status, color)
    
    def _start_time_updater(self) -> None:
        """Start the time counter updater."""
        def update_time():
            while self.debate_active:
                elapsed = time.time() - self.start_time
                self._send_message("time_update", elapsed=elapsed)
                time.sleep(0.1)
        
        timer_thread = threading.Thread(target=update_time, daemon=True)
        timer_thread.start()
    
    def _send_message(self, msg_type: str, **kwargs) -> None:
        """Send a message to the UI thread."""
        message = {"type": msg_type, **kwargs}
        self.message_queue.put(message)
    
    def _clear_transcript(self) -> None:
        """Clear the debate transcript."""
        dpg.set_value(self.transcript_text, "")
        dpg.set_value(self.final_answer_text, "")
        dpg.set_value(self.progress_bar, 0.0)
        dpg.set_value("round_counter", "Round: 0/12")
        dpg.set_value("time_counter", "Time: 0s")
    
    def _on_debate_complete(self, result: Optional[DebateResult]) -> None:
        """Handle debate completion."""
        self.debate_active = False
        dpg.configure_item(self.start_button, enabled=True, label="Start Debate")
        dpg.configure_item(self.spinner, show=False)
        
        if result:
            # Update final status
            if result.status == DebateStatus.COMPLETED:
                self._send_message("status", "Debate completed successfully!", (100, 255, 100))
                if result.final_answer:
                    self._send_message("final_answer", answer=result.final_answer)
            elif result.status == DebateStatus.TIMEOUT:
                self._send_message("status", "Debate timed out", (255, 255, 100))
            else:
                self._send_message("status", f"Debate failed: {result.error_message}", (255, 100, 100))
            
            # Update progress
            self._send_message("progress", progress=1.0)
            self._send_message("round_update", round=result.rounds, max_rounds=settings.max_rounds)
        else:
            self._send_message("status", "Debate failed", (255, 100, 100))
    
    def run(self) -> None:
        """Run the GUI application."""
        try:
            dpg.start_dearpygui()
        except KeyboardInterrupt:
            print("Application interrupted by user")
        finally:
            dpg.destroy_context()


def main() -> None:
    """Main entry point for the GUI application."""
    if not DEARPYGUI_AVAILABLE:
        print("❌ DearPyGui not available - GUI interface disabled")
        print("\n🔧 To enable GUI:")
        print("   1. Run the fix script: .\\fix_dearpygui.ps1")
        print("   2. Install Visual C++ Redistributable")
        print("   3. Try: pip uninstall dearpygui && pip install dearpygui")
        print("   4. Consider using Python 3.11/3.12 instead of 3.13")
        print("\n✅ Use CLI interface instead:")
        print("   python -m debate_calc.app.ui_cli")
        sys.exit(1)

    try:
        app = DebateGUI()
        app.run()
    except ImportError as e:
        print(f"❌ GUI dependencies not available: {e}")
        print("\n🔧 To fix this issue:")
        print("   1. Run: .\\fix_dearpygui.ps1")
        print("   2. Install Visual C++ Redistributable")
        print("   3. Use CLI instead: python -m debate_calc.app.ui_cli")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start GUI application: {e}")
        print("Please ensure DearPyGui is properly installed and API keys are configured.")
        print("Alternative: Use CLI interface with: python -m debate_calc.app.ui_cli")
        sys.exit(1)


if __name__ == "__main__":
    main()
