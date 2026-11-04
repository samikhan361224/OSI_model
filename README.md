# Professional OSI 7-Layer Communication Simulation

A high-level, interactive, educational, terminal-based **OSI 7-Layer Networking Simulation**. Developed with a **C-based Client & Server** communicating over real **TCP sockets** using packed binary protocol data units (PDUs), accompanied by an animated **Python Rich Visualizer** featuring zig-zag data flow, live progress checkpoints after every two layers, and deep protocol inspection.

> **Project Author:** Akib Jawad  
> **Architecture:** C Client (Encapsulation) ➔ TCP Stream Socket (Port 9090) ➔ C Server (Decapsulation)  
> **Visualization:** Python 3 + `rich` (Dashboard Layout, Live Zig-Zag Animation, Progress Tracking)

---

## 🌟 Key Features

1. **Full 7-Layer OSI Simulation in C**:
   - Implements **Application (L7)** down to **Physical (L1)** on the Client (Encapsulation).
   - Implements **Physical (L1)** up to **Application (L7)** on the Server (Decapsulation).
   - Real TCP socket communication on `127.0.0.1:9090` using Windows Sockets 2 (`ws2_32`).
2. **Animated Zig-Zag Data Flow**:
   - Alternating directional paths between layers (`═════════════▶` and `◀═════════════`).
   - Active layer highlights, completed layer markers (`✔`), and pending layers (`○`).
3. **Mandatory 2-Layer Progress Tracking (Exact Specification)**:
   - Progress checkpoints after every two OSI layers (mimicking Linux/Ubuntu network stack packet processing):
     - **Client Side (Encapsulation)**:
       - L7 + L6 Complete ➔ `2/7 (28%)` [Application + Presentation]
       - L5 + L4 Complete ➔ `4/7 (57%)` [Session + Transport]
       - L3 + L2 Complete ➔ `6/7 (85%)` [Network + Data Link]
       - L1 Complete      ➔ `7/7 (100%)` [Physical Bitstream Ready]
     - **Server Side (Decapsulation)**:
       - L1 + L2 Complete ➔ `2/7 (28%)` [Physical + Data Link]
       - L3 + L4 Complete ➔ `4/7 (57%)` [Network + Transport]
       - L5 + L6 Complete ➔ `6/7 (85%)` [Session + Presentation]
       - L7 Complete      ➔ `7/7 (100%)` [Application Message Delivered]
4. **Educational Layer Inspection & Protocol Explanations**:
   - Detailed educational breakdown cards for each layer.
   - Clear distinction between simulated OSI headers and host operating system socket encapsulation.
5. **Progressive Packet Structure Box**:
   - Visual inspection of the growing/shrinking frame: `[App | Payload]` ➔ `[Pres | App | Payload]` ➔ `...` ➔ `[Phys Frame: 143 Bytes]`.
6. **Live Data & Bitstream Inspection Panel**:
   - Inspects original text, XOR encryption (`0xAB`), 128 bytes of headers, 16-bit FCS checksum, and Manchester bitstream.
7. **Interactive Dashboard Controls**:
   - Menu choices: Run default message, custom message input, configurable animation speed (Slow, Normal, Fast, Step-by-Step), and OSI theoretical reference guide.

---

## 📁 Project Architecture & File Structure

```
d:\OSI model project/
├── osi_layers.h        # Common header: packed C structs for all 7 OSI headers & checksum
├── client.c            # C Client: 7-layer encapsulation & TCP socket transmission
├── server.c            # C Server: TCP listener & 7-layer decapsulation
├── osi_visualizer.py   # Python Rich terminal visualization & dashboard
├── build.bat           # MinGW GCC build script for server.exe and client.exe
├── run.bat             # Auto-dependency installer & visualizer launcher
├── client.exe          # Compiled client binary (included for convenience)
└── server.exe          # Compiled server binary (included for convenience)
```

---

## 📦 Binary Frame Architecture (`#pragma pack(1)`)

The 7-layer frame consists of **128 bytes of simulated headers** prepended to the user payload:

