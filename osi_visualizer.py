#!/usr/bin/env python3
"""
================================================================================
  OSI 7-LAYER COMMUNICATION SIMULATION — PROFESSIONAL TERMINAL VISUALIZER
================================================================================
  Author: Akib Jawad
  Architecture: C Client (Encapsulation) -> TCP Socket (Port 9090) -> C Server (Decapsulation)
  Visualization: Python Rich Terminal Interface
================================================================================
"""

import os
import sys
import time
import socket
import subprocess
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

# Force UTF-8 encoding on standard streams to avoid cp1252 Windows encoding crashes
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Ensure standard UTF-8 stream handling on Windows
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # ENABLE_PROCESSED_OUTPUT (1) | ENABLE_WRAP_AT_EOL_OUTPUT (2) | ENABLE_VIRTUAL_TERMINAL_PROCESSING (4)
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.align import Align
    from rich.columns import Columns
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich import box
    from rich.style import Style
except ImportError:
    print("[ERROR] 'rich' library is required. Please install it using: py -m pip install rich")
    sys.exit(1)

# Initialize console with forced UTF-8 & modern terminal capabilities
console = Console(legacy_windows=False)

# ─── Directories & Executables ────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_EXE = os.path.join(SCRIPT_DIR, "server.exe")
CLIENT_EXE = os.path.join(SCRIPT_DIR, "client.exe")
BUILD_BAT  = os.path.join(SCRIPT_DIR, "build.bat")

# ─── Animation Speed Presets (seconds per step) ──────────────────────────────
SPEED_PRESETS = {
    "1": ("Educational / Slow", 1.10),
    "2": ("Standard / Normal",  0.55),
    "3": ("Fast / Demo",         0.22),
    "4": ("Step-by-Step (Manual)", -1.0) # wait for Enter
}
current_speed_key = "2"

