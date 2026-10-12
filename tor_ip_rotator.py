#!/usr/bin/env python3
"""Tor IP Rotator — simple dark-mode GUI to rotate your Tor exit IP on a timer.
Developed by MAHRAN
"""
import threading, time, tkinter as tk
from tkinter import ttk, messagebox
from stem import Signal
from stem.control import Controller
try:
    import requests
except ImportError:
    requests = None

APP_TITLE = "Tor IP Rotator"
FOOTER_TEXT = "Developed by MAHRAN"

# Dark palette
BG = "#121212"
PANEL = "#1e1e1e"
FG = "#e8e8e8"
ACCENT = "#7c4dff"
MUTED = "#9a9a9a"
GREEN = "#4caf50"

class TorIPRotator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.resizable(True, True)
        self.geometry("560x560")
        self.configure(bg=BG)
        self._running = False
        self._worker = None
        self._rotation_count = 0
        self._interval = 10
        self._seconds_left = 0
        self._build_ui()
        self._tick_countdown()

    def _build_ui(self):
        tk.Label(self, text=APP_TITLE, font=("Helvetica", 18, "bold"), bg=BG, fg=FG).pack(pady=(16, 2))
        tk.Label(self, text="Rotates your Tor exit IP automatically, on a timer.",
                 font=("Helvetica", 10), bg=BG, fg=MUTED).pack(pady=(0, 12))

        form = tk.Frame(self, bg=BG); form.pack(padx=16, pady=4)

        def add_field(row, label, default):
            tk.Label(form, text=label, bg=BG, fg=FG, font=("Helvetica", 10)).grid(row=row, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=default)
            e = tk.Entry(form, textvariable=var, width=10, bg=PANEL, fg=FG,
                         insertbackground=FG, relief="flat", highlightthickness=1,
                         highlightbackground="#333", highlightcolor=ACCENT)
            e.grid(row=row, column=1, sticky="w", padx=10)
            return var

        self.control_port_var = add_field(0, "Tor Control Port:", "9051")
        self.socks_port_var = add_field(1, "Tor SOCKS Port:", "9050")
        self.interval_var = add_field(2, "Rotate every (seconds):", "10")

        tk.Label(self, text="Tip: values below ~10s often won't get a new circuit every time.",
                 font=("Helvetica", 8), bg=BG, fg=MUTED, justify="center").pack(pady=(6, 10))

        btns = tk.Frame(self, bg=BG); btns.pack(pady=4)
        self.start_btn = tk.Button(btns, text="Start", command=self.start, bg=ACCENT, fg="white",
                                    activebackground="#6a3fe0", relief="flat", width=10, font=("Helvetica", 10, "bold"))
        self.start_btn.grid(row=0, column=0, padx=6)
        self.stop_btn = tk.Button(btns, text="Stop", command=self.stop, state="disabled", bg="#333", fg=FG,
                                   activebackground="#444", relief="flat", width=10, font=("Helvetica", 10, "bold"))
        self.stop_btn.grid(row=0, column=1, padx=6)

        self.status_var = tk.StringVar(value="Stopped")
        tk.Label(self, textvariable=self.status_var, font=("Helvetica", 11, "bold"), bg=BG, fg=FG).pack(pady=(14, 6))

        # IP display box
        ip_box = tk.Frame(self, bg=PANEL, highlightbackground="#333", highlightthickness=1)
        ip_box.pack(pady=4, padx=40, fill="x")
        tk.Label(ip_box, text="CURRENT EXIT IP", font=("Helvetica", 8, "bold"), bg=PANEL, fg=MUTED).pack(pady=(8, 0))
        self.ip_var = tk.StringVar(value="—")
        tk.Label(ip_box, textvariable=self.ip_var, font=("Helvetica", 16, "bold"), bg=PANEL, fg=GREEN).pack(pady=(0, 8))

        # Countdown box
        cd_box = tk.Frame(self, bg=PANEL, highlightbackground="#333", highlightthickness=1)
        cd_box.pack(pady=10, padx=40, fill="x")
        tk.Label(cd_box, text="NEXT ROTATION IN", font=("Helvetica", 8, "bold"), bg=PANEL, fg=MUTED).pack(pady=(8, 0))
        self.countdown_var = tk.StringVar(value="—")
        tk.Label(cd_box, textvariable=self.countdown_var, font=("Helvetica", 16, "bold"), bg=PANEL, fg=ACCENT).pack(pady=(0, 8))

        # Log box
        logf = tk.Frame(self, bg=BG)
        logf.pack(fill="both", expand=True, padx=16, pady=(10, 0))
        self.log_box = tk.Text(logf, height=8, bg=PANEL, fg=FG, insertbackground=FG,
                                relief="flat", wrap="word", state="disabled")
        self.log_box.pack(side="left", fill="both", expand=True)
        sc = tk.Scrollbar(logf, command=self.log_box.yview)
        sc.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=sc.set)

        tk.Label(self, text=FOOTER_TEXT, font=("Helvetica", 10, "italic"), bg=BG, fg=ACCENT).pack(side="bottom", pady=12)

    def _log(self, text):
        self.log_box.config(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def start(self):
        try:
            control_port = int(self.control_port_var.get())
            interval = float(self.interval_var.get())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(APP_TITLE, "Control port and interval must be valid numbers.")
            return
        self._interval = interval
        self._seconds_left = interval
        self._running = True
        self._rotation_count = 0
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Running…")
        self._log("Started.")
        self._worker = threading.Thread(target=self._run_loop, args=(control_port, interval), daemon=True)
        self._worker.start()

    def stop(self):
        self._running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("Stopped")
        self.countdown_var.set("—")
        self._log("Stopped.")

    def _run_loop(self, control_port, interval):
        try:
            with Controller.from_port(port=control_port) as controller:
                controller.authenticate()
                while self._running:
                    controller.signal(Signal.NEWNYM)
                    self._rotation_count += 1
                    self._log(f"[{self._rotation_count}] Requested a new circuit.")
                    self._maybe_update_ip()
                    self._seconds_left = interval
                    time.sleep(interval)
        except Exception as exc:
            self._log(f"Error: {exc}")
            self.after(0, self.stop)

    def _maybe_update_ip(self):
        if requests is None:
            return
        try:
            socks_port = int(self.socks_port_var.get())
            proxies = {"http": f"socks5h://127.0.0.1:{socks_port}", "https": f"socks5h://127.0.0.1:{socks_port}"}
            ip = requests.get("https://api.ipify.org", proxies=proxies, timeout=8).text
            self.ip_var.set(ip)
        except Exception:
            self.ip_var.set("(couldn't check)")

    def _tick_countdown(self):
        if self._running and self._seconds_left is not None:
            self.countdown_var.set(f"{max(0, int(self._seconds_left))}s")
            self._seconds_left -= 1
        self.after(1000, self._tick_countdown)


if __name__ == "__main__":
    TorIPRotator().mainloop()
