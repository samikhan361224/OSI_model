/*
 * client.c
 * OSI Model Simulation – CLIENT side
 *
 * Takes a user message and performs 7-layer ENCAPSULATION
 * (Application → Presentation → Session → Transport → Network →
 *  Data Link → Physical), then sends the frame to the server.
 *
 * Compile (Windows/MinGW):
 *   gcc client.c -o client.exe -lws2_32
 *
 * Frame layout (built RIGHT-TO-LEFT in buf, then sent):
 *   [PhysHdr][DLHdr][NetHdr][TransHdr][SessHdr][PresHdr][AppHdr][payload]
 */

#include <winsock2.h>
#include <windows.h>
#include <ws2tcpip.h>
#include "osi_layers.h"

#pragma comment(lib, "ws2_32.lib")

/*
 * We build the frame from RIGHT to LEFT in a large buffer.
 * 'tail' points one past the last byte written; 'head' decreases as we
 * prepend headers.  At the end, the frame lives at [head..tail-1].
 */
static char frame_buf[MAX_FRAME_LEN];
static int  frame_head;   /* index of first byte of frame */
static int  frame_tail;   /* index one past last byte of frame */

#define FRAME_LEN  (frame_tail - frame_head)

/* Prepend 'size' bytes of 'hdr' in front of the current frame */
static void prepend(const void *hdr, int size) {
    frame_head -= size;
    memcpy(frame_buf + frame_head, hdr, size);
}

/* ═══════════════════════════════════════════════════════════════════════════
   ENCAPSULATION  (Layers 7 → 1)
   ═══════════════════════════════════════════════════════════════════════════ */

/* Layer 7 – Application */
void layer7_send(const char *message) {
    print_layer_banner("CLIENT", LAYER_APPLICATION, "Application", "ENCAPSULATION - creating application data");

    int msg_len = (int)strlen(message);

    /* Write payload at the right end of the buffer */
    frame_tail = MAX_FRAME_LEN - 32;   /* leave small tail margin */
    frame_head = frame_tail - msg_len;
    memcpy(frame_buf + frame_head, message, msg_len);

    /* Prepend application header */
    AppHeader hdr;
    memset(&hdr, 0, sizeof(hdr));
    strncpy(hdr.protocol, "HTTP", sizeof(hdr.protocol)-1);
    hdr.data_len = (uint16_t)msg_len;
    prepend(&hdr, sizeof(hdr));

    printf("  Protocol       : %s\n", hdr.protocol);
    printf("  Data Length    : %d bytes\n", hdr.data_len);
    printf("  Payload        : \"%s\"\n", message);
    printf("  >> Application header added (%d bytes total)\n", FRAME_LEN);
}

/* Layer 6 – Presentation */
void layer6_send(void) {
    print_layer_banner("CLIENT", LAYER_PRESENTATION, "Presentation", "ENCAPSULATION - encoding/encrypting data");

    /* XOR-encrypt the entire current frame (AppHdr + payload) */
    xor_data(frame_buf + frame_head, FRAME_LEN, 0xAB);
    printf("  >> Data encrypted with XOR key 0xAB\n");

    /* Prepend presentation header (NOT encrypted) */
    PresHeader hdr;
    memset(&hdr, 0, sizeof(hdr));
    strncpy(hdr.encoding, "ASCII", sizeof(hdr.encoding)-1);
    hdr.encrypted = 1;
    prepend(&hdr, sizeof(hdr));

    printf("  Encoding       : %s\n", hdr.encoding);
    printf("  Encrypted      : Yes\n");
    printf("  >> Presentation header added (%d bytes total)\n", FRAME_LEN);
}

/* Layer 5 – Session */
void layer5_send(void) {
    print_layer_banner("CLIENT", LAYER_SESSION, "Session", "ENCAPSULATION - establishing session");

    SessHeader hdr;
    memset(&hdr, 0, sizeof(hdr));
    hdr.session_id     = 0xDEADBEEF;
    hdr.dialog_control = 1; /* Full-duplex */
    prepend(&hdr, sizeof(hdr));

    printf("  Session ID     : 0x%08X\n", hdr.session_id);
    printf("  Dialog Control : Full-Duplex\n");
    printf("  >> Session header added (%d bytes total)\n", FRAME_LEN);
}

/* Layer 4 – Transport */
void layer4_send(void) {
    print_layer_banner("CLIENT", LAYER_TRANSPORT, "Transport", "ENCAPSULATION - creating TCP segment");

    TransHeader hdr;
    memset(&hdr, 0, sizeof(hdr));
    hdr.src_port = 50000;
    hdr.dst_port = SERVER_PORT;
    hdr.seq_num  = 1000;
    hdr.protocol = 6; /* TCP */
    prepend(&hdr, sizeof(hdr));

    printf("  Source Port    : %d\n", hdr.src_port);
    printf("  Dest Port      : %d\n", hdr.dst_port);
    printf("  Sequence #     : %u\n", hdr.seq_num);
    printf("  Protocol       : TCP\n");
    printf("  >> Transport header added (%d bytes total)\n", FRAME_LEN);
}

/* Layer 3 – Network */
void layer3_send(void) {
    print_layer_banner("CLIENT", LAYER_NETWORK, "Network", "ENCAPSULATION - creating IP packet");

    NetHeader hdr;
    memset(&hdr, 0, sizeof(hdr));
    strncpy(hdr.src_ip, "192.168.1.10", sizeof(hdr.src_ip)-1);
    strncpy(hdr.dst_ip, SERVER_ADDR,    sizeof(hdr.dst_ip)-1);
    hdr.ttl      = 64;
    hdr.protocol = 6; /* TCP */
    prepend(&hdr, sizeof(hdr));

    printf("  Source IP      : %s\n", hdr.src_ip);
    printf("  Dest IP        : %s\n", hdr.dst_ip);
    printf("  TTL            : %d\n", hdr.ttl);
    printf("  Protocol       : TCP\n");
    printf("  >> Network header added (%d bytes total)\n", FRAME_LEN);
}