# ─── OSI Layer Comprehensive Knowledge Base ──────────────────────────────────
OSI_LAYERS = {
    7: {
        "num": 7,
        "name": "Application",
        "pdu": "Data / Message",
        "color": "bright_green",
        "accent": "#00FF88",
        "icon": "🌐",
        "role": "User Interface & Network Application Services",
        "desc": "Initiates communication. Takes human-readable user input and wraps it in an application-level protocol PDU (HTTP, FTP, DNS).",
        "encap_action": "Prepends simulated AppHeader (Protocol: HTTP, Payload Length).",
        "decap_action": "Strips AppHeader, validates HTTP protocol, and delivers the original user message to the receiver.",
        "sim_header": "AppHeader (18 B) -> protocol: 'HTTP', data_len: %d B",
        "real_vs_sim": "Simulated HTTP header inside C struct; transported through the real OS socket stack.",
        "struct_fields": [("protocol", "char[16]", "HTTP"), ("data_len", "uint16_t", "%d bytes")]
    },
    6: {
        "num": 6,
        "name": "Presentation",
        "pdu": "Formatted Data",
        "color": "bright_cyan",
        "accent": "#00E5FF",
        "icon": "🔒",
        "role": "Syntax, Compression & Encryption",
        "desc": "Translates data formats, manages character encoding (ASCII/UTF-8), and handles cryptographic encryption/decryption (e.g. TLS/SSL simulation).",
        "encap_action": "XOR-encrypts payload with key 0xAB and prepends PresHeader (Encoding: ASCII, Encrypted: 1).",
        "decap_action": "Inspects PresHeader, detects encryption flag, and decrypts payload back to readable plaintext using key 0xAB.",
        "sim_header": "PresHeader (17 B) -> encoding: 'ASCII', encrypted: 1 (XOR 0xAB)",
        "real_vs_sim": "Simulates TLS/ASCII encoding; in real systems TLS record layer performs symmetric AES/ChaCha20 encryption.",
        "struct_fields": [("encoding", "char[16]", "ASCII"), ("encrypted", "uint8_t", "1 (True)")]
    },
    5: {
        "num": 5,
        "name": "Session",
        "pdu": "Session Protocol Data Unit",
        "color": "bright_blue",
        "accent": "#2979FF",
        "icon": "🤝",
        "role": "Session Synchronization & Dialog Control",
        "desc": "Establishes, maintains, and terminates conversational sessions between endpoints. Enforces simplex, half-duplex, or full-duplex transmission.",
        "encap_action": "Assigns unique Session ID (0xDEADBEEF) and establishes Full-Duplex dialog control header.",
        "decap_action": "Verifies active Session ID token (0xDEADBEEF) and tears down session context upon completion.",
        "sim_header": "SessHeader (5 B) -> session_id: 0xDEADBEEF, dialog_control: 1 (Full-Duplex)",
        "real_vs_sim": "Simulates NetBIOS/RPC session tokens; modern web mostly embeds session IDs in HTTP cookies/tokens.",
        "struct_fields": [("session_id", "uint32_t", "0xDEADBEEF"), ("dialog_control", "uint8_t", "1 (Full-Duplex)")]
    },
    4: {
        "num": 4,
        "name": "Transport",
        "pdu": "Segment",
        "color": "bright_magenta",
        "accent": "#D500F9",
        "icon": "🚚",
        "role": "End-to-End Reliability, Port Addressing & Flow Control",
        "desc": "Manages host-to-host segment delivery. Implements logical port numbers (e.g. 50000 -> 9090) and sequence tracking for order integrity.",
        "encap_action": "Adds simulated TransHeader (Src Port 50000, Dst Port 9090, Seq 1000, Protocol 6 [TCP]).",
        "decap_action": "Checks destination port 9090, verifies sequence continuity, and demultiplexes payload toward upper layers.",
        "sim_header": "TransHeader (9 B) -> src: 50000, dst: 9090, seq: 1000, proto: TCP (6)",
        "real_vs_sim": "Educational TCP header inside frame payload; real OS TCP header is managed by kernel network stack.",
        "struct_fields": [("src_port", "uint16_t", "50000"), ("dst_port", "uint16_t", "9090"), ("seq_num", "uint32_t", "1000"), ("protocol", "uint8_t", "6 (TCP)")]
    },
    3: {
        "num": 3,
        "name": "Network",
        "pdu": "Packet / Datagram",
        "color": "bright_yellow",
        "accent": "#FFD600",
        "icon": "🧭",
        "role": "Logical Addressing, Packet Routing & Path Determination",
        "desc": "Assigns logical IP addresses (IPv4/IPv6) for internetwork routing. Sets Time-To-Live (TTL) to prevent endless routing loops.",
        "encap_action": "Adds simulated NetHeader (Src IP 192.168.1.10, Dst IP 127.0.0.1, TTL 64, Protocol 6).",
        "decap_action": "Inspects destination IP (127.0.0.1), verifies TTL viability (> 0), and strips network header.",
        "sim_header": "NetHeader (34 B) -> src_ip: 192.168.1.10, dst_ip: 127.0.0.1, ttl: 64",
        "real_vs_sim": "Simulated IPv4 header structure; real IP routing is performed by host routing table and NIC driver.",
        "struct_fields": [("src_ip", "char[16]", "192.168.1.10"), ("dst_ip", "char[16]", "127.0.0.1"), ("ttl", "uint8_t", "64"), ("protocol", "uint8_t", "6 (TCP)")]
    },
    2: {
        "num": 2,
        "name": "Data Link",
        "pdu": "Frame",
        "color": "bright_red",
        "accent": "#FF1744",
        "icon": "🏷️",
        "role": "Node-to-Node Framing & Error Detection (MAC/FCS)",
        "desc": "Packages packets into Ethernet frames with physical MAC addresses. Computes Frame Check Sequence (FCS) checksum for error detection.",
        "encap_action": "Calculates 16-bit FCS checksum over payload; prepends DLHeader (Src MAC AA:BB:..., Dst MAC 11:22:..., EtherType 0x0800).",
        "decap_action": "Computes FCS over payload; matches against received FCS (0x%04X). Confirms zero bit corruption before passing up.",
        "sim_header": "DLHeader (40 B) -> MAC: AA:BB:CC:DD:EE:FF -> 11:22:33:44:55:66, FCS: 0x%04X",
        "real_vs_sim": "Simulated Ethernet II frame; physical NIC hardware handles real CRC-32 and preamble.",
        "struct_fields": [("src_mac", "char[18]", "AA:BB:CC:DD:EE:FF"), ("dst_mac", "char[18]", "11:22:33:44:55:66"), ("ether_type", "uint16_t", "0x0800 (IPv4)"), ("fcs", "uint16_t", "0x%04X (Computed)")]
    },
    1: {
        "num": 1,
        "name": "Physical",
        "pdu": "Bits / Raw Signals",
        "color": "white",
        "accent": "#EEEEEE",
        "icon": "⚡",
        "role": "Signal Encoding, Bit Transmission & Physical Media",
        "desc": "Converts binary frame bytes into physical digital signals or bitstreams (NRZ, Manchester line coding, voltages, radio waves, light pulses).",
        "encap_action": "Prepends PhysHeader (Bit Count: %d bits, Encoding: Manchester). Ready for transmission over physical media.",
        "decap_action": "Receives raw electrical/optical bitstream, converts bits into byte frame buffer, strips PhysHeader.",
        "sim_header": "PhysHeader (5 B) -> bit_count: %d bits, encoding_type: 1 (Manchester)",
        "real_vs_sim": "Simulated signal parameters; actual physical transmission handled by TCP/IP loopback socket driver.",
        "struct_fields": [("bit_count", "uint32_t", "%d bits"), ("encoding_type", "uint8_t", "1 (Manchester)")]
    }
}

# ─── Educational Helpers ───────────────────────────────────────────────────────

def simple_checksum_py(data: bytes) -> int:
    """16-bit simple checksum matching C simple_checksum()."""
    return sum(data) & 0xFFFF

def xor_bytes(data: bytes, key: int = 0xAB) -> bytes:
    """XOR bytes matching C xor_data()."""
    return bytes(b ^ key for b in data)

def to_bit_sample(data: bytes, max_bits: int = 48) -> str:
    """Returns a spaced binary bit sample string."""
    raw = "".join(f"{b:08b}" for b in data)
    sampled = raw[:max_bits]
    chunks = [sampled[i:i+8] for i in range(0, len(sampled), 8)]
    return " ".join(chunks) + ("..." if len(raw) > max_bits else "")

def to_hex_sample(data: bytes, max_bytes: int = 16) -> str:
    """Returns spaced hex byte string."""
    hex_str = " ".join(f"{b:02X}" for b in data[:max_bytes])
    if len(data) > max_bytes:
        hex_str += " ..."
    return hex_str

# ─── Frame Inspection Model ───────────────────────────────────────────────────

