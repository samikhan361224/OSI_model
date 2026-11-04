/*
 * server.c
 * OSI Model Simulation – SERVER side
 *
 * Receives a fully-encapsulated frame from the client and
 * performs 7-layer DECAPSULATION (Physical → Data Link → Network →
 * Transport → Session → Presentation → Application).
 *
 * Compile (Windows/MinGW):
 *   gcc server.c -o server.exe -lws2_32
 *
 * Frame layout received:
 *   [PhysHdr][DLHdr][NetHdr][TransHdr][SessHdr][PresHdr][AppHdr][payload]
 * We walk a pointer forward through the buffer, peeling each header.
 */

#include <winsock2.h>
#include <windows.h>
#include <ws2tcpip.h>
#include "osi_layers.h"

#pragma comment(lib, "ws2_32.lib")

/*
 * recv_cursor / recv_end: pointers into the receive buffer.
 * Each decapsulation function advances recv_cursor past its header.
 */
static char  recv_buf[MAX_FRAME_LEN];
static char *cur;    /* current read position */
static char *end;    /* one past last received byte */

#define REMAINING  ((int)(end - cur))

/* Consume 'size' bytes from front and return a pointer to them */
static void *consume(int size) {
    void *p = cur;
    cur += size;
    return p;
}

/* ═══════════════════════════════════════════════════════════════════════════
   DECAPSULATION  (Layers 1 → 7)
   ═══════════════════════════════════════════════════════════════════════════ */

/* Layer 1 – Physical */
void layer1_receive(void) {
    print_layer_banner("SERVER", LAYER_PHYSICAL, "Physical", "DECAPSULATION - converting bits to frame");
    PhysHeader *hdr = (PhysHeader *)consume(sizeof(PhysHeader));
    printf("  Bit count      : %u\n", hdr->bit_count);
    printf("  Encoding type  : %s\n", hdr->encoding_type == 1 ? "Manchester" : "NRZ");
    printf("  >> Bits converted to raw frame (%d bytes remain)\n", REMAINING);
}

/* Layer 2 – Data Link */
void layer2_receive(void) {
    print_layer_banner("SERVER", LAYER_DATALINK, "Data Link", "DECAPSULATION - verifying frame integrity");
    DLHeader *hdr = (DLHeader *)consume(sizeof(DLHeader));
    printf("  Source MAC     : %s\n", hdr->src_mac);
    printf("  Dest MAC       : %s\n", hdr->dst_mac);
    printf("  EtherType      : 0x%04X\n", hdr->ether_type);

    /* Verify FCS over remaining payload */
    uint16_t calc_fcs = simple_checksum(cur, REMAINING);
    printf("  FCS (received) : 0x%04X\n", hdr->fcs);
    printf("  FCS (computed) : 0x%04X  %s\n", calc_fcs,
           (calc_fcs == hdr->fcs) ? "[OK]" : "[MISMATCH]");
    printf("  >> Frame integrity verified (%d bytes remain)\n", REMAINING);
}

/* Layer 3 – Network */
void layer3_receive(void) {
    print_layer_banner("SERVER", LAYER_NETWORK, "Network", "DECAPSULATION - reading IP packet");
    NetHeader *hdr = (NetHeader *)consume(sizeof(NetHeader));
    printf("  Source IP      : %s\n", hdr->src_ip);
    printf("  Dest IP        : %s\n", hdr->dst_ip);
    printf("  TTL            : %d\n", hdr->ttl);
    printf("  Protocol       : %s\n", hdr->protocol == 6 ? "TCP" : "UDP");
    printf("  >> IP header stripped (%d bytes remain)\n", REMAINING);
}

/* Layer 4 – Transport */
void layer4_receive(void) {
    print_layer_banner("SERVER", LAYER_TRANSPORT, "Transport", "DECAPSULATION - reading TCP segment");
    TransHeader *hdr = (TransHeader *)consume(sizeof(TransHeader));
    printf("  Source Port    : %d\n", hdr->src_port);
    printf("  Dest Port      : %d\n", hdr->dst_port);
    printf("  Sequence #     : %u\n", hdr->seq_num);
    printf("  Protocol       : %s\n", hdr->protocol == 6 ? "TCP" : "UDP");
    printf("  >> Transport header stripped (%d bytes remain)\n", REMAINING);
}

/* Layer 5 – Session */
void layer5_receive(void) {
    print_layer_banner("SERVER", LAYER_SESSION, "Session", "DECAPSULATION - reading session info");
    SessHeader *hdr = (SessHeader *)consume(sizeof(SessHeader));
    printf("  Session ID     : 0x%08X\n", hdr->session_id);
    printf("  Dialog Control : %s\n", hdr->dialog_control ? "Full-Duplex" : "Half-Duplex");
    printf("  >> Session header stripped (%d bytes remain)\n", REMAINING);
}