/* Layer 2 – Data Link */
void layer2_send(void) {
    print_layer_banner("CLIENT", LAYER_DATALINK, "Data Link", "ENCAPSULATION - creating Ethernet frame");

    /* FCS computed over the current frame (all inner headers + payload) */
    uint16_t fcs = simple_checksum(frame_buf + frame_head, FRAME_LEN);

    DLHeader hdr;
    memset(&hdr, 0, sizeof(hdr));
    strncpy(hdr.src_mac, "AA:BB:CC:DD:EE:FF", sizeof(hdr.src_mac)-1);
    strncpy(hdr.dst_mac, "11:22:33:44:55:66", sizeof(hdr.dst_mac)-1);
    hdr.ether_type = 0x0800; /* IPv4 */
    hdr.fcs        = fcs;
    prepend(&hdr, sizeof(hdr));

    printf("  Source MAC     : %s\n", hdr.src_mac);
    printf("  Dest MAC       : %s\n", hdr.dst_mac);
    printf("  EtherType      : 0x%04X (IPv4)\n", hdr.ether_type);
    printf("  FCS            : 0x%04X\n", hdr.fcs);
    printf("  >> Data Link header added (%d bytes total)\n", FRAME_LEN);
}

/* Layer 1 – Physical */
void layer1_send(void) {
    print_layer_banner("CLIENT", LAYER_PHYSICAL, "Physical", "ENCAPSULATION - converting to bits/signals");

    PhysHeader hdr;
    memset(&hdr, 0, sizeof(hdr));
    hdr.bit_count     = (uint32_t)(FRAME_LEN) * 8;
    hdr.encoding_type = 1; /* Manchester */
    prepend(&hdr, sizeof(hdr));

    printf("  Bit Count      : %u bits\n", hdr.bit_count);
    printf("  Encoding Type  : Manchester\n");
    printf("  >> Physical header added (%d bytes total)\n", FRAME_LEN);
    printf("  >> Frame ready to transmit over the wire!\n");
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN – build message, encapsulate, send to server
   ═══════════════════════════════════════════════════════════════════════════ */
int main(int argc, char *argv[]) {
    const char *message = (argc > 1) ? argv[1] : "Hello from OSI Simulation!";

    printf("╔═══════════════════════════════════════════════════════════╗\n");
    printf("║          OSI MODEL SIMULATION  –  CLIENT                  ║\n");
    printf("╚═══════════════════════════════════════════════════════════╝\n");
    printf("  Message to send: \"%s\"\n", message);
    printf("\n════════════════════════════════════════════════════════════\n");
    printf("  BEGIN 7-LAYER ENCAPSULATION (Layers 7 → 1)\n");
    printf("════════════════════════════════════════════════════════════\n");

    memset(frame_buf, 0, sizeof(frame_buf));

    layer7_send(message);
    layer6_send();
    printf("\n  [PROGRESS] Layers 7-6 complete (Application + Presentation)\n");

    layer5_send();
    layer4_send();
    printf("\n  [PROGRESS] Layers 5-4 complete (Session + Transport)\n");

    layer3_send();
    layer2_send();
    printf("\n  [PROGRESS] Layers 3-2 complete (Network + Data Link)\n");

    layer1_send();
    printf("\n  [PROGRESS] Layer 1 complete (Physical) – Frame ready!\n");

    printf("\n════════════════════════════════════════════════════════════\n");
    printf("  ENCAPSULATION COMPLETE – Total frame: %d bytes\n", FRAME_LEN);
    printf("════════════════════════════════════════════════════════════\n");

    /* ── Connect to server and send ── */
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) {
        fprintf(stderr, "WSAStartup failed\n"); return 1;
    }

    SOCKET sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == INVALID_SOCKET) {
        fprintf(stderr, "socket() failed\n"); WSACleanup(); return 1;
    }

    struct sockaddr_in srv_addr;
    memset(&srv_addr, 0, sizeof(srv_addr));
    srv_addr.sin_family      = AF_INET;
    srv_addr.sin_port        = htons(SERVER_PORT);
    srv_addr.sin_addr.s_addr = inet_addr(SERVER_ADDR);

    printf("\n  Connecting to server %s:%d ...\n", SERVER_ADDR, SERVER_PORT);
    if (connect(sock, (struct sockaddr *)&srv_addr, sizeof(srv_addr)) == SOCKET_ERROR) {
        fprintf(stderr, "connect() failed: %d\n", WSAGetLastError());
        closesocket(sock); WSACleanup(); return 1;
    }
    printf("  Connected!\n");

    /* Send 4-byte length prefix, then the frame */
    int flen = FRAME_LEN;
    uint32_t len_net = htonl((uint32_t)flen);
    send(sock, (char *)&len_net, 4, 0);
    send(sock, frame_buf + frame_head, flen, 0);
    printf("  Frame transmitted (%d bytes).\n", flen);

    /* Wait for ACK */
    char ack[64] = {0};
    recv(sock, ack, sizeof(ack)-1, 0);
    printf("  Server ACK: %s\n\n", ack);

    closesocket(sock);
    WSACleanup();
    return 0;
}