def get_simulated_frame_breakdown(message: str) -> Dict[str, Any]:
    """Computes exact simulated header and frame sizes and values matching C client."""
    msg_bytes = message.encode("ascii", errors="replace")
    msg_len = len(msg_bytes)

    # L7: AppHeader (18 B) + msg_len
    app_hdr_len = 18
    # L6: PresHeader (17 B) + encrypted(L7 + msg)
    pres_hdr_len = 17
    # L5: SessHeader (5 B)
    sess_hdr_len = 5
    # L4: TransHeader (9 B)
    trans_hdr_len = 9
    # L3: NetHeader (34 B)
    net_hdr_len = 34
    # L2: DLHeader (40 B)
    dl_hdr_len = 40
    # L1: PhysHeader (5 B)
    phys_hdr_len = 5

    total_headers = (app_hdr_len + pres_hdr_len + sess_hdr_len +
                     trans_hdr_len + net_hdr_len + dl_hdr_len + phys_hdr_len)
    total_frame_len = total_headers + msg_len
    total_bits = (total_frame_len - phys_hdr_len) * 8

    # Approximate FCS checksum computation (simulated)
    # Payload covered by FCS = DLHeader..end
    sim_fcs = (sum(msg_bytes) + 0x2400 + msg_len * 7) & 0xFFFF

    return {
        "message": message,
        "msg_len": msg_len,
        "app_hdr_len": app_hdr_len,
        "pres_hdr_len": pres_hdr_len,
        "sess_hdr_len": sess_hdr_len,
        "trans_hdr_len": trans_hdr_len,
        "net_hdr_len": net_hdr_len,
        "dl_hdr_len": dl_hdr_len,
        "phys_hdr_len": phys_hdr_len,
        "total_headers": total_headers,
        "total_frame_len": total_frame_len,
        "total_bits": total_bits,
        "sim_fcs": sim_fcs,
        "xor_sample": xor_bytes(msg_bytes),
    }

# ─── UI Rendering Components ──────────────────────────────────────────────────

def render_banner(subtitle: str = "Live 7-Layer Encapsulation & Decapsulation Engine") -> Panel:
    """Generates the primary title banner panel."""
    title_text = Text()
    title_text.append("⚡ OSI 7-LAYER NETWORK COMMUNICATION SIMULATION ⚡\n", style="bold bright_cyan")
    title_text.append("═══════════════════════════════════════════════════════════════════════════════════\n", style="dim cyan")
    title_text.append(f"  System Author  : Akib Jawad          │  Local Time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", style="bright_white")
    title_text.append(f"  Simulation Mode: C Sockets (MinGW)   │  Transport   : TCP 127.0.0.1:9090\n", style="bright_white")
    title_text.append(f"  Current Status : {subtitle}", style="bold yellow")

    return Panel(
        Align.center(title_text),
        box=box.ROUNDED,
        border_style="bright_blue",
        padding=(0, 1),
    )

def render_zigzag_stack(
    phase: str, # "ENCAP" or "DECAP" or "WIRE"
    active_layer: int,
    completed_layers: List[int],
    step_indicator: int,
    message: str
) -> Table:
    """
    Renders the animated 7-layer OSI vertical stack with zig-zag data flow indicator.
    Phase ENCAP: moves L7 -> L1 (downward).
    Phase DECAP: moves L1 -> L7 (upward).
    """
    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        title=f"[bold bright_white]{'CLIENT (Sender) — ENCAPSULATION' if phase == 'ENCAP' else 'SERVER (Receiver) — DECAPSULATION'}[/bold bright_white]",
        title_style="bold cyan",
        header_style="bold yellow",
        expand=True,
    )
    table.add_column("Layer", justify="center", width=8)
    table.add_column("Name", width=14)
    table.add_column("Zig-Zag Data Flow Path", justify="center", width=26)
    table.add_column("PDU / Simulated Unit", width=22)
    table.add_column("Status", justify="center", width=12)

    order = [7, 6, 5, 4, 3, 2, 1] if phase == "ENCAP" else [1, 2, 3, 4, 5, 6, 7]

    for idx, lnum in enumerate(order):
        layer = OSI_LAYERS[lnum]
        is_active = (lnum == active_layer)
        is_done = (lnum in completed_layers)

        # Zig-Zag directional arrow styling: alternate left/right per layer
        if phase == "ENCAP":
            # Downward zig-zag
            if lnum % 2 == 1:
                # Odd layers: push right
                if is_active:
                    zigzag = "[bold bright_yellow]═════════════▶ [DATA][/bold bright_yellow]"
                elif is_done:
                    zigzag = "[bright_green]─────────────▶ [DONE][/bright_green]"
                else:
                    zigzag = "[dim]─────────────▶ [WAIT][/dim]"
            else:
                # Even layers: pull left
                if is_active:
                    zigzag = "[bold bright_yellow][DATA] ◀═════════════[/bold bright_yellow]"
                elif is_done:
                    zigzag = "[bright_green][DONE] ◀─────────────[/bright_green]"
                else:
                    zigzag = "[dim][WAIT] ◀─────────────[/dim]"
        else:
            # Upward zig-zag (Decapsulation)
            if lnum % 2 == 1:
                if is_active:
                    zigzag = "[bold bright_yellow][DATA] ◀═════════════[/bold bright_yellow]"
                elif is_done:
                    zigzag = "[bright_green][DONE] ◀─────────────[/bright_green]"
                else:
                    zigzag = "[dim][WAIT] ◀─────────────[/dim]"
            else:
                if is_active:
                    zigzag = "[bold bright_yellow]═════════════▶ [DATA][/bold bright_yellow]"
                elif is_done:
                    zigzag = "[bright_green]─────────────▶ [DONE][/bright_green]"
                else:
                    zigzag = "[dim]─────────────▶ [WAIT][/dim]"

        # PDU Label
        pdu_label = layer["pdu"]

        # Status text
        if is_active:
            status = "[bold blink yellow]● ACTIVE[/bold blink yellow]"
            layer_style = f"bold {layer['color']}"
        elif is_done:
            status = "[bold green]✔ COMPLETE[/bold green]"
            layer_style = "bright_green"
        else:
            status = "[dim]○ PENDING[/dim]"
            layer_style = "dim"

        table.add_row(
            f"[{layer_style}]L{lnum}[/{layer_style}]",
            f"[{layer_style}]{layer['icon']} {layer['name']}[/{layer_style}]",
            zigzag,
            f"[{layer_style}]{pdu_label}[/{layer_style}]",
            status,
        )

    return table

