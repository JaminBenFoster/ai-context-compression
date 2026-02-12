# CoText — Context Compression API
## Product Requirements Document (PRD) v1.0

---

## Document Control

| Field | Value |
|-------|-------|
| **Document Title** | CoText Product Requirements Document |
| **Document ID** | CTX-PRD-001 |
| **Version** | 1.0 |
| **Status** | Approved |
| **Product Owner** | Trong |
| **Created Date** | February 12, 2026 |
| **Last Updated** | February 12, 2026 |

### Related Documents

| Document | ID | Version |
|----------|----|---------| 
| Project Charter | CTX-PC-001 | 1.0 |
| Technical Design Specification | CTX-TDS-001 | 1.0 |

---

## 1. Product Overview

### 1.1 What is CoText?

CoText is a REST API that compresses LLM context windows — reducing token count while preserving semantic meaning. Developers send text, CoText returns compressed text with a confidence score and token savings metrics.

### 1.2 Target Users

**Primary: AI Application Developers**
- Building chatbots, RAG pipelines, AI agents, or any LLM-powered application
- Spending $500-$50,000+/month on LLM API costs
- Technical sophistication: can integrate a REST API
- Discovery: RapidAPI marketplace, dev communities, Twitter/X, Reddit

**User Segments:**

| Segment | Use Case | Volume | Price Sensitivity | Compression Type |
|---------|----------|--------|------------------|-----------------|
| **Indie Developer** | Side project chatbot, personal AI assistant | 1K-5K/month | High (free tier) | Token |
| **Startup Engineer** | Production chatbot, customer support AI | 10K-50K/month | Medium ($9-29/month) | Token + Semantic |
| **Mid-Market Team** | RAG pipeline, multi-agent system | 50K-250K/month | Low ($29-99/month) | Semantic |
| **Enterprise** | Large-scale AI deployment | 250K+/month | Very Low (custom) | Both + custom profiles |

### 1.3 User Personas

#### Persona 1: Alex — Indie AI Developer
- **Background:** Full-stack developer building an AI writing assistant as a side project
- **Pain:** GPT-4 costs are eating into the $50/month budget. Conversation history fills context windows fast.
- **Goal:** Reduce token costs by 30%+ without degrading output quality
- **Technical level:** Can read API docs and integrate in an afternoon
- **Willingness to pay:** Free tier initially, $9/month if savings are real
- **Discovery:** Browsing RapidAPI for "LLM" or "token" related APIs

#### Persona 2: Sarah — Startup Backend Engineer
- **Background:** Backend engineer at a Series A startup building a customer support AI
- **Pain:** Processing 50K conversations/month. Context windows hit limits. Costs are $8K/month and growing.
- **Goal:** Compress conversation history before sending to LLM without losing critical customer details
- **Technical level:** Will evaluate API thoroughly, needs good documentation and error handling
- **Willingness to pay:** $29/month easily justified if it saves even 10% of LLM costs
- **Discovery:** Team lead found it on RapidAPI or dev Twitter

#### Persona 3: Marcus — AI Platform Architect
- **Background:** Senior engineer at a mid-market company running multi-agent AI systems
- **Pain:** Agents pass context to each other, compounding token usage. Monthly LLM spend is $40K+.
- **Goal:** Systematic context optimization across the entire AI pipeline
- **Technical level:** Wants SDKs, batch processing, and detailed analytics
- **Willingness to pay:** $99/month is trivial relative to savings. Will push for enterprise contract.
- **Discovery:** Referred by colleague, or found via technical blog post

---

## 2. API Specification

### 2.1 Base URL

```
https://cotext-api.p.rapidapi.com/v1
```

### 2.2 Authentication

All requests require RapidAPI authentication headers:

```
X-RapidAPI-Key: <api_key>
X-RapidAPI-Host: cotext-api.p.rapidapi.com
```

### 2.3 Endpoints

#### `POST /v1/compress`

**Description:** Compress input text using specified compression strategy.

**Request Body:**

```json
{
  "text": "string (required) — The text to compress. Max 100,000 characters.",
  "strategy": "string (optional) — 'token' | 'semantic' | 'auto'. Default: 'auto'",
  "target_ratio": "number (optional) — Target compression ratio 0.1-0.9. Default: 0.5 (50% reduction)",
  "preserve_keywords": "string[] (optional) — Words/phrases that must be preserved verbatim",
  "output_format": "string (optional) — 'text' | 'json'. Default: 'text'"
}
```

