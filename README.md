# OSI Layer Simulation – Live Project

A **C-based client/server** application implementing full **7-layer OSI encapsulation and decapsulation** using real socket communication, with a **Python visualizer** that renders the zig-zag data flow and prints progress after every two layers.

---

## Project Structure

```
OSI model project/
├── osi_layers.h        # Shared header: OSI struct definitions, utilities
├── client.c            # C client – 7-layer ENCAPSULATION (L7 → L1)
├── server.c            # C server – 7-layer DECAPSULATION (L1 → L7)
├── osi_visualizer.py   # Python user app – launches & visualizes both sides
├── build.bat           # Compile client.exe & server.exe (MinGW GCC)
├── run.bat             # Build if needed, then launch visualizer
├── client.exe          # (compiled)
└── server.exe          # (compiled)
```

---

## How It Works

### OSI Encapsulation (CLIENT – Layers 7 → 1)

| Layer | Name         | Action                                     | Header Added               |
|-------|--------------|--------------------------------------------|----------------------------|
| 7     | Application  | Wraps message in HTTP PDU                  | Protocol, data length      |
| 6     | Presentation | XOR-encrypts payload (key `0xAB`)          | Encoding type, encrypt flag|
| 5     | Session      | Establishes session context                | Session ID, dialog control |
| 4     | Transport    | Creates TCP segment                        | Src/dst ports, seq number  |
| 3     | Network      | Adds IP routing information                | Src/dst IP, TTL, protocol  |
| 2     | Data Link    | Builds Ethernet frame + FCS checksum       | Src/dst MAC, EtherType, FCS|
| 1     | Physical     | Converts to bit-stream (Manchester coding) | Bit count, encoding type   |

### OSI Decapsulation (SERVER – Layers 1 → 7)

Server strips each header in reverse order, verifying integrity at Layer 2 (FCS check) and decrypting at Layer 6 before delivering the original message at Layer 7.

### Progress Checkpoints (Every 2 Layers)

Printed after layers 7-6, 5-4, 3-2, and 1 on the client side, and after layers 1-2, 3-4, 5-6, and 7 on the server side — mimicking Linux/Ubuntu networking stack behavior.

---

## Build & Run

### Prerequisites
- **MinGW GCC** (available at `C:\MinGW\bin\gcc.exe`)
- **Python 3** (available via `py` launcher)

### Quick Start

```bat
run.bat
```

Or manually:

```bat
:: Step 1: Compile
build.bat

:: Step 2: Run visualizer (launches server + client automatically)
py osi_visualizer.py "Your custom message here"

:: Or run server and client manually in two terminals:
server.exe
client.exe "Hello OSI World"
```

---

## Sample Output

### Client (Encapsulation)
```
[CLIENT] Layer 7 (Application) - ENCAPSULATION - creating application data
  Protocol       : HTTP
  Data Length    : 15 bytes
  Payload        : "Hello OSI World"

  [PROGRESS] Layers 7-6 complete (Application + Presentation)
  ...
  ENCAPSULATION COMPLETE – Total frame: 143 bytes
```

### Server (Decapsulation)
```
[SERVER] Layer 2 (Data Link) - DECAPSULATION - verifying frame integrity
  Source MAC     : AA:BB:CC:DD:EE:FF
  FCS (received) : 0x24D3
  FCS (computed) : 0x24D3  [OK]
  ...
  ╔══════════════════════════════════════════════╗
  ║  MESSAGE RECEIVED: Hello OSI World           ║
  ╚══════════════════════════════════════════════╝
```

---

## Technical Details

- **Language**: C (client/server), Python 3 (visualizer)
- **Socket**: TCP/IP on `127.0.0.1:9090` with real Winsock2 sockets
- **Frame format**: Binary packed structs (`#pragma pack(1)`) sent over the wire
- **Encryption**: XOR cipher with key `0xAB` at Presentation layer
- **Integrity**: 16-bit additive checksum (FCS) at Data Link layer
- **Frame size**: 143 bytes for a 15-byte message (128 bytes of headers)

---

## References
- [The OSI Model Explained – dev.to](https://dev.to/iaadidev/the-osi-model-explained-key-layers-in-computer-networking-53b7)
- Based on: [jsramesh1990/OSI_Communication_Simulation_Project](https://github.com/jsramesh1990/OSI_Communication_Simulation_Project)