def render_packet_structure_box(phase: str, active_layer: int, message: str) -> Panel:
    """
    Renders progressive visual encapsulation / decapsulation data structure block:
    [ Application Data ] -> [ Transport | App Data ] -> etc.
    """
    lines = []
    lines.append("[bold bright_white]Progressive Frame Encapsulation Architecture:[/bold bright_white]\n")

    # Client (encapsulation): builds from inside out
    # Stage representations:
    stages = [
        (7, "[bold green][ HTTP Payload: \"" + message + "\" ][/bold green]"),
        (6, "[cyan][ Pres: ASCII/XOR ][/cyan] [bold green][ HTTP Payload ][/bold green]"),
        (5, "[blue][ Sess: ID 0xDEADBEEF ][/blue] [cyan][ Pres ][/cyan] [bold green][ HTTP Payload ][/bold green]"),
        (4, "[magenta][ TCP: Port 50000->9090 Seq:1000 ][/magenta] [blue][ Sess ][/blue] [cyan][ Pres ][/cyan] [bold green][ Payload ][/bold green]"),
        (3, "[yellow][ IP: 192.168.1.10->127.0.0.1 TTL:64 ][/yellow] [magenta][ TCP ][/magenta] [blue][ Sess ][/blue] [cyan][ Pres ][/cyan] [bold green][ Payload ][/bold green]"),
        (2, "[red][ Eth: MAC AA:..->11:.. ][/red] [yellow][ IP ][/yellow] [magenta][ TCP ][/magenta] [blue][ Sess ][/blue] [cyan][ Pres ][/cyan] [bold green][ Payload ][/bold green] [red][ FCS Checksum ][/red]"),
        (1, "[white][ Phys Line Encoding: 1104 Manchester Bits ][/white]\n   [bold bright_yellow]▶ Frame Complete: 143 Bytes Ready for Wire Transmission[/bold bright_yellow]")
    ]

    if phase == "ENCAP":
        for lnum, stext in stages:
            if lnum >= active_layer:
                prefix = "[bold yellow]▶[/bold yellow] " if lnum == active_layer else "  "
                lines.append(f"{prefix}{stext}")
            else:
                lines.append(f"  [dim]{stext}[/dim]")
    else: # DECAP
        for lnum, stext in reversed(stages):
            if lnum <= active_layer:
                prefix = "[bold yellow]◀ Stripping: [/bold yellow]" if lnum == active_layer else "  [bright_green]✔ Decapsulated: [/bright_green]"
                lines.append(f"{prefix}{stext}")
            else:
                lines.append(f"  [dim]Bound: {stext}[/dim]")

    return Panel(
        "\n".join(lines),
        title="[bold bright_magenta]📦 Data Encapsulation / Decapsulation Inspector[/bold bright_magenta]",
        box=box.ROUNDED,
        border_style="magenta",
        padding=(0, 1),
    )

def render_layer_detail_card(lnum: int, phase: str, fbreak: Dict[str, Any]) -> Panel:
    """
    Renders educational explanation for the currently active OSI layer.
    Distinguishes simulated OSI headers from actual TCP/IP socket headers.
    """
    layer = OSI_LAYERS[lnum]
    action_text = layer["encap_action"] if phase == "ENCAP" else layer["decap_action"]

    content = Text()
    content.append(f"{layer['icon']} LAYER {layer['num']}: {layer['name'].upper()} LAYER\n", style=f"bold {layer['color']}")
    content.append("─────────────────────────────────────────────────────────────\n", style="dim")
    content.append("• Primary Role : ", style="bold bright_white")
    content.append(f"{layer['role']}\n", style="bright_white")
    content.append("• Description  : ", style="bold bright_white")
    content.append(f"{layer['desc']}\n\n", style="white")

    content.append(f"• Active Action ({'Encapsulation' if phase == 'ENCAP' else 'Decapsulation'}):\n", style="bold yellow")
    content.append(f"  {action_text}\n\n", style="bright_yellow")

    content.append("• Simulated Header Fields:\n", style="bold cyan")
    for fname, ftype, fval in layer["struct_fields"]:
        if "%d" in fval:
            if "bytes" in fval:
                val_formatted = fval % fbreak["msg_len"]
            elif "bits" in fval:
                val_formatted = fval % fbreak["total_bits"]
            else:
                val_formatted = fval % fbreak["msg_len"]
        elif "%04X" in fval:
            val_formatted = fval % fbreak["sim_fcs"]
        else:
            val_formatted = fval
        content.append(f"   ▫ {fname:<15} ({ftype:<10}) = {val_formatted}\n", style="bright_cyan")

    content.append("\n• Educational Stack Note:\n", style="bold bright_magenta")
    content.append(f"  {layer['real_vs_sim']}\n", style="italic gray")
    content.append("  [Note: In real operating systems, Layers 1-4 are managed by the kernel & NIC driver.\n", style="dim white")
    content.append("   This project simulates the full 7-layer encapsulation before transmitting over standard sockets.]\n", style="dim white")

    return Panel(
        content,
        title=f"[bold {layer['color']}]Educational Protocol Breakdown[/bold {layer['color']}]",
        box=box.ROUNDED,
        border_style=layer["color"],
        padding=(0, 1)
    )

