import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import sys
import os
import json
import pandas as pd
from PIL import Image, ImageTk

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import process_user_request

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Statistical Analysis Tool")
        self.geometry("1200x800")

        self.selected_file_path = ""
        self.conversation_history = []
        self.image_reference = None

        # --- Main Layout (3 columns) ---
        self.main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_paned_window.pack(fill=tk.BOTH, expand=True)

        # -- Left Pane: Data Preview --
        self.left_frame = ttk.Frame(self.main_paned_window)
        self.main_paned_window.add(self.left_frame, weight=1) # Equal weight
        self.data_preview_frame = ttk.Frame(self.left_frame)
        self.data_preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.data_preview_tree = ttk.Treeview(self.data_preview_frame, show="headings")
        vsb = ttk.Scrollbar(self.data_preview_frame, orient="vertical", command=self.data_preview_tree.yview)
        hsb = ttk.Scrollbar(self.data_preview_frame, orient="horizontal", command=self.data_preview_tree.xview)
        self.data_preview_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.data_preview_tree.pack(fill=tk.BOTH, expand=True)

        # -- Middle Pane: Conversation & Code --
        self.middle_frame = ttk.Frame(self.main_paned_window)
        self.main_paned_window.add(self.middle_frame, weight=1) # Equal weight
        self.middle_paned_window = ttk.PanedWindow(self.middle_frame, orient=tk.VERTICAL)
        self.middle_paned_window.pack(fill=tk.BOTH, expand=True)
        self.conversation_frame = ttk.Frame(self.middle_paned_window)
        self.conversation_text = scrolledtext.ScrolledText(self.conversation_frame, wrap=tk.WORD, state='disabled', padx=5, pady=5)
        self.conversation_text.pack(fill=tk.BOTH, expand=True)
        self.middle_paned_window.add(self.conversation_frame, weight=3)
        self.code_frame = ttk.Frame(self.middle_paned_window)
        self.code_text = scrolledtext.ScrolledText(self.code_frame, wrap=tk.WORD, state='disabled', height=10, bg="#2d2d2d", fg="#cccccc")
        self.code_text.pack(fill=tk.BOTH, expand=True)
        self.middle_paned_window.add(self.code_frame, weight=1)
        self.prompt_frame = ttk.Frame(self.middle_frame)
        self.prompt_frame.pack(fill=tk.X, padx=10, pady=5)
        self.prompt_entry = ttk.Entry(self.prompt_frame)
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_send = ttk.Button(self.prompt_frame, text="Send", command=self.send_message_threaded)
        self.btn_send.pack(side=tk.LEFT, padx=(5, 0))
        self.prompt_entry.bind("<Return>", self.send_message_threaded)

        # -- Right Pane: Outputs --
        self.right_frame = ttk.Frame(self.main_paned_window)
        self.main_paned_window.add(self.right_frame, weight=1) # Equal weight
        self.right_paned_window = ttk.PanedWindow(self.right_frame, orient=tk.VERTICAL)
        self.right_paned_window.pack(fill=tk.BOTH, expand=True)
        self.image_frame = ttk.Frame(self.right_paned_window)
        self.lbl_image = ttk.Label(self.image_frame, text="Generated plot appears here.", anchor=tk.CENTER)
        self.lbl_image.pack(fill=tk.BOTH, expand=True)
        self.right_paned_window.add(self.image_frame, weight=2)
        self.console_frame = ttk.Frame(self.right_paned_window)
        self.console_text = scrolledtext.ScrolledText(self.console_frame, wrap=tk.WORD, state='disabled', height=10, bg="#2b2b2b", fg="#d3d3d3")
        self.console_text.pack(fill=tk.BOTH, expand=True)
        self.right_paned_window.add(self.console_frame, weight=1)

        self.create_menu()

    def create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open CSV/Excel...", command=self.select_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=(("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")))
        if not path: return
        self.selected_file_path = path
        self.title(f"Statistical Analysis Tool - {os.path.basename(path)}")
        self.conversation_history = []
        self.update_conversation_display("System", f"File selected: {os.path.basename(path)}. You can now start the analysis.")
        self.display_data_preview(path)

    def display_data_preview(self, file_path):
        try:
            for i in self.data_preview_tree.get_children(): self.data_preview_tree.delete(i)
            self.data_preview_tree["columns"] = ()
            if file_path.endswith('.csv'): df = pd.read_csv(file_path, nrows=50)
            elif file_path.endswith('.xlsx'): df = pd.read_excel(file_path, engine='openpyxl', nrows=50)
            else: self.update_conversation_display("Error", "Unsupported file type for preview."); return
            self.data_preview_tree["columns"] = list(df.columns)
            for col in df.columns: self.data_preview_tree.heading(col, text=col); self.data_preview_tree.column(col, width=100, anchor='w')
            for index, row in df.iterrows(): self.data_preview_tree.insert("", "end", values=list(row))
        except Exception as e: self.update_conversation_display("Error", f"Failed to preview data: {e}")

    def send_message_threaded(self, event=None):
        user_prompt = self.prompt_entry.get()
        if not user_prompt: return
        if not self.selected_file_path: self.update_conversation_display("Error", "Please select a file first."); return
        self.prompt_entry.delete(0, tk.END)
        self.update_conversation_display("You", user_prompt)
        self.update_code_view("")
        self.conversation_history.append({"role": "user", "content": user_prompt})
        self.btn_send.config(state='disabled')
        threading.Thread(target=self.run_analysis_logic, args=(user_prompt,)).start()

    def run_analysis_logic(self, user_prompt):
        result = process_user_request(user_prompt, self.selected_file_path, self.conversation_history)
        self.after(0, self.finalize_analysis, result)

    def finalize_analysis(self, result):
        self.btn_send.config(state='normal')
        if error := result.get("error"): self.update_conversation_display("Error", error); return
        self.conversation_history.append({"role": "assistant", "content": result['llm_response']})
        self.update_conversation_display("Assistant", f"**Reasoning:**\n{result['llm_reasoning']}\n\n**Response:**\n{result['llm_response']}")
        self.update_code_view(result.get("r_code", ""))
        self.update_console(result.get("r_stdout"), result.get("r_stderr"))
        if artifact_path := result.get("artifact_path"): 
            if os.path.exists(artifact_path): self.show_image(artifact_path)
        else: self.clear_image()

    def update_conversation_display(self, speaker, text):
        self.conversation_text.config(state='normal')
        self.conversation_text.insert(tk.END, f"--- {speaker} ---\n{text}\n\n")
        self.conversation_text.config(state='disabled')
        self.conversation_text.see(tk.END)

    def update_console(self, stdout, stderr):
        self.console_text.config(state='normal')
        self.console_text.delete('1.0', tk.END)
        if stderr: self.console_text.insert(tk.END, f"--- R SCRIPT ERROR ---\n{stderr}")
        elif stdout: self.console_text.insert(tk.END, f"--- R SCRIPT OUTPUT ---\n{stdout}")
        self.console_text.config(state='disabled')

    def update_code_view(self, code):
        self.code_text.config(state='normal')
        self.code_text.delete('1.0', tk.END)
        if code: self.code_text.insert(tk.END, "--- Generated R Code ---\\n" + code)
        self.code_text.config(state='disabled')

    def show_image(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((self.image_frame.winfo_width(), self.image_frame.winfo_height()), Image.Resampling.LANCZOS)
            self.image_reference = ImageTk.PhotoImage(img)
            self.lbl_image.config(image=self.image_reference, text="")
        except Exception as e: self.update_console(None, f"Failed to display image: {e}")

    def clear_image(self):
        self.lbl_image.config(image='', text="Generated plot appears here.")
        self.image_reference = None

if __name__ == "__main__":
    app = App()
    app.mainloop()