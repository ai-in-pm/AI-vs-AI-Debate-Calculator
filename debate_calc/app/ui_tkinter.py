"""
Tkinter GUI interface for the Debate Calculator (fallback for DearPyGui issues).
Simple but functional GUI using Python's built-in tkinter.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
from typing import Optional

try:
    from .settings import settings, PaceMode
    from .orchestrator import DebateOrchestrator, DebateStatus, DebateResult
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from debate_calc.app.settings import settings, PaceMode
    from debate_calc.app.orchestrator import DebateOrchestrator, DebateStatus, DebateResult


class TkinterDebateGUI:
    """Simple Tkinter-based GUI for the Debate Calculator."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI vs AI Debate Calculator")
        self.root.geometry("800x600")
        
        self.orchestrator = DebateOrchestrator()
        self.debate_active = False
        self.message_queue = queue.Queue()
        
        self._setup_gui()
        self._start_message_processor()
    
    def _setup_gui(self):
        """Setup the GUI layout."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="AI vs AI Mathematical Debate Calculator", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="Terrence (GPT-5) vs Neil (Claude 3.7 Sonnet)")
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # Input section
        ttk.Label(main_frame, text="Expression:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.expression_var = tk.StringVar(value="1 + 1")
        self.expression_entry = ttk.Entry(main_frame, textvariable=self.expression_var, width=40)
        self.expression_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Pace selection
        ttk.Label(main_frame, text="Pace:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5))
        self.pace_var = tk.StringVar(value=settings.default_pace_mode)
        pace_combo = ttk.Combobox(main_frame, textvariable=self.pace_var, 
                                 values=["slow", "medium", "fast"], state="readonly", width=10)
        pace_combo.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=2, sticky=tk.E, pady=(5, 0))
        
        self.start_button = ttk.Button(button_frame, text="Start Debate", command=self._start_debate)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_button = ttk.Button(button_frame, text="Clear", command=self._clear_transcript)
        clear_button.pack(side=tk.LEFT)
        
        # Status section
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 10))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky=tk.W)
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="green")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Progress bar
        ttk.Label(status_frame, text="Progress:").grid(row=1, column=0, sticky=tk.W)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=(5, 0))
        
        # Round and time info
        info_frame = ttk.Frame(status_frame)
        info_frame.grid(row=1, column=2, sticky=tk.E, padx=(10, 0))
        
        self.round_var = tk.StringVar(value="Round: 0/12")
        ttk.Label(info_frame, textvariable=self.round_var).pack(side=tk.LEFT, padx=(0, 10))
        
        self.time_var = tk.StringVar(value="Time: 0s")
        ttk.Label(info_frame, textvariable=self.time_var).pack(side=tk.LEFT)
        
        # Transcript section
        transcript_frame = ttk.LabelFrame(main_frame, text="Debate Transcript", padding="5")
        transcript_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        transcript_frame.columnconfigure(0, weight=1)
        transcript_frame.rowconfigure(0, weight=1)
        
        self.transcript_text = scrolledtext.ScrolledText(transcript_frame, wrap=tk.WORD, height=15)
        self.transcript_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.transcript_text.insert(tk.END, "Debate transcript will appear here...\n")
        self.transcript_text.config(state=tk.DISABLED)
        
        # Final answer section
        answer_frame = ttk.LabelFrame(main_frame, text="Final Answer", padding="5")
        answer_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        answer_frame.columnconfigure(0, weight=1)
        
        self.answer_var = tk.StringVar()
        answer_entry = ttk.Entry(answer_frame, textvariable=self.answer_var, state="readonly", 
                                font=("Arial", 12, "bold"))
        answer_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    def _start_message_processor(self):
        """Start the message processing loop."""
        def process_messages():
            try:
                while True:
                    message = self.message_queue.get_nowait()
                    self._handle_message(message)
            except queue.Empty:
                pass
            
            # Schedule next check
            self.root.after(50, process_messages)
        
        process_messages()
    
    def _handle_message(self, message):
        """Handle messages from the debate thread."""
        msg_type = message.get("type")
        
        if msg_type == "status":
            self.status_var.set(message["text"])
            color = "red" if "error" in message["text"].lower() else "green"
            self.status_label.config(foreground=color)
        
        elif msg_type == "progress":
            self.progress_var.set(message.get("progress", 0) * 100)
        
        elif msg_type == "round_update":
            round_num = message.get("round", 0)
            max_rounds = message.get("max_rounds", 12)
            self.round_var.set(f"Round: {round_num}/{max_rounds}")
        
        elif msg_type == "time_update":
            elapsed = message.get("elapsed", 0.0)
            self.time_var.set(f"Time: {elapsed:.1f}s")
        
        elif msg_type == "transcript_append":
            content = message.get("content", "")
            self.transcript_text.config(state=tk.NORMAL)
            self.transcript_text.insert(tk.END, content)
            self.transcript_text.see(tk.END)
            self.transcript_text.config(state=tk.DISABLED)
        
        elif msg_type == "final_answer":
            self.answer_var.set(message.get("answer", ""))
        
        elif msg_type == "debate_complete":
            self._on_debate_complete(message.get("result"))
    
    def _start_debate(self):
        """Start a new debate."""
        if self.debate_active:
            return
        
        expression = self.expression_var.get().strip()
        if not expression:
            messagebox.showerror("Error", "Please enter a mathematical expression")
            return
        
        pace = self.pace_var.get()
        
        # Update UI state
        self.debate_active = True
        self.start_button.config(state="disabled", text="Debating...")
        self._clear_transcript()
        self.answer_var.set("")
        self.start_time = time.time()
        
        # Start debate thread
        debate_thread = threading.Thread(
            target=self._run_debate_thread,
            args=(expression, pace),
            daemon=True
        )
        debate_thread.start()
        
        # Start time updater
        self._start_time_updater()
    
    def _run_debate_thread(self, expression: str, pace: PaceMode):
        """Run the debate in a background thread."""
        try:
            self._send_message("status", text="Initializing debate...")
            
            result = self.orchestrator.debate_sync(
                expression=expression,
                pace=pace,
                progress_callback=self._debate_progress_callback
            )
            
            # Display the debate turns
            for i, turn in enumerate(result.turns):
                header = f"\n{'='*20} {turn.speaker} {'='*20}\n"
                self._send_message("transcript_append", content=header)
                self._send_message("transcript_append", content=turn.content + "\n")
                
                if turn.agreement_flag is not None:
                    agreement_text = f"[AGREES: {turn.agreement_flag}]\n"
                    self._send_message("transcript_append", content=agreement_text)
                
                # Update progress
                progress = (i + 1) / len(result.turns)
                self._send_message("progress", progress=progress)
                
                # Update round counter
                round_num = (i // 2) + 1
                self._send_message("round_update", round=round_num, max_rounds=settings.max_rounds)
            
            self._send_message("debate_complete", result=result)
            
        except Exception as e:
            self._send_message("status", text=f"Error: {e}")
            self._on_debate_complete(None)
    
    def _debate_progress_callback(self, status: str):
        """Callback for debate progress updates."""
        self._send_message("status", text=status)
    
    def _start_time_updater(self):
        """Start the time counter updater."""
        def update_time():
            if self.debate_active:
                elapsed = time.time() - self.start_time
                self._send_message("time_update", elapsed=elapsed)
                self.root.after(100, update_time)
        
        update_time()
    
    def _send_message(self, msg_type: str, **kwargs):
        """Send a message to the UI thread."""
        message = {"type": msg_type, **kwargs}
        self.message_queue.put(message)
    
    def _clear_transcript(self):
        """Clear the debate transcript."""
        self.transcript_text.config(state=tk.NORMAL)
        self.transcript_text.delete(1.0, tk.END)
        self.transcript_text.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.round_var.set("Round: 0/12")
        self.time_var.set("Time: 0s")
    
    def _on_debate_complete(self, result: Optional[DebateResult]):
        """Handle debate completion."""
        self.debate_active = False
        self.start_button.config(state="normal", text="Start Debate")
        
        if result:
            if result.status == DebateStatus.COMPLETED:
                self._send_message("status", text="Debate completed successfully!")
                if result.final_answer:
                    self._send_message("final_answer", answer=result.final_answer)
            elif result.status == DebateStatus.TIMEOUT:
                self._send_message("status", text="Debate timed out")
            else:
                self._send_message("status", text=f"Debate failed: {result.error_message}")
            
            self._send_message("progress", progress=1.0)
        else:
            self._send_message("status", text="Debate failed")
    
    def run(self):
        """Run the GUI application."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Application interrupted by user")


def main():
    """Main entry point for the Tkinter GUI."""
    try:
        app = TkinterDebateGUI()
        app.run()
    except Exception as e:
        print(f"Failed to start Tkinter GUI: {e}")
        print("Please ensure your API keys are configured in .env")
        print("Alternative: Use CLI interface with: python -m debate_calc.app.ui_cli")


if __name__ == "__main__":
    main()