def render_two_layer_progress(
    phase: str,
    active_layer: int,
    completed_layers: List[int]
) -> Panel:
    """
    Renders progress update specifically after every TWO OSI layers as required:
    Encapsulation:
      L7+L6 -> 2/7 (28%)
      L5+L4 -> 4/7 (57%)
      L3+L2 -> 6/7 (85%)
      L1    -> 7/7 (100%)
    Decapsulation:
      L1+L2 -> 2/7 (28%)
      L3+L4 -> 4/7 (57%)
      L5+L6 -> 6/7 (85%)
      L7    -> 7/7 (100%)
    """
    count = len(completed_layers)
    percent = int((count / 7.0) * 100)

    # Calculate two-layer milestone
    if phase == "ENCAP":
        if count >= 7:
            stage_msg = "[bold green]Milestone 4/4: Layer 1 Complete (7/7 - 100%) — Physical Bitstream Ready![/bold green]"
        elif count >= 6:
            stage_msg = "[bold bright_yellow]Milestone 3/4: Layers 3+2 Complete (6/7 - 85%) — Network & Data Link Done[/bold bright_yellow]"
        elif count >= 4:
            stage_msg = "[bold bright_cyan]Milestone 2/4: Layers 5+4 Complete (4/7 - 57%) — Session & Transport Done[/bold bright_cyan]"
        elif count >= 2:
            stage_msg = "[bold bright_blue]Milestone 1/4: Layers 7+6 Complete (2/7 - 28%) — Application & Presentation Done[/bold bright_blue]"
        else:
            stage_msg = f"[dim]Encapsulating Layer {active_layer}...[/dim]"
    else: # DECAP
        if count >= 7:
            stage_msg = "[bold green]Milestone 4/4: Layer 7 Complete (7/7 - 100%) — Application Message Fully Recovered![/bold green]"
        elif count >= 6:
            stage_msg = "[bold bright_cyan]Milestone 3/4: Layers 5+6 Complete (6/7 - 85%) — Session & Presentation Done[/bold bright_cyan]"
        elif count >= 4:
            stage_msg = "[bold bright_blue]Milestone 2/4: Layers 3+4 Complete (4/7 - 57%) — Network & Transport Done[/bold bright_blue]"
        elif count >= 2:
            stage_msg = "[bold bright_yellow]Milestone 1/4: Layers 1+2 Complete (2/7 - 28%) — Physical & Data Link Done[/bold bright_yellow]"
        else:
            stage_msg = f"[dim]Decapsulating Layer {active_layer}...[/dim]"

    # Build ASCII progress bar
    bar_width = 32
    filled = int(bar_width * (count / 7.0))
    bar_str = "█" * filled + "░" * (bar_width - filled)

    table = Table.grid(expand=True)
    table.add_column("Key", width=22)
    table.add_column("Value")

    table.add_row(
        "[bold white]Progress Bar:[/bold white]",
        f"[bold bright_green][{bar_str}][/bold bright_green]  [bold yellow]{count}/7 Layers ({percent}%)[/bold yellow]"
    )
    table.add_row(
        "[bold white]Active Stage:[/bold white]",
        f"[bright_white]{stage_msg}[/bright_white]"
    )
    table.add_row(
        "[bold white]Checkpoint Rule:[/bold white]",
        "[cyan]Progress milestone logged after every two OSI layers (mimicking Linux network stacks)[/cyan]"
    )

    return Panel(
        table,
        title="[bold bright_yellow]📊 Two-Layer Progress Tracking Checkpoint[/bold bright_yellow]",
        box=box.ROUNDED,
        border_style="yellow",
        padding=(0, 1),
    )

def render_socket_transmission_wire(pulse_step: int, frame_size: int) -> Panel:
    """Renders the real TCP socket transmission over loopback wire animation."""
    wire_len = 24
    pos = pulse_step % wire_len

    wire_chars = list("═" * wire_len)
    for p in range(max(0, pos - 2), min(wire_len, pos + 3)):
        wire_chars[p] = "▓"
    wire_chars[pos] = "█"
    wire_str = "".join(wire_chars)

    content = Text()
    content.append("CLIENT (127.0.0.1:50000) ", style="bold bright_cyan")
    content.append(f"───[{wire_str}]───▶ ", style="bold bright_yellow")
    content.append("SERVER (127.0.0.1:9090)\n\n", style="bold bright_green")

    content.append(f"• Transport Socket: Real TCP Stream (AF_INET, SOCK_STREAM) on Localhost\n", style="bright_white")
    content.append(f"• Frame Transmitted: {frame_size} Bytes Binary Struct PDU\n", style="bright_white")
    content.append(f"• Server Response: ACK:OSI_SIM_OK\n", style="bold green")

    return Panel(
        Align.center(content),
        title="[bold bright_cyan]🌐 Real TCP Socket Transmission Phase (Wire Level)[/bold bright_cyan]",
        box=box.DOUBLE,
        border_style="bright_cyan",
        padding=(0, 1),
    )

def render_educational_data_panel(fbreak: Dict[str, Any], stage: str) -> Panel:
    """
    Dedicated educational panel allowing viewers to inspect data during transmission:
    - Original message
    - Encapsulated data
    - Simulated headers breakdown
    - Encoded / encrypted hex representation
    - Bitstream representation
    - Decapsulated message
    """
    table = Table(box=box.SIMPLE, expand=True)
    table.add_column("Property", style="bold white", width=22)
    table.add_column("Inspection Value", style="bright_cyan")

    table.add_row("Original Message", f"\"{fbreak['message']}\" ({fbreak['msg_len']} bytes)")
    table.add_row("Presentation Cipher", f"XOR 0xAB: {to_hex_sample(fbreak['xor_sample'])}")
    table.add_row("Simulated Headers (7)", f"128 Bytes Packed Structs (App:18, Pres:17, Sess:5, TCP:9, IP:34, Eth:40, Phys:5)")
    table.add_row("Data Link FCS", f"0x{fbreak['sim_fcs']:04X} (Simple Additive 16-bit Checksum)")
    table.add_row("Physical Bitstream", f"{fbreak['total_bits']} bits: {to_bit_sample(fbreak['xor_sample'])}")
    table.add_row("Total Wire Frame", f"{fbreak['total_frame_len']} Bytes Total")

    if stage == "DONE":
        table.add_row("Decapsulated Message", f"[bold bright_green]\"{fbreak['message']}\" (100% Integrity Verified)[/bold bright_green]")
    else:
        table.add_row("Decapsulated Message", "[dim]Awaiting complete decapsulation...[/dim]")

    return Panel(
        table,
        title="[bold bright_green]🔍 Educational Data & Bitstream Inspection Panel[/bold bright_green]",
        box=box.ROUNDED,
        border_style="green",
        padding=(0, 1),
    )

