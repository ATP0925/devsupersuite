# DEVSUPERSUITE INTERACTIVE DEVELOPER API PORTAL & REST/gRPC REFERENCE
**Production OpenAPI 3.1 & gRPC Protobuf Specifications for OmniKernel 5.2-LTS Microservices**

*Document ID: DSS-API-PORTAL-2026-V1*  
*Classification: Developer Infrastructure & Systems Architecture*  
*Maintained By: DevSuperSuite Brand & Communications Directorate (`press@devsupersuite.com`)*  
*Engineering Oversight: OmniKernel Core Systems Engineering (`api@devsupersuite.com`)*  
*Service Host: `http://127.0.0.1:8443` (Local Loopback) | Production Socket: `/var/run/omnikernel/daemon.sock`*

---

## TABLE OF CONTENTS

1. [Architecture & Transport Protocols](#1-architecture--transport-protocols)
2. [Microservice 1: AgentShield AST Context Slicer Service](#2-microservice-1-agentshield-ast-context-slicer-service)
3. [Microservice 2: Shannon Entropy Engine & Secret Interceptor](#3-microservice-2-shannon-entropy-engine--secret-interceptor)
4. [Microservice 3: Raft Consensus & High-Availability Failover Service](#4-microservice-3-raft-consensus--high-availability-failover-service)
5. [Microservice 4: Local Vault & Cryptographic Key Provider Service](#5-microservice-4-local-vault--cryptographic-key-provider-service)
6. [gRPC Protobuf Service Definitions (`omnikernel_v1.proto`)](#6-grpc-protobuf-service-definitions)
7. [Error Codes, Rate Limiting & Health Checks](#7-error-codes-rate-limiting--health-checks)

---

## 1. ARCHITECTURE & TRANSPORT PROTOCOLS

OmniKernel 5.2-LTS microservices execute in-process on host workstation silicon. To support high-throughput developer tooling and continuous integration pipelines, OmniKernel exposes two native transport layers:
1. **High-Performance gRPC over HTTP/2 & UNIX Domain Sockets**: Designed for low-latency IPC ($<0.4\text{ms}$) between editor plugins (Neovim, JetBrains, VS Code, Zed) and the local compiler daemon.
2. **RESTful HTTP/JSON over Local Loopback (`127.0.0.1:8443`)**: OpenAPI 3.1 compliant endpoint suite for scriptable CI/CD runners, terminal extensions, and headless automation.

### Protocol Comparison Matrix:

| Operational Metric | gRPC / HTTP/2 (UNIX Socket) | REST / JSON (Loopback TCP) |
| :--- | :--- | :--- |
| **Serialization Overhead** | Binary Protocol Buffers ($< 0.1\text{ms}$) | JSON Parsing ($< 0.6\text{ms}$) |
| **Transport Layer** | `/var/run/omnikernel/daemon.sock` | `http://127.0.0.1:8443` |
| **Primary Consumer** | Neovim Lua, JetBrains Java Plugin, Zed Rust | cURL, Shell Scripts, Python Automation, GitHub Actions |
| **Zero-Egress Isolation** | Hard Air-Gap (Filesystem socket only) | Loopback-bound (`127.0.0.1` strictly) |

---

## 2. MICROSERVICE 1: AGENTSHIELD AST CONTEXT SLICER SERVICE

The **AST Context Slicer Service** parses incoming source files using AVX-512 vector-accelerated Tree-sitter parsers, separating public interface boundaries (Control Plane) from redundant internal function bodies (Execution Plane) to achieve an audited 83.5% token reduction.

### 2.1 Endpoint Specification: `POST /v1/slicer/slice`
- **Method**: `POST`
- **Path**: `/v1/slicer/slice`
- **Content-Type**: `application/json`
- **Authentication**: `Bearer <ED25519_SESSION_TOKEN>` (or local loopback authentication bypass in air-gap mode)

#### Request Schema:
```json
{
  "filePath": "services/payment_router.go",
  "language": "go",
  "content": "package orders\n\ntype PaymentRouter struct { ... }",
  "options": {
    "stripFunctionBodies": true,
    "preserveDocstrings": true,
    "preserveTypeAnnotations": true,
    "maxDepth": 12,
    "collapseProtobuf": true
  }
}
```

#### Response Schema (HTTP 200 OK):
```json
{
  "status": "SUCCESS",
  "filePath": "services/payment_router.go",
  "originalTokens": 1480,
  "slicedTokens": 234,
  "tokenReductionPct": 84.19,
  "parseLatencyMs": 1.14,
  "slicedContent": "package orders\n\ntype PaymentRouter struct {}\nfunc (r *PaymentRouter) RoutePayment(id string) error { ... }",
  "symbolManifest": [
    { "name": "PaymentRouter", "kind": "struct", "exported": true },
    { "name": "RoutePayment", "kind": "method", "exported": true }
  ]
}
```

### 2.2 Polyglot Client Implementation Samples

#### cURL
```bash
curl -X POST http://127.0.0.1:8443/v1/slicer/slice \
  -H "Content-Type: application/json" \
  -d '{
    "filePath": "services/transaction.py",
    "language": "python",
    "content": "class Transaction:\n    def process(self):\n        pass",
    "options": { "stripFunctionBodies": true }
  }'
```

#### Python (Async httpx)
```python
import httpx
import asyncio

async def slice_source_file(file_path: str, code_content: str) -> dict:
    url = "http://127.0.0.1:8443/v1/slicer/slice"
    payload = {
        "filePath": file_path,
        "language": "python",
        "content": code_content,
        "options": {
            "stripFunctionBodies": True,
            "preserveDocstrings": True,
            "preserveTypeAnnotations": True
        }
    }
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"Tokens reduced by {data['tokenReductionPct']}% in {data['parseLatencyMs']}ms")
        return data

# Execution Example
# asyncio.run(slice_source_file("models/order.py", "..."))
```

#### TypeScript / Node.js
```typescript
import axios from 'axios';

interface SliceResponse {
  status: string;
  originalTokens: number;
  slicedTokens: number;
  tokenReductionPct: number;
  parseLatencyMs: number;
  slicedContent: string;
}

export async function sliceBuffer(filePath: string, content: string): Promise<SliceResponse> {
  const endpoint = 'http://127.0.0.1:8443/v1/slicer/slice';
  const response = await axios.post<SliceResponse>(endpoint, {
    filePath,
    language: 'typescript',
    content,
    options: {
      stripFunctionBodies: true,
      preserveTypeAnnotations: true
    }
  });
  return response.data;
}
```

#### Go (Native Net/HTTP)
```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type SliceRequest struct {
	FilePath string                 `json:"filePath"`
	Language string                 `json:"language"`
	Content  string                 `json:"content"`
	Options  map[string]interface{} `json:"options"`
}

type SliceResponse struct {
	Status            string  `json:"status"`
	OriginalTokens    int     `json:"originalTokens"`
	SlicedTokens      int     `json:"slicedTokens"`
	TokenReductionPct float64 `json:"tokenReductionPct"`
	ParseLatencyMs    float64 `json:"parseLatencyMs"`
	SlicedContent     string  `json:"slicedContent"`
}

func SliceSource(filePath, code string) (*SliceResponse, error) {
	reqBody := SliceRequest{
		FilePath: filePath,
		Language: "go",
		Content:  code,
		Options: map[string]interface{}{
			"stripFunctionBodies": true,
			"collapseProtobuf":    true,
		},
	}
	buf, _ := json.Marshal(reqBody)
	client := &http.Client{Timeout: 2 * time.Second}
	resp, err := client.Post("http://127.0.0.1:8443/v1/slicer/slice", "application/json", bytes.NewBuffer(buf))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result SliceResponse
	json.NewDecoder(resp.Body).Decode(&result)
	return &result, nil
}
```

---

## 3. MICROSERVICE 2: SHANNON ENTROPY ENGINE & SECRET INTERCEPTOR

The **Shannon Entropy Engine** inspects source diff buffers directly within CPU SIMD registers ($<0.8\text{ms}$) to intercept high-entropy credentials ($H \ge 4.50\text{ bits/char}$) and enforce `INVARIANT_TEST_PRESERVATION`.

### 3.1 Endpoint Specification: `POST /v1/entropy/scan`
- **Method**: `POST`
- **Path**: `/v1/entropy/scan`
- **Content-Type**: `application/json`

#### Request Schema:
```json
{
  "targetBuffer": "STRIPE_SECRET_KEY = \"sk_test_SIMULATED_HIGH_ENTROPY_KEY_TEST_MOCK_99\"",
  "threshold": 4.50,
  "slidingWindowSize": 32,
  "enforceTestPreservation": true,
  "gitDiffContext": "diff --git a/tests/test_auth.py b/tests/test_auth.py\n- def test_token_expiration():"
}
```

#### Response Schema (Security Breach - HTTP 422 Unprocessable Entity):
```json
{
  "status": "INVARIANT_BREACH",
  "exitCode": 1,
  "verdict": "REJECTED",
  "secretDetected": true,
  "metrics": {
    "calculatedEntropy": 4.88,
    "threshold": 4.50,
    "violatingString": "sk_test_SIMULATED_HIGH_ENTROPY_KEY_TEST_MOCK_99",
    "classification": "PRODUCTION_API_KEY",
    "scanLatencyUs": 740
  },
  "testPreservationBreached": true,
  "remediation": "Remove secret credential and restore deleted unit test assertions in tests/test_auth.py."
}
```

### 3.2 Polyglot Client Implementation Samples

#### cURL
```bash
curl -X POST http://127.0.0.1:8443/v1/entropy/scan \
  -H "Content-Type: application/json" \
  -d '{
    "targetBuffer": "const key = \"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\";",
    "threshold": 4.50
  }'
```

#### Python
```python
import requests

def scan_buffer_entropy(diff_text: str) -> dict:
    url = "http://127.0.0.1:8443/v1/entropy/scan"
    payload = {
        "targetBuffer": diff_text,
        "threshold": 4.50,
        "enforceTestPreservation": True
    }
    resp = requests.post(url, json=payload)
    if resp.status_code == 422:
        breach = resp.json()
        print(f"[SECURITY ALERT] Secret detected with H = {breach['metrics']['calculatedEntropy']}")
        return breach
    return resp.json()
```

#### TypeScript
```typescript
import axios from 'axios';

export async function verifyEntropyGate(codeDiff: string): Promise<boolean> {
  try {
    await axios.post('http://127.0.0.1:8443/v1/entropy/scan', {
      targetBuffer: codeDiff,
      threshold: 4.50,
      enforceTestPreservation: true
    });
    return true; // Clean buffer
  } catch (err: any) {
    if (err.response && err.response.status === 422) {
      console.error('AgentShield Invariant Blocked Diff:', err.response.data);
      return false; // Block commit
    }
    throw err;
  }
}
```

#### Go
```go
package main

import (
	"bytes"
	"encoding/json"
	"net/http"
)

func ScanEntropy(diff string) (bool, error) {
	payload, _ := json.Marshal(map[string]interface{}{
		"targetBuffer": diff,
		"threshold":    4.50,
	})
	resp, err := http.Post("http://127.0.0.1:8443/v1/entropy/scan", "application/json", bytes.NewBuffer(payload))
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()
	return resp.StatusCode == http.StatusOK, nil
}
```

---

## 4. MICROSERVICE 3: RAFT CONSENSUS & HIGH-AVAILABILITY FAILOVER SERVICE

The **Raft Consensus Microservice** manages local-cluster leader election, configuration state replication, and sub-second failover across active-standby daemon nodes in enterprise developer fleets.

### 4.1 Endpoint Specification: `GET /v1/raft/status`
- **Method**: `GET`
- **Path**: `/v1/raft/status`

#### Response Schema (HTTP 200 OK):
```json
{
  "clusterId": "dss-raft-cluster-west-1",
  "nodeId": "node-101",
  "state": "LEADER",
  "currentTerm": 42,
  "commitIndex": 18452,
  "peers": [
    { "id": "node-102", "address": "127.0.0.1:8444", "status": "ACTIVE", "matchIndex": 18452 },
    { "id": "node-103", "address": "127.0.0.1:8445", "status": "ACTIVE", "matchIndex": 18451 }
  ],
  "heartbeatIntervalMs": 50,
  "electionTimeoutMs": 150
}
```

---

## 5. MICROSERVICE 4: LOCAL VAULT & CRYPTOGRAPHIC KEY PROVIDER SERVICE

The **Vault Secret Provider** interfaces with host hardware security modules (TPM 2.0, Apple Keychain, Windows DPAPI) to unseal offline Ed25519 license keys without cloud phone-home telemetry.

### 5.1 Endpoint Specification: `POST /v1/vault/attest`
- **Method**: `POST`
- **Path**: `/v1/vault/attest`

#### Request Schema:
```json
{
  "tpmRegisters": [0, 2, 4, 7],
  "nonce": "4f8fce229e054a3a98888a83b9301a91"
}
```

#### Response Schema (HTTP 200 OK):
```json
{
  "hardwareRooted": true,
  "fipsStatus": "FIPS_140_3_LEVEL_3_COMPLIANT",
  "tpmPcrDigest": "7a8f9c1e3d5b2a0f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5",
  "licenseTier": "PRO_LIFETIME",
  "offlineVerified": true
}
```

---

## 6. gRPC PROTOBUF SERVICE DEFINITIONS (`omnikernel_v1.proto`)

For high-throughput systems integration, OmniKernel exposes native gRPC Protocol Buffer services:

```protobuf
syntax = "proto3";

package omnikernel.v1;

option go_package = "github.com/devsupersuite/omnikernel/v1;omnikernelv1";

// ====================================================================
// Slicer Service Definition
// ====================================================================
service SlicerService {
  rpc SliceFile (SliceRequest) returns (SliceResponse);
  rpc StreamSliceBatch (stream SliceRequest) returns (stream SliceResponse);
}

message SlicingOptions {
  bool strip_function_bodies = 1;
  bool preserve_docstrings = 2;
  bool preserve_type_annotations = 3;
  int32 max_depth = 4;
  bool collapse_protobuf = 5;
}

message SliceRequest {
  string file_path = 1;
  string language = 2;
  bytes content = 3;
  SlicingOptions options = 4;
}

message SymbolStub {
  string name = 1;
  string kind = 2;
  bool exported = 3;
}

message SliceResponse {
  string status = 1;
  int32 original_tokens = 2;
  int32 sliced_tokens = 3;
  float token_reduction_pct = 4;
  float parse_latency_ms = 5;
  bytes sliced_content = 6;
  repeated SymbolStub symbols = 7;
}

// ====================================================================
// AgentShield Entropy Service Definition
// ====================================================================
service AgentShieldService {
  rpc ScanEntropy (EntropyScanRequest) returns (EntropyScanResponse);
}

message EntropyScanRequest {
  bytes target_buffer = 1;
  float threshold = 2;
  int32 sliding_window_size = 3;
  bool enforce_test_preservation = 4;
  string git_diff_context = 5;
}

message EntropyScanResponse {
  enum Verdict {
    ALLOW = 0;
    BLOCK_SECRET = 1;
    BLOCK_TEST_DELETION = 2;
  }
  Verdict verdict = 1;
  float calculated_entropy = 2;
  string violating_token = 3;
  int64 scan_latency_nanos = 4;
  string error_message = 5;
}
```

---

## 7. ERROR CODES, RATE LIMITING & HEALTH CHECKS

OmniKernel adheres to strict POSIX and HTTP error semantics:

| HTTP Status | POSIX Code | Error Constant | Remediation Guidance |
| :--- | :---: | :--- | :--- |
| `200 OK` | `0` | `STATUS_SUCCESS` | Operation completed without invariant violations. |
| `422 Unprocessable`| `1` | `ERR_HIGH_ENTROPY_SECRET` | High-entropy token detected ($H \ge 4.50$). Remove secret from buffer. |
| `422 Unprocessable`| `2` | `ERR_INVARIANT_TEST_PRESERVATION` | Rogue test suite deletion blocked. Restore test assertions. |
| `400 Bad Request` | `13` | `ERR_TREE_SITTER_SYNTAX_ERROR` | Syntax error in source buffer preventing CST generation. |
| `503 Unavailable` | `126`| `ERR_RAFT_LEADER_REELECTION` | Raft cluster currently undergoing sub-second failover. |

---

## COMMERCIAL ACCESS & STOREFRONT

- **Direct Pro Lifetime Storefront ($29 USD / ₹1,499 INR)**: [gumroad.com/l/tlzdco](https://gumroad.com/l/tlzdco)
- **Live Interactive Sandbox**: [devsupersuite.web.app](https://devsupersuite.web.app)
- **API Support & Enterprise Keys**: `api@devsupersuite.com` | `press@devsupersuite.com`

---
*© DevSuperSuite Official & OmniKernel Labs. All rights reserved. Strict Brand Anonymity Protocol Enforced.*
