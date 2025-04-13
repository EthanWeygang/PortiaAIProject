import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from dotenv import load_dotenv
from portia import (
    Config,
    MultipleChoiceClarification,
    Portia,
    PlanRunState,
    default_config,
)
from portia.config import LLMModel
from portia import MultipleChoiceClarification
import json
import speech_recognition as sr
import threading

class PortiaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Day Planner with Portia")
        self.root.geometry("800x180")  # Slightly increased height for new button
        self.constraints = []
        self.plan = None
        self.plan_run = None
        self.portia = None
        
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.listen_thread = None
        
        self.create_widgets()
        
        load_dotenv(override=True)

        self.init_portia()

    def create_widgets(self):
        # Input frame
        input_frame = ttk.LabelFrame(self.root, text="Inputs")
        input_frame.pack(fill="x", padx=10, pady=10)
        
        # Day input
        ttk.Label(input_frame, text="Enter day:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.day_entry = ttk.Entry(input_frame, width=30)
        self.day_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Events input
        ttk.Label(input_frame, text="Enter events:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.events_entry = ttk.Entry(input_frame, width=50)
        self.events_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Voice input button
        self.voice_btn = ttk.Button(input_frame, text="Toggle Voice Input", command=self.toggle_listening)
        self.voice_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Generate plan button
        self.generate_btn = ttk.Button(input_frame, text="Generate Plan", command=self.generate_plan)
        self.generate_btn.grid(row=2, column=0, columnspan=3, padx=5, pady=10)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def toggle_listening(self):
        if self.is_listening:
            # Stop listening
            self.is_listening = False
            self.voice_btn.config(text="🎤 Voice Input")
            self.status_var.set("Voice input stopped")
        else:
            # Start listening
            self.is_listening = True
            self.voice_btn.config(text="⏹️ Stop Listening")
            self.status_var.set("Listening... speak now")
            
            # Start listening in a separate thread to keep the UI responsive
            self.listen_thread = threading.Thread(target=self.listen_continuous)
            self.listen_thread.daemon = True
            self.listen_thread.start()

    def listen_continuous(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            
            while self.is_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)
                    try:
                        text = self.recognizer.recognize_google(audio)
                        # Use after method to safely update UI from a different thread
                        self.root.after(0, lambda t=text: self.update_events_entry(t))
                    except sr.UnknownValueError:
                        pass  # Silently ignore when no speech is detected
                    except sr.RequestError as e:
                        self.root.after(0, lambda e=e: self.status_var.set(f"Could not request results: {e}"))
                except Exception as e:
                    if self.is_listening:  # Only show error if still supposed to be listening
                        self.root.after(0, lambda e=e: self.status_var.set(f"Error: {e}"))

    def update_events_entry(self, text):
        current_text = self.events_entry.get()
        if current_text:
            # If there's already text, add a comma and space before the new text
            self.events_entry.delete(0, tk.END)
            self.events_entry.insert(0, f"{current_text}, {text}")
        else:
            self.events_entry.insert(0, text)
        self.status_var.set(f"Added: {text}")

    def init_portia(self):
        my_config = Config.from_default(
            models={
                "planning_default_model_name": LLMModel.GPT_4_O,
                "default_model_name": LLMModel.GPT_4_O
            }
        )
        self.portia = Portia(config=my_config)

    def generate_plan(self):
        day = self.day_entry.get()
        prompt = self.events_entry.get()
        
        if not day or not prompt:
            messagebox.showerror("Input Error", "Please enter both day and events")
            return
        
        self.status_var.set("Planning your day... Please wait.")
        self.root.update()
        
        task_lambda = lambda: f"""
        I am going to provide you with a list of events I want to do on that day and I would like you to add them to my google calendar. 
        Plan my events on this specific day: {day}.
        
        Make sure to schedule the events in a way that makes sense and is efficient.
        Ensuring you take into account the following constraints ({"".join(self.constraints)}), do the following:
        - Add the following events to my google calendar: {prompt}
        - Make the description of the event "Generated by Portia"
        - Leave the attendee list empty
        """
        
        self.plan = self.portia.plan(task_lambda())
        
        # Show plan popup
        self.show_plan_popup()
        
        self.status_var.set("Plan generated. Please provide feedback.")

    def show_plan_popup(self):
        # Create popup for the plan
        plan_popup = tk.Toplevel(self.root)
        plan_popup.title("Generated Plan")
        plan_popup.geometry("800x600")
        plan_popup.transient(self.root)
        plan_popup.grab_set()
        
        plan_output = scrolledtext.ScrolledText(plan_popup, wrap=tk.WORD, height=20)
        plan_output.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Display the plan
        for step in self.plan.steps:
            plan_output.insert(tk.END, json.dumps(step.model_dump(), indent=2) + "\n\n")
        
        # Buttons frame
        btn_frame = ttk.Frame(plan_popup)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        # Accept button
        accept_btn = ttk.Button(btn_frame, text="Accept Plan", 
                               command=lambda: [plan_popup.destroy(), self.execute_plan()])
        accept_btn.pack(side=tk.LEFT, padx=5)
        
        # Modify button
        modify_btn = ttk.Button(btn_frame, text="Modify Plan", 
                               command=lambda: [plan_popup.destroy(), self.show_feedback_popup()])
        modify_btn.pack(side=tk.RIGHT, padx=5)

    def show_feedback_popup(self):
        # Create popup for feedback
        feedback_popup = tk.Toplevel(self.root)
        feedback_popup.title("Modify Plan")
        feedback_popup.geometry("600x200")
        feedback_popup.transient(self.root)
        feedback_popup.grab_set()
        
        # Guidance input
        ttk.Label(feedback_popup, text="Additional guidance:", 
                 wraplength=550).pack(padx=10, pady=10, anchor="w")
        
        guidance_entry = ttk.Entry(feedback_popup, width=60)
        guidance_entry.pack(fill="x", padx=10, pady=5)
        guidance_entry.focus_set()
        
        # Submit button
        def submit_guidance():
            guidance = guidance_entry.get()
            if not guidance:
                messagebox.showerror("Guidance Error", "Please provide additional guidance", parent=feedback_popup)
                return
            
            self.constraints.append(guidance)
            feedback_popup.destroy()
            self.generate_plan()
        
        submit_btn = ttk.Button(feedback_popup, text="Submit Feedback", command=submit_guidance)
        submit_btn.pack(pady=20)

    def execute_plan(self):
        if not self.plan:
            messagebox.showerror("Plan Error", "No plan to execute")
            return
        
        self.status_var.set("Executing plan... Please wait.")
        self.root.update()
        
        self.plan_run = self.portia.run_plan(self.plan)
        
        self.handle_clarifications()
        
        self.status_var.set("Plan executed successfully.")
        messagebox.showinfo("Success", "Plan has been executed successfully!")

    def handle_clarifications(self):
        while self.plan_run and self.plan_run.state == PlanRunState.NEED_CLARIFICATION:
            for clarification in self.plan_run.get_outstanding_clarifications():
                # Create dialog for clarification
                dialog = tk.Toplevel(self.root)
                dialog.title("Clarification Needed")
                dialog.geometry("500x300")
                dialog.transient(self.root)
                dialog.grab_set()
                
                ttk.Label(dialog, text=clarification.user_guidance, wraplength=450).pack(padx=10, pady=10)
                
                if isinstance(clarification, MultipleChoiceClarification):
                    choice_var = tk.StringVar()
                    for option in clarification.options:
                        ttk.Radiobutton(dialog, text=option, variable=choice_var, value=option).pack(anchor=tk.W, padx=20)
                    
                    def submit_choice():
                        self.plan_run = self.portia.resolve_clarification(clarification, choice_var.get(), self.plan_run)
                        dialog.destroy()
                    
                    ttk.Button(dialog, text="Submit", command=submit_choice).pack(pady=20)
                else:
                    input_var = tk.StringVar()
                    ttk.Entry(dialog, textvariable=input_var, width=50).pack(padx=10, pady=10)
                    
                    def submit_input():
                        self.plan_run = self.portia.resolve_clarification(clarification, input_var.get(), self.plan_run)
                        dialog.destroy()
                    
                    ttk.Button(dialog, text="Submit", command=submit_input).pack(pady=20)
                
                self.root.wait_window(dialog)
            
            # Resume plan execution
            self.plan_run = self.portia.run(self.plan_run)

if __name__ == "__main__":
    root = tk.Tk()
    app = PortiaGUI(root)
    root.mainloop()