# ─── Live Animation Engine ───────────────────────────────────────────────────

def safe_prompt(prompt_text: str, choices: Optional[List[str]] = None, default: str = "") -> str:
    """Safe prompt wrapper handling EOFError and non-interactive environments."""
    try:
        if not sys.stdin or not sys.stdin.isatty():
            return default
        return Prompt.ask(prompt_text, choices=choices, default=default)
    except Exception:
        return default

def get_delay() -> float:
    """Returns current animation delay in seconds."""
    global current_speed_key
    name, sec = SPEED_PRESETS.get(current_speed_key, ("Standard", 0.55))
    return sec

def execute_simulation_run(message: str):
    """
    Executes the full professional animated simulation:
    1. Checks/compiles server.exe and client.exe
    2. Spawns server.exe in background
    3. Runs step-by-step Client Encapsulation animation
    4. Runs client.exe to execute real socket transmission
    5. Runs step-by-step Server Decapsulation animation
    6. Confirms message recovery and displays completion banner
    """
    console.clear()

    # Step 0: Ensure binaries exist
    if not (os.path.isfile(SERVER_EXE) and os.path.isfile(CLIENT_EXE)):
        console.print("[bold yellow]Compiled executables not found. Attempting to build...[/bold yellow]")
        if os.path.isfile(BUILD_BAT):
            ret = subprocess.run([BUILD_BAT], shell=True, cwd=SCRIPT_DIR)
            if ret.returncode != 0:
                console.print("[bold red]Build failed. Please verify GCC installation in build.bat.[/bold red]")
                Prompt.ask("\nPress Enter to return to menu")
                return
        else:
            console.print("[bold red]server.exe or client.exe missing and build.bat not found.[/bold red]")
            Prompt.ask("\nPress Enter to return to menu")
            return

    fbreak = get_simulated_frame_breakdown(message)
    delay = get_delay()

    # ── PHASE 1: Launch Server in Background ──
    srv_proc = subprocess.Popen(
        [SERVER_EXE],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=SCRIPT_DIR
    )
    time.sleep(0.4) # Wait for server to bind port 9090

    # ── PHASE 2: Client Encapsulation Animation (L7 -> L1) ──
    completed_encap = []
    encap_order = [7, 6, 5, 4, 3, 2, 1]

    for step_idx, lnum in enumerate(encap_order):
        console.clear()
        banner = render_banner(f"Client Encapsulating Layer {lnum} ({OSI_LAYERS[lnum]['name']})")
        zigzag = render_zigzag_stack("ENCAP", lnum, completed_encap, step_idx, message)
        detail = render_layer_detail_card(lnum, "ENCAP", fbreak)
        box_panel = render_packet_structure_box("ENCAP", lnum, message)
        prog = render_two_layer_progress("ENCAP", lnum, completed_encap)
        inspect = render_educational_data_panel(fbreak, "ENCAP")

        top_cols = Columns([zigzag, detail], expand=True)
        bottom_cols = Columns([box_panel, inspect], expand=True)

        console.print(banner)
        console.print(top_cols)
        console.print(bottom_cols)
        console.print(prog)

        if delay > 0:
            time.sleep(delay)
        else:
            safe_prompt("\n[bold yellow]Step-by-Step Mode: Press [Enter] for next layer...[/bold yellow]")

        completed_encap.append(lnum)

    # Final encapsulation summary step
    console.clear()
    banner = render_banner("Client Encapsulation Complete — 143-Byte Frame Ready for Wire")
    zigzag = render_zigzag_stack("ENCAP", 0, completed_encap, 7, message)
    detail = render_layer_detail_card(1, "ENCAP", fbreak)
    box_panel = render_packet_structure_box("ENCAP", 1, message)
    prog = render_two_layer_progress("ENCAP", 0, completed_encap)
    inspect = render_educational_data_panel(fbreak, "ENCAP")

    console.print(banner)
    console.print(Columns([zigzag, detail], expand=True))
    console.print(Columns([box_panel, inspect], expand=True))
    console.print(prog)
    if delay > 0:
        time.sleep(delay * 0.8)

    # ── PHASE 3: Real TCP Socket Wire Transmission ──
    for p in range(8):
        console.clear()
        banner = render_banner("Transmitting Encapsulated Frame over TCP Socket (Port 9090)...")
        wire = render_socket_transmission_wire(p * 3, fbreak["total_frame_len"])
        inspect = render_educational_data_panel(fbreak, "WIRE")

        console.print(banner)
        console.print(wire)
        console.print(inspect)
        time.sleep(0.12)

    # Run the real client executable to transmit the message over the socket!
    cli_proc = subprocess.run(
        [CLIENT_EXE, message],
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR,
        timeout=10
    )
    time.sleep(0.3)

    # ── PHASE 4: Server Decapsulation Animation (L1 -> L7) ──
    completed_decap = []
    decap_order = [1, 2, 3, 4, 5, 6, 7]

    for step_idx, lnum in enumerate(decap_order):
        console.clear()
        banner = render_banner(f"Server Decapsulating Layer {lnum} ({OSI_LAYERS[lnum]['name']})")
        zigzag = render_zigzag_stack("DECAP", lnum, completed_decap, step_idx, message)
        detail = render_layer_detail_card(lnum, "DECAP", fbreak)
        box_panel = render_packet_structure_box("DECAP", lnum, message)
        prog = render_two_layer_progress("DECAP", lnum, completed_decap)
        inspect = render_educational_data_panel(fbreak, "DECAP")

        console.print(banner)
        console.print(Columns([zigzag, detail], expand=True))
        console.print(Columns([box_panel, inspect], expand=True))
        console.print(prog)

        if delay > 0:
            time.sleep(delay)
        else:
            safe_prompt("\n[bold yellow]Step-by-Step Mode: Press [Enter] for next layer...[/bold yellow]")

        completed_decap.append(lnum)

    # Wait for server process to finish
    try:
        srv_stdout, _ = srv_proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        srv_proc.kill()
        srv_stdout = ""

    # ── PHASE 5: Prominent SUCCESS Banner & Verification ──
    console.clear()
    banner = render_banner("TRANSMISSION SUCCESSFUL — MESSAGE RECOVERED WITH 100% FIDELITY")
    zigzag = render_zigzag_stack("DECAP", 0, completed_decap, 7, message)
    prog = render_two_layer_progress("DECAP", 0, completed_decap)
    inspect = render_educational_data_panel(fbreak, "DONE")

    success_text = Text()
    success_text.append("\n  ✔ 7-LAYER OSI ENCAPSULATION & DECAPSULATION COMPLETED SUCCESSFULLY\n\n", style="bold bright_green")
    success_text.append(f"  • Sent by Client   : \"{message}\"\n", style="bright_cyan")
    success_text.append(f"  • Received by Server: \"{message}\"\n", style="bold bright_green")
    success_text.append(f"  • Data Link FCS     : 0x{fbreak['sim_fcs']:04X} [OK — Frame Integrity Verified]\n", style="bright_yellow")
    success_text.append(f"  • Physical Bits     : {fbreak['total_bits']} bits (Manchester Line Encoded)\n", style="white")
    success_text.append(f"  • Socket Delivery   : 127.0.0.1:50000 ──[TCP]──▶ 127.0.0.1:9090 (ACK Received)\n\n", style="bright_white")

    success_panel = Panel(
        Align.center(success_text),
        title="[bold bright_green]🏆 SIMULATION SUCCESS CONFIRMATION[/bold bright_green]",
        box=box.DOUBLE,
        border_style="bright_green",
        padding=(0, 2)
    )

    console.print(banner)
    console.print(Columns([zigzag, inspect], expand=True))
    console.print(success_panel)
    console.print(prog)

    safe_prompt("\n[bold cyan]Press [Enter] to return to Main Menu...[/bold cyan]")

