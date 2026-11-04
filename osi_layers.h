/*
 * osi_layers.h
 * Common OSI layer definitions, header structures, and constants
 * shared between client and server.
 */

#ifndef OSI_LAYERS_H
#define OSI_LAYERS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* ─── Sizes ───────────────────────────────────────────────────────────────── */
#define MAX_DATA_LEN        512
#define MAX_FRAME_LEN       2048

/* ─── Port the server listens on ──────────────────────────────────────────── */
#define SERVER_PORT         9090
#define SERVER_ADDR         "127.0.0.1"

/* ─── Layer identifiers (for logging) ────────────────────────────────────── */
#define LAYER_APPLICATION   7
#define LAYER_PRESENTATION  6
#define LAYER_SESSION       5
#define LAYER_TRANSPORT     4
#define LAYER_NETWORK       3
#define LAYER_DATALINK      2
#define LAYER_PHYSICAL      1

/* ─── Header structures (each layer prepends its own header) ─────────────── */
/* NOTE: packed to avoid padding differences between sender and receiver.    */
#pragma pack(push, 1)

/* Layer 7 – Application */
typedef struct {
    char     protocol[16];      /* e.g. "HTTP", "FTP"  */
    uint16_t data_len;
} AppHeader;

/* Layer 6 – Presentation */
typedef struct {
    char    encoding[16];       /* e.g. "ASCII", "UTF-8" */
    uint8_t encrypted;          /* 0 = plain, 1 = XOR-scrambled */
} PresHeader;

/* Layer 5 – Session */
typedef struct {
    uint32_t session_id;
    uint8_t  dialog_control;   /* 0=half-duplex, 1=full-duplex */
} SessHeader;

/* Layer 4 – Transport */
typedef struct {
    uint16_t src_port;
    uint16_t dst_port;
    uint32_t seq_num;
    uint8_t  protocol;         /* 6=TCP, 17=UDP */
} TransHeader;

/* Layer 3 – Network */
typedef struct {
    char    src_ip[16];
    char    dst_ip[16];
    uint8_t ttl;
    uint8_t protocol;          /* 6=TCP */
} NetHeader;

/* Layer 2 – Data Link */
typedef struct {
    char     src_mac[18];
    char     dst_mac[18];
    uint16_t ether_type;
    uint16_t fcs;              /* simple checksum */
} DLHeader;

/* Layer 1 – Physical */
typedef struct {
    uint32_t bit_count;
    uint8_t  encoding_type;   /* 0=NRZ, 1=Manchester */
} PhysHeader;

#pragma pack(pop)

/* ─── Utility: simple XOR "encryption" for Presentation layer ─────────────── */
static inline void xor_data(char *buf, int len, uint8_t key) {
    for (int i = 0; i < len; i++) buf[i] ^= key;
}

/* ─── Utility: 16-bit checksum ────────────────────────────────────────────── */
static inline uint16_t simple_checksum(const char *buf, int len) {
    uint32_t sum = 0;
    for (int i = 0; i < len; i++) sum += (unsigned char)buf[i];
    return (uint16_t)(sum & 0xFFFF);
}

/* ─── Pretty print helper ─────────────────────────────────────────────────── */
static inline void print_layer_banner(const char *side, int layer, const char *name, const char *action) {
    printf("\n[%s] Layer %d (%s) - %s\n", side, layer, name, action);
    printf("%-60s\n", "------------------------------------------------------------");
}

#endif /* OSI_LAYERS_H */