| Byte Offset | Header Struct | Size | Fields & Parameters | OSI Layer |
|:---:|:---:|:---:|:---|:---:|
| `0 - 4` | `PhysHeader` | 5 B | `bit_count` (uint32), `encoding_type` (uint8: Manchester) | **Layer 1: Physical** |
| `5 - 44` | `DLHeader` | 40 B | `src_mac[18]`, `dst_mac[18]`, `ether_type` (0x0800), `fcs` (checksum) | **Layer 2: Data Link** |
| `45 - 78` | `NetHeader` | 34 B | `src_ip[16]`, `dst_ip[16]`, `ttl` (64), `protocol` (6: TCP) | **Layer 3: Network** |
| `79 - 87` | `TransHeader`| 9 B | `src_port` (50000), `dst_port` (9090), `seq_num` (1000), `protocol` | **Layer 4: Transport** |
| `88 - 92` | `SessHeader` | 5 B | `session_id` (0xDEADBEEF), `dialog_control` (1: Full-Duplex) | **Layer 5: Session** |
| `93 - 109`| `PresHeader` | 17 B | `encoding[16]` ("ASCII"), `encrypted` (1: XOR 0xAB) | **Layer 6: Presentation** |
| `110 - 127`| `AppHeader` | 18 B | `protocol[16]` ("HTTP"), `data_len` (Payload length) | **Layer 7: Application** |
| `128 - End`| **Payload** | N B | XOR-encrypted user application text message | **Application Data** |

**Total Frame Size** = `128 Bytes + Payload Length` (e.g. 15 bytes message ➔ **143 Bytes**).

---

## 🚀 Installation & Prerequisites

### 1. Requirements
- **Windows 10 / 11**
- **Python 3.8+** (available via `py` or `python` command)
- **MinGW GCC** (required only if modifying `.c` source files; pre-compiled `.exe` binaries are already included)

### 2. Install Python Dependencies
Run the following command to install the required `rich` terminal library:
```bat
py -m pip install rich
```

*(Note: `run.bat` automatically checks and installs `rich` if it is not already present).*

---

## 💻 How to Run

### Method 1: Interactive Dashboard Launcher (Recommended)
Simply run `run.bat` or launch the Python script:
```bat
cd "d:\OSI model project"
run.bat
```
or
```bat
py osi_visualizer.py
```
This presents an interactive menu with options to run simulations, customize messages, change speed presets, inspect frame bytes, and view educational references.

### Method 2: Direct One-Shot Run with Custom Message
You can pass your message directly on the command line:
```bat
py osi_visualizer.py "Hello from Akib Jawad!"
```

### Method 3: Manual Direct C Sockets Execution (Two Terminals)
To verify the raw C sockets communication without visualization:

**Terminal 1 (Start Server First):**
```bat
cd "d:\OSI model project"
server.exe
```

**Terminal 2 (Run Client):**
```bat
cd "d:\OSI model project"
client.exe "Live Socket Communication Test"
```

---

## 🛠️ Recompiling C Binaries
If you make any changes to `server.c`, `client.c`, or `osi_layers.h`:
```bat
build.bat
```
This automatically locates GCC (PATH, `C:\MinGW\bin\gcc.exe`, or MSYS2) and compiles both executables with `-lws2_32`.

---

## 🎓 Educational Note: Real vs. Simulated Networking
In standard operating systems (such as Windows or Linux):
- **Layers 7, 6, and 5** run in user space (Application code, TLS/SSL libraries, session tokens).
- **Layer 4 and 3** are handled by the OS kernel network stack (TCP/IP driver).
- **Layers 2 and 1** are managed by Network Interface Card (NIC) firmware and physical transceivers.

*In this educational project, client and server explicitly simulate all seven distinct OSI headers inside a binary packed protocol data unit before streaming the raw byte frame across a real TCP loopback socket, providing full visibility into every layer's theoretical and practical responsibilities.*

---

## 📜 Submission Details
- **Student / Author**: Akib Jawad
- **GitHub Repository**: [https://github.com/samikhan361224/OSI_model](https://github.com/samikhan361224/OSI_model)
- **Task Reference**: [jsramesh1990/OSI_Communication_Simulation_Project](https://github.com/jsramesh1990/OSI_Communication_Simulation_Project)