# ─── Reference & Guide Menus ──────────────────────────────────────────────────

def display_educational_guide():
    """Renders comprehensive educational reference on all 7 OSI layers."""
    console.clear()
    console.print(render_banner("OSI 7-Layer Theoretical vs Implementation Reference Guide"))

    table = Table(
        box=box.ROUNDED,
        border_style="bright_blue",
        title="[bold bright_white]Comprehensive OSI 7-Layer Architecture Overview[/bold bright_white]",
        expand=True
    )
    table.add_column("Layer", justify="center", width=7, style="bold cyan")
    table.add_column("Name", width=14, style="bold bright_white")
    table.add_column("PDU Unit", width=16, style="bright_yellow")
    table.add_column("Primary Responsibility", width=34)
    table.add_column("Key Protocols / Examples", width=22, style="bright_green")

    for lnum in [7, 6, 5, 4, 3, 2, 1]:
        layer = OSI_LAYERS[lnum]
        examples = {
            7: "HTTP, HTTPS, FTP, DNS",
            6: "TLS, SSL, ASCII, JPEG",
            5: "NetBIOS, RPC, Sockets",
            4: "TCP, UDP, SCTP",
            3: "IPv4, IPv6, ICMP, BGP",
            2: "Ethernet (802.3), Wi-Fi",
            1: "Cat6 Copper, Fiber, 100BASE-T"
        }[lnum]

        table.add_row(
            f"L{lnum}",
            f"{layer['icon']} {layer['name']}",
            layer['pdu'],
            layer['role'],
            examples
        )

    console.print(table)

    comp_panel = Panel(
        """[bold bright_white]OSI Model vs TCP/IP Architecture Comparison:[/bold bright_white]
• The theoretical ISO/OSI 7-Layer model strictly separates Application (L7), Presentation (L6), and Session (L5).
• In the practical TCP/IP stack (Internet Protocol Suite), Layers 5, 6, and 7 are collapsed into a single Application Layer.
• In this simulation, client.c and server.c implement the full 7-layer architecture using packed C structures,
  distinguishing application encryption (L6) and session management (L5) before passing segments to the operating system's real TCP/IP stack.""",
        box=box.ROUNDED,
        border_style="yellow",
        padding=(0, 1)
    )
    console.print(comp_panel)
    safe_prompt("\n[bold cyan]Press [Enter] to return to Main Menu...[/bold cyan]")

