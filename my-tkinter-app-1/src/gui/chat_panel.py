from tkinter import Frame, Label, Text, Scrollbar, Entry, Button, END
from tkinter.ttk import Progressbar

def get_system_font():
    import platform
    system = platform.system()
    if system == "Windows":
        return "Segoe UI"
    elif system == "Darwin":
        return "SF Pro Display"
    else:
        return "Liberation Sans"

def get_monospace_font():
    import platform
    system = platform.system()
    if system == "Windows":
        return "Consolas"
    elif system == "Darwin":
        return "SF Mono"
    else:
        return "Liberation Mono"

class ChatPanel:
    def __init__(self, master, on_send_callback):
        self.master = master
        self.on_send_callback = on_send_callback
        self.frame = None
        self.chat_text = None
        self.user_entry = None
        self.send_button = None
        self.settings_button = None
        self.scrollbar = None
        self.progress = None

    def build(self):
        margin_top = 40
        margin_bottom = 24
        margin_right = 32
        margin_left = 32
        self.frame = Frame(self.master, bg="#23272f")
        self.frame.place(x=margin_left, y=margin_top, relwidth=1, relheight=1, height=-(margin_top+margin_bottom), width=-(margin_left+margin_right))
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.chat_label = Label(self.master, text="Proposition d'organisation :", font=(get_system_font(), 12, "bold"), fg="#fff", bg="#23272f")
        self.chat_label.pack(padx=18, anchor="w")
        self.progress = Progressbar(self.frame, orient="horizontal", mode="determinate", length=200)
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.progress['value'] = 0
        chat_frame = Frame(self.frame, bg="#23272f")
        chat_frame.grid(row=1, column=0, sticky="nsew")
        self.chat_text = Text(chat_frame, font=(get_monospace_font(), 11), bg="#181a20", fg="#e0e0e0", relief="flat", wrap="word", state="disabled", borderwidth=0, highlightthickness=1, highlightbackground="#444")
        self.chat_text.pack(side="left", fill="both", expand=True)
        self.scrollbar = Scrollbar(chat_frame, command=self.chat_text.yview, bg="#23272f", troughcolor="#23272f", bd=0, relief="flat")
        self.scrollbar.pack(side='right', fill='y')
        self.chat_text.config(yscrollcommand=self.scrollbar.set)
        input_frame = Frame(self.frame, bg="#23272f")
        input_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.user_entry = Entry(input_frame, font=(get_system_font(), 11), bg="#23272f", fg="#fff", insertbackground="#fff", relief="flat", width=32)
        self.user_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.send_button = Button(input_frame, text="Envoyer", font=(get_system_font(), 10, "bold"), bg="#FFD700", fg="#23272f", relief="flat", command=self.on_send)
        self.send_button.pack(side="right")

    def on_send(self):
        user_text = self.user_entry.get().strip()
        if not user_text:
            return
        self.chat_text.config(state="normal")
        self.chat_text.insert(END, f"\nVous : {user_text}\n", ("user",))
        self.chat_text.tag_config("user", foreground="#7CFC00", font=(get_system_font(), 10, "bold"))
        self.chat_text.config(state="disabled")
        self.user_entry.delete(0, END)
        self.on_send_callback(user_text)
