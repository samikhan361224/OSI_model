#!/usr/bin/env python3
"""
osi_visualizer.py
OSI Model Simulation – Python Visualizer

Launches server.exe and client.exe, captures their output, and renders
a live zig-zag data-flow diagram to the terminal, printing progress
after every two OSI layers (mimicking Linux/Ubuntu networking stacks).
"""

import subprocess
import sys
import time
import threading
import os
import re
from datetime import datetime

# ─── ANSI colors ──────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    GRAY   = "\033[90m"

# ─── Layer metadata ───────────────────────────────────────────────────────────
LAYERS = [
    (7, "Application",   C.GREEN),
    (6, "Presentation",  C.CYAN),
    (5, "Session",       C.BLUE),
    (4, "Transport",     C.MAGENTA),
    (3, "Network",       C.YELLOW),
    (2, "Data Link",     C.RED),
    (1, "Physical",      C.WHITE),
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_EXE = os.path.join(SCRIPT_DIR, "server.exe")
CLIENT_EXE = os.path.join(SCRIPT_DIR, "client.exe")

def enable_ansi():
    """Enable ANSI escape codes on Windows 10+."""
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def banner():
    print(f"\n{C.BOLD}{C.CYAN}{'═'*68}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  OSI MODEL SIMULATION  –  Python Visualizer  {C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  Date/Time : {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'═'*68}{C.RESET}\n")

def zigzag_diagram(message: str):
    """Print a static zig-zag OSI data-flow diagram."""
    col_w = 22
    print(f"\n{C.BOLD}  DATA FLOW ZIG-ZAG DIAGRAM{C.RESET}")
    print(f"  {'CLIENT (Sender)':<{col_w}}   {'SERVER (Receiver)':<{col_w}}")
    print(f"  {'─'*col_w}   {'─'*col_w}")

    for i, (num, name, color) in enumerate(LAYERS):
        arrow_down = "↓ ENCAPSULATE" if i < len(LAYERS)-1 else "↓ SEND ──────▶"
        arrow_up   = "↑ DECAPSULATE"
        client_col = f"Layer {num}: {name}"
        server_col = f"Layer {num}: {name}"

        print(
            f"  {color}{client_col:<{col_w}}{C.RESET}"
            f"   {color}{server_col:<{col_w}}{C.RESET}"
        )
        # Every two layers print progress
        if (i + 1) % 2 == 0:
            layer_pair = f"L{LAYERS[i-1][0]}&L{num}"
            print(f"  {C.GRAY}{'·'*col_w}   {'·'*col_w}{C.RESET}")
            print(f"  {C.YELLOW}  ▶ Progress checkpoint: {layer_pair} done{C.RESET}")
            print()

def stream_output(label: str, color: str, proc_stdout):
    """Thread target: stream subprocess stdout line-by-line."""
    for line in proc_stdout:
        line = line.rstrip()
        if line:
            print(f"{color}[{label}]{C.RESET} {line}")

def run_simulation(message: str):
    if not os.path.isfile(SERVER_EXE):
        print(f"{C.RED}ERROR: {SERVER_EXE} not found. Run 'build.bat' first.{C.RESET}")
        sys.exit(1)
    if not os.path.isfile(CLIENT_EXE):
        print(f"{C.RED}ERROR: {CLIENT_EXE} not found. Run 'build.bat' first.{C.RESET}")
        sys.exit(1)

    print(f"{C.BOLD}  Message to simulate: {C.GREEN}\"{message}\"{C.RESET}\n")

    # ── Start server ──────────────────────────────────────────────────────────
    print(f"{C.CYAN}  Starting SERVER ...{C.RESET}")
    srv_proc = subprocess.Popen(
        [SERVER_EXE],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=SCRIPT_DIR,
    )
    time.sleep(0.5)  # Give server a moment to bind

    srv_thread = threading.Thread(
        target=stream_output,
        args=("SERVER", C.GREEN, srv_proc.stdout),
        daemon=True,
    )
    srv_thread.start()
    time.sleep(0.3)

    # ── Show zig-zag diagram ──────────────────────────────────────────────────
    zigzag_diagram(message)

    print(f"\n{C.BOLD}{'─'*68}{C.RESET}")
    print(f"{C.BOLD}  LIVE LAYER-BY-LAYER OUTPUT{C.RESET}")
    print(f"{C.BOLD}{'─'*68}{C.RESET}\n")

    # ── Start client ──────────────────────────────────────────────────────────
    print(f"{C.MAGENTA}  Starting CLIENT ...{C.RESET}\n")
    cli_proc = subprocess.Popen(
        [CLIENT_EXE, message],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=SCRIPT_DIR,
    )

    cli_thread = threading.Thread(
        target=stream_output,
        args=("CLIENT", C.MAGENTA, cli_proc.stdout),
        daemon=True,
    )
    cli_thread.start()

    cli_proc.wait(timeout=15)
    srv_proc.wait(timeout=15)
    cli_thread.join(timeout=5)
    srv_thread.join(timeout=5)

    print(f"\n{C.BOLD}{C.CYAN}{'═'*68}{C.RESET}")
    print(f"{C.BOLD}{C.GREEN}  SIMULATION COMPLETE{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'═'*68}{C.RESET}\n")

def print_layer_progress_guide():
    """Print a legend explaining the two-layer progress checkpoints."""
    print(f"\n{C.BOLD}  PROGRESS CHECKPOINT LEGEND (every 2 layers){C.RESET}")
    print(f"  {'─'*50}")
    checkpoints = [
        ("CLIENT Layers 7-6", "Application + Presentation (Encapsulation starts)"),
        ("CLIENT Layers 5-4", "Session + Transport"),
        ("CLIENT Layers 3-2", "Network + Data Link"),
        ("CLIENT Layer 1",    "Physical – Frame on the wire!"),
        ("SERVER Layers 1-2", "Physical + Data Link (Decapsulation starts)"),
        ("SERVER Layers 3-4", "Network + Transport"),
        ("SERVER Layers 5-6", "Session + Presentation"),
        ("SERVER Layer 7",    "Application – Message delivered!"),
    ]
    for step, desc in checkpoints:
        print(f"  {C.YELLOW}►{C.RESET} {step:<24} {C.GRAY}{desc}{C.RESET}")
    print()

if __name__ == "__main__":
    enable_ansi()
    banner()

    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello from OSI Simulation!"

    print_layer_progress_guide()
    run_simulation(msg)