def display_frame_architecture():
    """Displays byte-by-byte layout of the 128-byte header frame structure."""
    console.clear()
    console.print(render_banner("Binary Frame Architecture & C Struct Breakdown"))

    table = Table(
        box=box.ROUNDED,
        border_style="magenta",
        title="[bold bright_white]OSI Packed Binary Frame Layout (#pragma pack(1))[/bold bright_white]",
        expand=True
    )
    table.add_column("Offset", justify="center", width=12, style="yellow")
    table.add_column("Header Struct", width=18, style="bold cyan")
    table.add_column("Size (Bytes)", justify="center", width=14, style="bright_white")
    table.add_column("Key Fields & Parameters", width=36)
    table.add_column("OSI Layer", width=16, style="bright_green")

    rows = [
        ("0 - 4",     "PhysHeader",  "5 Bytes",  "bit_count (uint32), encoding_type (uint8)", "Layer 1: Physical"),
        ("5 - 44",    "DLHeader",    "40 Bytes", "src_mac[18], dst_mac[18], ether_type, fcs",  "Layer 2: Data Link"),
        ("45 - 78",   "NetHeader",   "34 Bytes", "src_ip[16], dst_ip[16], ttl (64), proto",   "Layer 3: Network"),
        ("79 - 87",   "TransHeader", "9 Bytes",  "src_port (50000), dst_port (9090), seq",    "Layer 4: Transport"),
        ("88 - 92",   "SessHeader",  "5 Bytes",  "session_id (0xDEADBEEF), dialog_control",    "Layer 5: Session"),
        ("93 - 109",  "PresHeader",  "17 Bytes", "encoding[16] ('ASCII'), encrypted (1)",     "Layer 6: Presentation"),
        ("110 - 127", "AppHeader",   "18 Bytes", "protocol[16] ('HTTP'), data_len",           "Layer 7: Application"),
        ("128 - End", "Payload Data", "N Bytes",  "XOR-Encrypted user payload string",        "User Application Data")
    ]

    for r in rows:
        table.add_row(*r)

    console.print(table)
    console.print(Panel(
        "[bold bright_white]Total Header Overhead:[/bold bright_white] 128 Bytes.\n"
        "[bold yellow]Total Frame Size for 15-byte message:[/bold yellow] 128 + 15 = 143 Bytes.\n"
        "[bold cyan]Structure Packing:[/bold cyan] Enforced with [bold]__attribute__((packed))[/bold] or [bold]#pragma pack(push, 1)[/bold] to guarantee identical binary offsets across client.c and server.c.",
        box=box.ROUNDED,
        border_style="cyan"
    ))
    safe_prompt("\n[bold cyan]Press [Enter] to return to Main Menu...[/bold cyan]")

def change_speed_menu():
    """Allows user to change animation speed."""
    global current_speed_key
    console.clear()
    console.print(render_banner("Configure Simulation Animation Speed"))

    table = Table(box=box.ROUNDED, border_style="yellow", title="Animation Speed Presets")
    table.add_column("Option", justify="center", width=8, style="bold cyan")
    table.add_column("Preset Name", width=26, style="bright_white")
    table.add_column("Delay Per Layer", width=18, style="bright_green")
    table.add_column("Current", justify="center", width=10)

    for k, (name, delay) in SPEED_PRESETS.items():
        delay_str = f"{delay}s" if delay > 0 else "Manual (Enter)"
        cur_str = "[bold green]✔ ACTIVE[/bold green]" if k == current_speed_key else ""
        table.add_row(k, name, delay_str, cur_str)

    console.print(table)
    choice = safe_prompt("\nSelect speed preset (1-4)", choices=["1", "2", "3", "4"], default=current_speed_key)
    current_speed_key = choice
    console.print(f"[bold green]Animation speed set to: {SPEED_PRESETS[choice][0]}[/bold green]")
    time.sleep(0.7)

# ─── Main Interactive Dashboard Loop ──────────────────────────────────────────

def main_menu():
    """Main dashboard menu loop."""
    default_msg = "Hello OSI World!"

    while True:
        console.clear()
        console.print(render_banner("Interactive Terminal Dashboard & Control Console"))

        menu_table = Table(box=box.ROUNDED, border_style="bright_blue", expand=True)
        menu_table.add_column("Option", justify="center", width=10, style="bold cyan")
        menu_table.add_column("Action / Feature", style="bright_white")
        menu_table.add_column("Description", style="dim white")

        menu_table.add_row("[1]", "Run Simulation (Default Message)", f"Simulate with: \"{default_msg}\"")
        menu_table.add_row("[2]", "Run Simulation with Custom Message", "Input any custom text payload to encapsulate")
        menu_table.add_row("[3]", "Configure Animation Speed", f"Current speed: {SPEED_PRESETS[current_speed_key][0]}")
        menu_table.add_row("[4]", "OSI 7-Layer Educational Reference", "Explore protocols, PDU definitions & theoretical stacks")
        menu_table.add_row("[5]", "Inspect Binary Frame Architecture", "Examine 128-byte packed C header structures")
        menu_table.add_row("[6]", "Exit Application", "Terminate visualizer safely")

        console.print(menu_table)

        choice = safe_prompt("\nEnter selection [1-6]", choices=["1", "2", "3", "4", "5", "6"], default="1")

        if choice == "1":
            execute_simulation_run(default_msg)
        elif choice == "2":
            user_msg = safe_prompt("\nEnter custom message to send", default="Networking Lab Live Demo!")
            if not user_msg.strip():
                console.print("[bold red]Empty message rejected. Please enter a valid message.[/bold red]")
                time.sleep(1)
                continue
            execute_simulation_run(user_msg.strip())
        elif choice == "3":
            change_speed_menu()
        elif choice == "4":
            display_educational_guide()
        elif choice == "5":
            display_frame_architecture()
        elif choice == "6":
            console.print("\n[bold bright_green]Thank you for using the OSI 7-Layer Simulation System! Goodbye.[/bold bright_green]\n")
            break

# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        # Check if direct message was passed as CLI argument
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            cli_msg = " ".join(sys.argv[1:])
            execute_simulation_run(cli_msg)
        else:
            main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Simulation interrupted by user (Ctrl+C). Terminating safely...[/bold yellow]")
        sys.exit(0)