**Response (200 OK):**

```json
{
  "compressed_text": "string — The compressed output",
  "metadata": {
    "original_tokens": 4250,
    "compressed_tokens": 2100,
    "compression_ratio": 0.506,
    "confidence_score": 0.87,
    "strategy_used": "semantic",
    "processing_time_ms": 245,
    "billable": true
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `compressed_text` | string | The compressed output text |
| `metadata.original_tokens` | integer | Token count of input (using cl100k_base tokenizer) |
| `metadata.compressed_tokens` | integer | Token count of compressed output |
| `metadata.compression_ratio` | float | Ratio of tokens removed (0.0-1.0). 0.5 = 50% reduction. |
| `metadata.confidence_score` | float | Semantic fidelity score (0.0-1.0). Higher = more meaning preserved. |
| `metadata.strategy_used` | string | Which compression strategy was applied |
| `metadata.processing_time_ms` | integer | Server-side processing time |
| `metadata.billable` | boolean | Whether this request counts against quota. `false` if confidence < 0.5 |

**Confidence Score & Fair Billing:**
- `confidence_score >= 0.5` → `billable: true` — counts against monthly quota
- `confidence_score < 0.5` → `billable: false` — free, not counted
- Customer decides their own quality threshold for using the result

#### `GET /v1/health`

**Description:** Health check endpoint.

**Response (200 OK):**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "engines": {
    "token": "ready",
    "semantic": "ready"
  }
}
```

#### `GET /v1/usage`

**Description:** Return current billing period usage statistics.

**Response (200 OK):**

```json
{
  "period": {
    "start": "2026-02-01T00:00:00Z",
    "end": "2026-02-28T23:59:59Z"
  },
  "usage": {
    "total_requests": 8432,
    "billable_requests": 7890,
    "non_billable_requests": 542,
    "tokens_processed": 33750000,
    "tokens_saved": 16200000,
    "average_compression_ratio": 0.48,
    "average_confidence_score": 0.83
  },
  "plan": {
    "name": "Pro",
    "included_compressions": 50000,
    "used_compressions": 7890,
    "remaining_compressions": 42110,
    "overage_rate": 0.0008
  }
}
```