/* Layer 6 – Presentation */
void layer6_receive(void) {
    print_layer_banner("SERVER", LAYER_PRESENTATION, "Presentation", "DECAPSULATION - decoding/decrypting data");
    PresHeader *hdr = (PresHeader *)consume(sizeof(PresHeader));
    printf("  Encoding       : %s\n", hdr->encoding);
    printf("  Encrypted      : %s\n", hdr->encrypted ? "Yes (XOR)" : "No");

    if (hdr->encrypted) {
        /* Decrypt the remaining payload (AppHdr + data) in-place */
        xor_data(cur, REMAINING, 0xAB);
        printf("  >> Data decrypted with XOR key 0xAB\n");
    }
    printf("  >> Presentation header stripped (%d bytes remain)\n", REMAINING);
}

/* Layer 7 – Application */
void layer7_receive(void) {
    print_layer_banner("SERVER", LAYER_APPLICATION, "Application", "DECAPSULATION - reading application data");
    AppHeader *hdr = (AppHeader *)consume(sizeof(AppHeader));
    printf("  Protocol       : %s\n", hdr->protocol);
    printf("  Data Length    : %d bytes\n", hdr->data_len);

    /* Remaining bytes are the payload */
    int payload_len = REMAINING;
    char message[MAX_DATA_LEN + 1];
    int copy_len = payload_len < MAX_DATA_LEN ? payload_len : MAX_DATA_LEN;
    memcpy(message, cur, copy_len);
    message[copy_len] = '\0';

    printf("\n  ╔══════════════════════════════════════════════╗\n");
    printf("  ║  MESSAGE RECEIVED: %-26s║\n", message);
    printf("  ╚══════════════════════════════════════════════╝\n");
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN – accept one connection, decapsulate in full
   ═══════════════════════════════════════════════════════════════════════════ */
int main(void) {
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) {
        fprintf(stderr, "WSAStartup failed\n"); return 1;
    }

    SOCKET srv = socket(AF_INET, SOCK_STREAM, 0);
    if (srv == INVALID_SOCKET) {
        fprintf(stderr, "socket() failed: %d\n", WSAGetLastError());
        WSACleanup(); return 1;
    }

    int opt = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, (char *)&opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port        = htons(SERVER_PORT);

    if (bind(srv, (struct sockaddr *)&addr, sizeof(addr)) == SOCKET_ERROR) {
        fprintf(stderr, "bind() failed: %d\n", WSAGetLastError());
        closesocket(srv); WSACleanup(); return 1;
    }

    listen(srv, 1);
    printf("╔═══════════════════════════════════════════════════════════╗\n");
    printf("║          OSI MODEL SIMULATION  –  SERVER                  ║\n");
    printf("╚═══════════════════════════════════════════════════════════╝\n");
    printf("  Listening on %s:%d ...\n", SERVER_ADDR, SERVER_PORT);

    struct sockaddr_in cli_addr;
    int cli_len = sizeof(cli_addr);
    SOCKET cli = accept(srv, (struct sockaddr *)&cli_addr, &cli_len);
    if (cli == INVALID_SOCKET) {
        fprintf(stderr, "accept() failed: %d\n", WSAGetLastError());
        closesocket(srv); WSACleanup(); return 1;
    }
    printf("  Client connected!\n");

    /* Receive 4-byte length prefix */
    uint32_t total_len_net = 0;
    {
        int got = 0;
        while (got < 4) {
            int r = recv(cli, ((char *)&total_len_net) + got, 4 - got, 0);
            if (r <= 0) { fprintf(stderr, "recv length failed\n"); goto cleanup; }
            got += r;
        }
    }
    int total_len = (int)ntohl(total_len_net);
    printf("  Total frame size received: %d bytes\n", total_len);

    /* Receive full frame */
    memset(recv_buf, 0, sizeof(recv_buf));
    {
        int received = 0;
        while (received < total_len) {
            int r = recv(cli, recv_buf + received, total_len - received, 0);
            if (r <= 0) break;
            received += r;
        }
        cur = recv_buf;
        end = recv_buf + received;
    }

    printf("\n════════════════════════════════════════════════════════════\n");
    printf("  BEGIN 7-LAYER DECAPSULATION (Layers 1 → 7)\n");
    printf("════════════════════════════════════════════════════════════\n");

    layer1_receive();
    layer2_receive();
    printf("\n  [PROGRESS] Layers 1-2 complete (Physical + Data Link)\n");

    layer3_receive();
    layer4_receive();
    printf("\n  [PROGRESS] Layers 3-4 complete (Network + Transport)\n");

    layer5_receive();
    layer6_receive();
    printf("\n  [PROGRESS] Layers 5-6 complete (Session + Presentation)\n");

    layer7_receive();
    printf("\n  [PROGRESS] Layer 7 complete (Application) – DONE!\n");

    printf("\n════════════════════════════════════════════════════════════\n");
    printf("  DECAPSULATION COMPLETE\n");
    printf("════════════════════════════════════════════════════════════\n\n");

    /* Send ACK */
    const char *ack = "ACK:OSI_SIM_OK";
    send(cli, ack, (int)strlen(ack), 0);

cleanup:
    closesocket(cli);
    closesocket(srv);
    WSACleanup();
    return 0;
}