### 2.4 Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "string — Machine-readable error code",
    "message": "string — Human-readable description",
    "details": "object (optional) — Additional context",
    "request_id": "string — Unique ID for debugging"
  }
}
```

**Error Codes:**

| HTTP Status | Error Code | Description | Action |
|-------------|-----------|-------------|--------|
| 400 | `INVALID_INPUT` | Request body is malformed or missing required fields | Fix request body per API spec |
| 400 | `TEXT_TOO_LONG` | Input text exceeds 100,000 character limit | Split input into smaller chunks |
| 400 | `INVALID_STRATEGY` | Unknown compression strategy | Use 'token', 'semantic', or 'auto' |
| 400 | `INVALID_TARGET_RATIO` | target_ratio outside 0.1-0.9 range | Use value between 0.1 and 0.9 |
| 401 | `UNAUTHORIZED` | Missing or invalid API key | Check RapidAPI key configuration |
| 429 | `RATE_LIMITED` | Too many requests per minute | Wait and retry. Check tier rate limits. |
| 429 | `QUOTA_EXCEEDED` | Monthly compression limit reached | Upgrade plan or wait for next billing period |
| 500 | `COMPRESSION_FAILED` | Internal compression engine error | Retry with exponential backoff. If persistent, contact support. |
| 500 | `EMBEDDING_UNAVAILABLE` | Semantic engine temporarily unavailable | Retry, or use strategy='token' as fallback |
| 503 | `SERVICE_UNAVAILABLE` | API is undergoing maintenance | Retry after `Retry-After` header value |

**Retry Policy:**
- Include `Retry-After` header on 429 and 503 responses
- Recommend exponential backoff: 1s, 2s, 4s, 8s, max 30s
- Include `X-Request-ID` header on all responses for debugging

---

## 3. Feature Specifications

### 3.1 Token Compression Engine

**Story ID:** COMP-001

**As a** developer sending verbose text to an LLM,
**I want** to automatically remove filler words and redundant tokens,
**So that** I use fewer tokens without losing information.

**Acceptance Criteria:**
1. Removes filler words/phrases ("you know", "basically", "in order to", "it should be noted that", etc.)
2. Deduplicates repeated information within the text
3. Simplifies verbose constructions ("in the event that" → "if")
4. Preserves all proper nouns, numbers, dates, and technical terms
5. Preserves words listed in `preserve_keywords` array verbatim
6. Achieves 15-30% token reduction on average English text
7. Processing time < 100ms for inputs up to 10,000 tokens
8. Returns confidence score based on information density preservation

**Technical Notes:**
- Uses tiktoken (cl100k_base) for tokenization
- Rule-based engine with configurable reduction patterns
- No external API calls — runs entirely in-process
- Deterministic: same input always produces same output

**Test Corpus:**
- Customer support conversation transcripts (verbose, repetitive)
- Technical documentation (information-dense, less compressible)
- Chat history with system prompts (mixed density)
- Legal/medical text (domain-specific, high preservation needed)

---

### 3.2 Semantic Compression Engine

**Story ID:** COMP-002

**As a** developer building a RAG pipeline,
**I want** to remove semantically redundant passages from retrieved context,
**So that** I send only the most relevant information to the LLM.

**Acceptance Criteria:**
1. Identifies semantically similar/redundant sentences using embedding similarity
2. Removes lowest-information sentences while preserving meaning flow
3. Maintains logical coherence (no orphaned references or dangling pronouns)
4. Achieves 30-60% token reduction depending on redundancy level
5. Confidence score reflects embedding similarity between original and compressed text
6. Processing time < 500ms for inputs up to 10,000 tokens
7. Gracefully degrades for very short inputs (< 100 tokens): returns original with confidence 1.0 and billable: false

**Technical Notes:**
- Uses all-MiniLM-L6-v2 (384-dim embeddings, 22M params)
- Sentence-level segmentation using rule-based splitter (not NLTK — too heavy for serverless)
- Cosine similarity threshold for redundancy detection: configurable, default 0.85
- Final output re-scored against original for confidence score

---

### 3.3 Auto Strategy Selection

**Story ID:** COMP-003

**As a** developer who doesn't want to choose a compression strategy,
**I want** the API to automatically select the best strategy for my input,
**So that** I get optimal results without understanding compression internals.

**Acceptance Criteria:**
1. When `strategy: "auto"` (default), analyzes input characteristics
2. Selects token compression for: short inputs (< 500 tokens), conversation-style text, high filler word density
3. Selects semantic compression for: long inputs (> 2,000 tokens), document-style text, multiple paragraphs with potential redundancy
4. Uses combined approach for inputs between 500-2,000 tokens: token compression first, then semantic on result
5. `strategy_used` field in response indicates which was chosen
6. Auto selection adds < 50ms overhead

---

### 3.4 Confidence Scoring System

**Story ID:** SCORE-001

**As a** developer consuming compressed text,
**I want** a reliable confidence score with every compression,
**So that** I can decide whether to use the compressed version or fall back to original.

**Acceptance Criteria:**
1. Score range: 0.0 (no confidence) to 1.0 (perfect preservation)
2. Score is computed as cosine similarity between embeddings of original and compressed text
3. For token compression: also factors in information density ratio (unique tokens / total tokens)
4. Score < 0.5 triggers `billable: false` — not counted against quota
5. Score is deterministic for same input + strategy combination
6. Score computation adds < 100ms to total processing time

**Scoring Thresholds (guidance for documentation):**

| Score Range | Quality | Recommended Action |
|-------------|---------|-------------------|
| 0.9 - 1.0 | Excellent | Safe to use for any purpose |
| 0.7 - 0.89 | Good | Safe for most use cases |
| 0.5 - 0.69 | Acceptable | Review for critical applications |
| < 0.5 | Low | Not billed. Likely too much information lost. |

---

### 3.5 Usage Tracking & Analytics

**Story ID:** USAGE-001

**As a** developer,
**I want** to see my API usage, token savings, and billing status,
**So that** I can track ROI and manage my quota.

**Acceptance Criteria:**
1. `GET /v1/usage` returns current period statistics
2. Tracks: total requests, billable requests, tokens processed, tokens saved, average ratios
3. Shows plan details: name, included compressions, used, remaining, overage rate
4. Data refreshes in near-real-time (< 60 second delay)
5. Historical data retained for 90 days

**Technical Notes:**
- Metrics stored in Supabase
- Aggregate queries, not per-request lookups (performance)
- RapidAPI also provides its own analytics dashboard — this supplements, not replaces

---

### 3.6 Preserve Keywords

**Story ID:** COMP-004

**As a** developer compressing text that contains critical terms,
**I want** to specify keywords that must never be removed or altered,
**So that** domain-specific terms, names, and codes survive compression.

**Acceptance Criteria:**
1. `preserve_keywords` array accepts up to 50 strings
2. Each keyword is matched case-insensitively in the input
3. Matched keywords and the surrounding context (±1 sentence) are protected from removal
4. Works with both token and semantic compression
5. If a keyword is not found in input, it is silently ignored (no error)

---

## 4. Non-Functional Requirements

### 4.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| **API Latency (p50)** | < 200ms | For 4K token input, token compression |
| **API Latency (p95)** | < 500ms | For 4K token input, semantic compression |
| **API Latency (p99)** | < 1,000ms | For 10K token input, any strategy |
| **Throughput** | 100 concurrent requests | Without degradation |
| **Cold Start** | < 2,000ms | Vercel serverless function initialization |
| **Embedding Model Load** | < 500ms | Model cached in memory after first load |

### 4.2 Reliability

| Metric | Target |
|--------|--------|
| **Uptime** | 99% (no contractual SLA for v1.0) |
| **Error Rate** | < 1% of requests return 5xx |
| **Data Loss** | Zero tolerance for usage metrics |
| **Recovery Time** | < 15 minutes for any single-component failure |

### 4.3 Security

| Requirement | Implementation |
|------------|----------------|
| **Authentication** | RapidAPI-managed API keys |
| **Transport** | HTTPS only (TLS 1.2+) |
| **Data at Rest** | Supabase encryption (AES-256) |
| **No PII Storage** | Never store customer text content |
| **Metadata Only** | Store only: token counts, ratios, timestamps, API key hash |
| **Audit Logging** | Log all API requests with: timestamp, API key hash, strategy, token counts, latency, status code |
| **Rate Limiting** | Per-tier limits enforced at RapidAPI gateway level |

### 4.4 Scalability

| Dimension | v1.0 Capacity | Scale Trigger | Scale Action |
|-----------|--------------|---------------|--------------|
| **Requests/month** | 100K | 80K reached | Evaluate Vercel Pro ($20/month) |
| **Database rows** | 500K | 400K reached | Evaluate Supabase Pro ($25/month) |
| **Concurrent users** | 100 | Sustained > 80 | Add edge caching for health/usage endpoints |

### 4.5 Streaming Readiness (Design Now, Build Later)

The API architecture must support future streaming without breaking changes:

1. Response format is JSON — streaming will use Server-Sent Events (SSE) on a separate endpoint (`POST /v1/compress/stream`)
2. Compression engines must be designed as pipeline stages (tokenize → compress → score) that can emit partial results
3. Database schema includes a `streaming` boolean column (default false) for future feature flagging
4. API versioning (`/v1/`) allows `/v2/` to introduce streaming natively

---

## 5. Edge Cases & Handling

| Scenario | Expected Behavior |
|----------|------------------|
| **Empty input text** | Return 400 `INVALID_INPUT` with message "text field cannot be empty" |
| **Input is a single word** | Return original text, confidence: 1.0, compression_ratio: 0.0, billable: false |
| **Input is already maximally compressed** | Return original text, confidence: 1.0, compression_ratio: 0.0, billable: false |
| **Input is all preserve_keywords** | Return original text, confidence: 1.0, compression_ratio: 0.0, billable: false |
| **Input contains only code/JSON** | Token compression skips code blocks. Semantic compression treats as opaque. Low compression ratio expected. |
| **Input is in non-English language** | v1.0: Process anyway. Token compression may have limited effect. Semantic compression works on any language embeddings support. Document as limitation. |
| **Input exceeds 100K chars** | Return 400 `TEXT_TOO_LONG` |
| **target_ratio is 0.9 (aggressive)** | Compress aggressively. Confidence score will likely be low. Customer's choice. |
| **target_ratio is 0.1 (minimal)** | Light compression. High confidence. Customer pays for a valid compression. |
| **Embedding model fails to load** | Semantic engine returns 500 `EMBEDDING_UNAVAILABLE`. Token engine continues working. API health check shows semantic: "degraded". |
| **RapidAPI sends request without valid tier** | Return 401 `UNAUTHORIZED` |
| **Concurrent identical requests** | Each processed independently (stateless). Same input = same output (deterministic). |

---

## 6. API Documentation Requirements

The following documentation must be published on RapidAPI and/or a docs site:

### 6.1 Required Docs

| Document | Content | Format |
|----------|---------|--------|
| **Quick Start** | 5-minute integration guide with curl examples | Markdown |
| **API Reference** | Full endpoint documentation with request/response examples | OpenAPI 3.0 spec |
| **Compression Strategies** | Explanation of token vs semantic vs auto with use case guidance | Markdown |
| **Confidence Score Guide** | What scores mean, recommended thresholds by use case | Markdown |
| **Error Handling** | Complete error code reference with retry guidance | Markdown |
| **Fair Billing Policy** | How non-billable requests work | Markdown |
| **Changelog** | Version history with breaking/non-breaking change labels | Markdown |

### 6.2 Code Examples (for RapidAPI listing)

Provide working code examples in:
- **curl** (universal)
- **Python** (requests library)
- **Node.js** (fetch / axios)
- **Go** (net/http)

---

## 7. Testing Requirements

### 7.1 Test Coverage Targets

| Category | Coverage Target | Tool |
|----------|----------------|------|
| **Unit Tests** | 80%+ code coverage | Jest/Vitest |
| **Integration Tests** | All endpoints, all error codes | Supertest |
| **Performance Tests** | p50, p95, p99 latency benchmarks | Custom benchmarking script |
| **Compression Quality** | Test corpus with known expected outcomes | Custom test suite |

### 7.2 Test Corpus

A standardized test corpus must be created with:

| Corpus Type | Source | Expected Behavior |
|-------------|--------|------------------|
| **Verbose conversation** | Synthetic customer support chat (10K tokens) | 30-50% compression, confidence > 0.7 |
| **Technical documentation** | Real API docs (5K tokens) | 10-20% compression, confidence > 0.85 |
| **RAG retrieval** | 5 overlapping passages on same topic (8K tokens) | 40-60% compression, confidence > 0.75 |
| **Minimal text** | Single sentence (50 tokens) | 0-5% compression, confidence ~1.0 |
| **Code-heavy** | Mixed prose and code blocks (4K tokens) | 5-15% compression (code preserved) |
| **All keywords** | Text where every sentence contains a preserve_keyword | ~0% compression, confidence 1.0 |

### 7.3 Quality Regression Tests

Before each release:
1. Run full test corpus through both compression engines
2. Compare compression ratios against baseline (must not degrade > 5%)
3. Compare confidence scores against baseline
4. Verify all error codes return correct format
5. Load test: 100 concurrent requests, verify p95 < 500ms

---

## 8. Launch Checklist

| # | Item | Owner | Status |
|---|------|-------|--------|
| 1 | Token compression engine passing all unit tests | Dev | ☐ |
| 2 | Semantic compression engine passing all unit tests | Dev | ☐ |
| 3 | Confidence scoring calibrated against test corpus | Dev | ☐ |
| 4 | All error codes implemented and tested | Dev | ☐ |
| 5 | Usage tracking writing to Supabase correctly | Dev | ☐ |
| 6 | Fair billing (non-billable for confidence < 0.5) verified | Dev | ☐ |
| 7 | RapidAPI listing configured with all tiers | Trong | ☐ |
| 8 | API documentation published | Dev | ☐ |
| 9 | Code examples (curl, Python, Node, Go) tested | Dev | ☐ |
| 10 | Load test passed (100 concurrent, p95 < 500ms) | Dev | ☐ |
| 11 | Health check endpoint returning correct status | Dev | ☐ |
| 12 | Monitoring/alerting configured (Vercel) | Dev | ☐ |
| 13 | 5 beta users identified and invited | Trong | ☐ |
| 14 | Changelog initialized | Dev | ☐ |

---

## 9. Post-Launch Monitoring

### 9.1 Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| **High Error Rate** | 5xx rate > 5% for 5 minutes | Investigate immediately |
| **High Latency** | p95 > 1000ms for 10 minutes | Check embedding model, Vercel cold starts |
| **Low Confidence** | Average confidence < 0.6 for 1 hour | Review compression quality, check for input pattern changes |
| **Quota Approaching** | Any customer at 90% of tier limit | No action (informational) |

### 9.2 Weekly Metrics Review

| Metric | What to Look For |
|--------|-----------------|
| New signups | Growth trend, conversion from free → paid |
| API calls | Usage patterns, peak times |
| Average compression ratio | Quality trend |
| Average confidence score | Quality trend |
| Error rates by code | Systemic issues |
| P95 latency | Performance trend |
| Revenue | MRR trajectory toward $200 (day 60), $500 (day 90) |

---

*This PRD is a living document. Changes require Product Owner approval.*
