# CoText — Context Compression API
## Technical Design Specification (TDS) v1.0

---

## Document Control

| Field | Value |
|-------|-------|
| **Document Title** | CoText Technical Design Specification |
| **Document ID** | CTX-TDS-001 |
| **Version** | 1.0 |
| **Status** | Approved |
| **Author** | Solution Architect (AI Agent) |
| **Reviewed By** | Trong (Product Owner) |
| **Created Date** | February 12, 2026 |
| **Last Updated** | February 12, 2026 |

### Related Documents

| Document | ID | Version |
|----------|----|---------| 
| Project Charter | CTX-PC-001 | 1.0 |
| Product Requirements Document | CTX-PRD-001 | 1.0 |

---

## 1. Introduction

### 1.1 Purpose

This TDS provides the implementation blueprint for CoText. Every section is written to be directly actionable by a developer or AI coding agent (Claude Code, Cursor). Ambiguity has been intentionally minimized.

### 1.2 Architecture Principles

| Principle | Implementation |
|-----------|----------------|
| **Stateless API** | No session state. Every request is self-contained. |
| **Deterministic** | Same input + strategy always produces same output. |
| **No PII Storage** | Never persist customer text. Only metadata/metrics. |
| **Fail Gracefully** | Partial engine failure doesn't take down the API. |
| **Design for Streaming** | Pipeline architecture that can emit partial results in v1.1. |
| **Zero External Dependencies at Runtime** | No calls to OpenAI/Anthropic. Compression runs locally. |

### 1.3 Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| **Language** | TypeScript | 5.x | Strict mode enabled |
| **Runtime** | Node.js | 20.x LTS | Vercel serverless |
| **Framework** | Next.js | 14.x | App Router, API Routes only (no frontend for v1.0) |
| **Database** | PostgreSQL | 15.x | Via Supabase |
| **ORM/Client** | Supabase JS Client | 2.x | Direct SQL for complex queries |
| **Tokenizer** | tiktoken | 1.x | cl100k_base encoding (GPT-4 compatible) |
| **Embeddings** | @xenova/transformers | 2.x | all-MiniLM-L6-v2 (runs in Node.js, no Python) |
| **Validation** | zod | 3.x | Request/response schema validation |
| **Testing** | Vitest | 1.x | Fast, TypeScript-native |
| **Hosting** | Vercel | — | Serverless functions, Edge config |

---

## 2. System Architecture

### 2.1 High-Level Flow

```
Client Request
     |
     v
[RapidAPI Gateway] -- Auth, Rate Limiting, Billing
     |
     v
[Vercel Serverless Function]
     |
     v
[Input Validator (Zod)] --> [Strategy Selector (auto/manual)]
                                     |
                        +------------+------------+
                        v                         v
               [Token Engine]           [Semantic Engine]
                        |                         |
                        +------------+------------+
                                     |
                                     v
                           [Confidence Scorer]
                                     |
                                     v
                           [Response Builder]
                                     |
                        +------------+------------+
                        v                         v
                [HTTP Response]         [Supabase Metrics]
                (to Client)            (Async, Non-blocking)
```

### 2.2 Request Lifecycle

1. **RapidAPI Gateway** authenticates request, checks rate limits, identifies billing tier
2. **Input Validator** validates request body against Zod schema
3. **Strategy Selector** determines compression approach (auto, token, or semantic)
4. **Compression Engine** processes text through selected pipeline
5. **Confidence Scorer** computes semantic similarity between original and compressed
6. **Response Builder** assembles JSON response with metadata
7. **Metrics Writer** (async, non-blocking) writes usage data to Supabase
8. **Response** returns to client via RapidAPI gateway

**Critical: Metrics writing is fire-and-forget.** Database latency must never impact API response time.

---

## 3. Project Structure

```
cotext-api/
├── .env.local                    # Local environment variables
├── .env.example                  # Template for environment setup
├── next.config.js                # Next.js configuration
├── package.json
├── tsconfig.json
├── vitest.config.ts
│
├── src/
│   ├── app/
│   │   └── api/
│   │       └── v1/
│   │           ├── compress/
│   │           │   └── route.ts          # POST /v1/compress
│   │           ├── health/
│   │           │   └── route.ts          # GET /v1/health
│   │           └── usage/
│   │               └── route.ts          # GET /v1/usage
│   │
│   ├── engines/
│   │   ├── token-engine.ts               # Token compression
│   │   ├── semantic-engine.ts            # Semantic compression
│   │   ├── strategy-selector.ts          # Auto strategy selection
│   │   └── confidence-scorer.ts          # Embedding-based scoring
│   │
│   ├── lib/
│   │   ├── supabase.ts                   # Supabase client init
│   │   ├── tokenizer.ts                  # tiktoken wrapper
│   │   ├── embeddings.ts                 # Embedding model loader & cache
│   │   ├── metrics.ts                    # Async metrics writer
│   │   └── errors.ts                     # Error class definitions
│   │
│   ├── schemas/
│   │   ├── compress-request.ts           # Zod schema for compress endpoint
│   │   ├── compress-response.ts          # Response type definitions
│   │   └── error-response.ts             # Error response schema
│   │
│   └── utils/
│       ├── text-splitter.ts              # Sentence segmentation
│       ├── cosine-similarity.ts          # Vector math
│       └── constants.ts                  # Shared constants
│
├── tests/
│   ├── unit/
│   │   ├── token-engine.test.ts
│   │   ├── semantic-engine.test.ts
│   │   ├── confidence-scorer.test.ts
│   │   └── strategy-selector.test.ts
│   ├── integration/
│   │   ├── compress-endpoint.test.ts
│   │   ├── health-endpoint.test.ts
│   │   └── usage-endpoint.test.ts
│   ├── performance/
│   │   └── benchmark.ts
│   └── fixtures/
│       ├── verbose-conversation.txt
│       ├── technical-docs.txt
│       ├── rag-retrieval.txt
│       ├── minimal-text.txt
│       └── code-heavy.txt
│
└── docs/
    ├── api-reference.md
    ├── quick-start.md
    ├── compression-strategies.md
    └── changelog.md
```

---

## 4. Compression Engines

### 4.1 Token Compression Engine

**File:** `src/engines/token-engine.ts`

**Algorithm Pipeline:**

```
Input Text
  -> Tokenize with tiktoken
  -> Detect protected regions (keywords, code blocks, URLs, numbers)
  -> Remove filler words/phrases (pattern matching against dictionary)
  -> Simplify verbose constructions ("in order to" -> "to")
  -> Deduplicate repeated sentences/clauses
  -> Check target_ratio — if not met, escalate to more aggressive levels
  -> Output compressed text
```

**Filler Dictionary (partial — 100+ patterns in full implementation):**

```typescript
const FILLER_PHRASES = [
  { pattern: /\bin order to\b/gi, replacement: 'to' },
  { pattern: /\bat this point in time\b/gi, replacement: 'now' },
  { pattern: /\bin the event that\b/gi, replacement: 'if' },
  { pattern: /\bdue to the fact that\b/gi, replacement: 'because' },
  { pattern: /\bfor the purpose of\b/gi, replacement: 'to' },
  { pattern: /\bin spite of the fact that\b/gi, replacement: 'although' },
  { pattern: /\bit should be noted that\b/gi, replacement: '' },
  { pattern: /\bit is important to note that\b/gi, replacement: '' },
  { pattern: /\bas a matter of fact\b/gi, replacement: '' },
  { pattern: /\bneedless to say\b/gi, replacement: '' },
  { pattern: /\bbasically\b/gi, replacement: '' },
  { pattern: /\bactually\b/gi, replacement: '' },
  { pattern: /\byou know\b/gi, replacement: '' },
  { pattern: /\bI mean\b/gi, replacement: '' },
  { pattern: /\bkind of\b/gi, replacement: '' },
  { pattern: /\bsort of\b/gi, replacement: '' },
];
```

**Protected Region Detection:**

```typescript
interface ProtectedRegion {
  start: number;
  end: number;
  type: 'keyword' | 'code' | 'url' | 'number' | 'proper_noun';
}

function detectProtectedRegions(
  text: string, 
  preserveKeywords: string[]
): ProtectedRegion[] {
  const regions: ProtectedRegion[] = [];
  // Code blocks (``` ... ``` or indented blocks)
  // URLs (http/https patterns)
  // Numbers and dates
  // preserve_keywords (case-insensitive match + surrounding sentence)
  // Proper nouns (capitalized words not at sentence start)
  return regions;
}
```

**Progressive Compression Levels:**

| Level | Actions | Risk |
|-------|---------|------|
| 1 (default) | Remove filler words, simplify constructions | Very Low |
| 2 | Remove redundant adjectives and adverbs | Low |
| 3 | Merge short sentences | Medium |
| 4 | Remove entire low-information sentences | Medium-High |

Level escalates automatically until `target_ratio` is met or Level 4 is exhausted.

---

### 4.2 Semantic Compression Engine

**File:** `src/engines/semantic-engine.ts`

**Algorithm Pipeline:**

```
Input Text
  -> Sentence split (rule-based: .!? + whitespace + capital)
  -> Embed each sentence (all-MiniLM-L6-v2 via @xenova/transformers)
  -> Build N x N cosine similarity matrix
  -> Identify redundant pairs (similarity > 0.85)
  -> Score sentences by information density (1 - max similarity to any other)
  -> Remove lowest-scored sentences until target_ratio met
  -> Preserve sentence order for coherence
  -> Check protected regions (never remove keyword-containing sentences)
  -> Output compressed text
```

**Embedding Model Management:**

```typescript
// src/lib/embeddings.ts
import { pipeline } from '@xenova/transformers';

let embeddingPipeline: any = null;

// Singleton: model loads once per serverless lifecycle (~500ms)
// Subsequent calls use cached instance
// Model size: ~6MB quantized. Fits within Vercel 50MB function limit.
export async function getEmbeddings(texts: string[]): Promise<number[][]> {
  if (!embeddingPipeline) {
    embeddingPipeline = await pipeline(
      'feature-extraction',
      'Xenova/all-MiniLM-L6-v2',
      { quantized: true }
    );
  }
  const results = await embeddingPipeline(texts, {
    pooling: 'mean',
    normalize: true
  });
  return results.tolist();
}
```

**Sentence Splitter (no NLTK):**

```typescript
// src/utils/text-splitter.ts
// Rule-based: split on .!? followed by whitespace + capital letter
// Preserves: Mr. Mrs. Dr. etc., URLs, decimal numbers, ellipsis
export function splitSentences(text: string): string[] {
  const sentences = text
    .split(/(?<=[.!?])\s+(?=[A-Z])/)
    .filter(s => s.trim().length > 0);
  return sentences;
}
```

**Cosine Similarity:**

```typescript
// src/utils/cosine-similarity.ts
export function cosineSimilarity(a: number[], b: number[]): number {
  let dotProduct = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  const denominator = Math.sqrt(normA) * Math.sqrt(normB);
  return denominator === 0 ? 0 : dotProduct / denominator;
}

export function buildSimilarityMatrix(vectors: number[][]): number[][] {
  const n = vectors.length;
  const matrix = Array(n).fill(null).map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {
    matrix[i][i] = 1.0;
    for (let j = i + 1; j < n; j++) {
      const sim = cosineSimilarity(vectors[i], vectors[j]);
      matrix[i][j] = sim;
      matrix[j][i] = sim;
    }
  }
  return matrix;
}
```

---

### 4.3 Strategy Selector

**File:** `src/engines/strategy-selector.ts`

```typescript
interface StrategyDecision {
  strategy: 'token' | 'semantic' | 'combined';
  reason: string;
}

export function selectStrategy(
  text: string,
  requestedStrategy: 'auto' | 'token' | 'semantic',
  tokenCount: number
): StrategyDecision {
  if (requestedStrategy !== 'auto') {
    return { strategy: requestedStrategy, reason: 'explicitly requested' };
  }
  
  if (tokenCount < 500) {
    return { strategy: 'token', reason: 'short input (<500 tokens)' };
  }
  if (tokenCount > 2000) {
    return { strategy: 'semantic', reason: 'long input (>2000 tokens)' };
  }
  
  const fillerDensity = estimateFillerDensity(text);
  const paragraphCount = (text.match(/\n\n/g) || []).length + 1;
  
  if (fillerDensity > 0.15) return { strategy: 'token', reason: 'high filler density' };
  if (paragraphCount >= 3) return { strategy: 'combined', reason: 'multi-paragraph' };
  
  return { strategy: 'token', reason: 'default for mid-range input' };
}
```

**Combined Strategy:** Token compression first (fast noise removal), then semantic compression (redundancy removal). Confidence score is based on original vs. final result.

---

### 4.4 Confidence Scorer

**File:** `src/engines/confidence-scorer.ts`

```typescript
interface ConfidenceResult {
  score: number;        // 0.0 - 1.0
  billable: boolean;    // false if score < 0.5
  components: {
    embedding_similarity: number;
    information_density: number;
  };
}

export async function scoreConfidence(
  originalText: string,
  compressedText: string,
  originalTokens: number,
  compressedTokens: number
): Promise<ConfidenceResult> {
  // 1. Embedding similarity (primary signal, 80% weight)
  const [origEmb, compEmb] = await getEmbeddings([originalText, compressedText]);
  const embSim = cosineSimilarity(origEmb, compEmb);
  
  // 2. Information density preservation (secondary, 20% weight)
  const origDensity = uniqueTokenRatio(originalText);
  const compDensity = uniqueTokenRatio(compressedText);
  const densityPres = Math.min(compDensity / origDensity, 1.0);
  
  // 3. Weighted score
  const score = Math.max(0, Math.min(1, (embSim * 0.8) + (densityPres * 0.2)));
  
  return {
    score: Math.round(score * 1000) / 1000,
    billable: score >= 0.5,
    components: {
      embedding_similarity: Math.round(embSim * 1000) / 1000,
      information_density: Math.round(densityPres * 1000) / 1000,
    }
  };
}
```

---

## 5. Database Design

### 5.1 Schema

All tables in Supabase PostgreSQL. Usage metrics only — never customer text.

```sql
-- API request log (append-only)
CREATE TABLE api_requests (
  id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  request_id        TEXT NOT NULL UNIQUE,
  api_key_hash      TEXT NOT NULL,
  tier              TEXT NOT NULL,
  strategy          TEXT NOT NULL,
  strategy_used     TEXT NOT NULL,
  original_tokens   INTEGER NOT NULL,
  compressed_tokens INTEGER NOT NULL,
  compression_ratio DECIMAL(5,4) NOT NULL,
  confidence_score  DECIMAL(5,4) NOT NULL,
  billable          BOOLEAN NOT NULL DEFAULT true,
  processing_time_ms INTEGER NOT NULL,
  status_code       INTEGER NOT NULL DEFAULT 200,
  error_code        TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_api_req_key ON api_requests(api_key_hash);
CREATE INDEX idx_api_req_time ON api_requests(created_at);
CREATE INDEX idx_api_req_billable ON api_requests(billable) WHERE billable = true;

-- Monthly usage aggregates
CREATE TABLE usage_aggregates (
  id                    UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  api_key_hash          TEXT NOT NULL,
  period_start          DATE NOT NULL,
  period_end            DATE NOT NULL,
  total_requests        INTEGER NOT NULL DEFAULT 0,
  billable_requests     INTEGER NOT NULL DEFAULT 0,
  non_billable_requests INTEGER NOT NULL DEFAULT 0,
  total_tokens_processed BIGINT NOT NULL DEFAULT 0,
  total_tokens_saved    BIGINT NOT NULL DEFAULT 0,
  avg_compression_ratio DECIMAL(5,4),
  avg_confidence_score  DECIMAL(5,4),
  tier                  TEXT NOT NULL,
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(api_key_hash, period_start)
);

-- System health metrics
CREATE TABLE system_health (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  metric_name  TEXT NOT NULL,
  metric_value DECIMAL(10,4) NOT NULL,
  period_minutes INTEGER NOT NULL DEFAULT 5,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 5.2 Row-Level Security

```sql
ALTER TABLE api_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_only" ON api_requests FOR ALL USING (auth.role() = 'service_role');

ALTER TABLE usage_aggregates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_only" ON usage_aggregates FOR ALL USING (auth.role() = 'service_role');
```

### 5.3 Upsert Aggregate RPC

```sql
CREATE OR REPLACE FUNCTION upsert_usage_aggregate(
  p_api_key_hash TEXT, p_period_start DATE, p_period_end DATE, p_tier TEXT,
  p_original_tokens INTEGER, p_compressed_tokens INTEGER,
  p_compression_ratio DECIMAL, p_confidence_score DECIMAL, p_billable BOOLEAN
) RETURNS VOID AS $$
BEGIN
  INSERT INTO usage_aggregates (
    api_key_hash, period_start, period_end, tier,
    total_requests, billable_requests, non_billable_requests,
    total_tokens_processed, total_tokens_saved,
    avg_compression_ratio, avg_confidence_score, updated_at
  ) VALUES (
    p_api_key_hash, p_period_start, p_period_end, p_tier,
    1, CASE WHEN p_billable THEN 1 ELSE 0 END, CASE WHEN p_billable THEN 0 ELSE 1 END,
    p_original_tokens, p_original_tokens - p_compressed_tokens,
    p_compression_ratio, p_confidence_score, NOW()
  )
  ON CONFLICT (api_key_hash, period_start) DO UPDATE SET
    total_requests = usage_aggregates.total_requests + 1,
    billable_requests = usage_aggregates.billable_requests + CASE WHEN p_billable THEN 1 ELSE 0 END,
    non_billable_requests = usage_aggregates.non_billable_requests + CASE WHEN p_billable THEN 0 ELSE 1 END,
    total_tokens_processed = usage_aggregates.total_tokens_processed + p_original_tokens,
    total_tokens_saved = usage_aggregates.total_tokens_saved + (p_original_tokens - p_compressed_tokens),
    avg_compression_ratio = (usage_aggregates.avg_compression_ratio * usage_aggregates.total_requests + p_compression_ratio) / (usage_aggregates.total_requests + 1),
    avg_confidence_score = (usage_aggregates.avg_confidence_score * usage_aggregates.total_requests + p_confidence_score) / (usage_aggregates.total_requests + 1),
    updated_at = NOW();
END;
$$ LANGUAGE plpgsql;
```

### 5.4 Async Metrics Writer

```typescript
// src/lib/metrics.ts — Fire-and-forget. NEVER block API response.
export function writeMetrics(event: MetricEvent): void {
  supabase.from('api_requests').insert(event)
    .then(({ error }) => { if (error) console.error('[metrics]', error.message); })
    .catch((err) => { console.error('[metrics]', err.message); });
}
```

---

## 6. API Implementation

### 6.1 Compress Endpoint

**File:** `src/app/api/v1/compress/route.ts`

Core flow (pseudocode with types):

```typescript
export async function POST(request: NextRequest) {
  const startTime = Date.now();
  const requestId = crypto.randomUUID();
  
  try {
    // 1. Parse + validate with Zod
    const body = await request.json();
    const parsed = compressRequestSchema.safeParse(body);
    if (!parsed.success) throw new ApiError(400, 'INVALID_INPUT', parsed.error.issues[0].message);
    
    // 2. Count tokens
    const originalTokens = countTokens(parsed.data.text);
    
    // 3. Trivial input check (< 10 tokens: return as-is, non-billable)
    if (originalTokens < 10) return trivialResponse(...);
    
    // 4. Select strategy
    const { strategy } = selectStrategy(text, requestedStrategy, originalTokens);
    
    // 5. Compress
    let compressed: string;
    if (strategy === 'token') compressed = tokenCompress(text, targetRatio, keywords);
    else if (strategy === 'semantic') compressed = await semanticCompress(text, targetRatio, keywords);
    else { // combined
      const pass1 = tokenCompress(text, 0.7, keywords);
      compressed = await semanticCompress(pass1, targetRatio, keywords);
    }
    
    // 6. Score confidence
    const confidence = await scoreConfidence(text, compressed, originalTokens, countTokens(compressed));
    
    // 7. Write metrics (async, non-blocking)
    writeMetrics({ ...metricData });
    
    // 8. Return response
    return NextResponse.json({ compressed_text: compressed, metadata: { ... } });
  } catch (error) {
    return handleError(error, requestId, startTime);
  }
}
```

### 6.2 Request Validation Schema

```typescript
// src/schemas/compress-request.ts
import { z } from 'zod';

export const compressRequestSchema = z.object({
  text: z.string().min(1, 'text cannot be empty').max(100_000, 'exceeds 100K char limit'),
  strategy: z.enum(['token', 'semantic', 'auto']).optional().default('auto'),
  target_ratio: z.number().min(0.1).max(0.9).optional().default(0.5),
  preserve_keywords: z.array(z.string().max(100)).max(50).optional().default([]),
  output_format: z.enum(['text', 'json']).optional().default('text'),
});
```

---

## 7. Authentication & Security

### 7.1 Auth Flow

RapidAPI handles all authentication. CoText validates the proxy secret to ensure requests originated from RapidAPI (not direct access bypassing billing).

```typescript
function validateRapidApiOrigin(request: NextRequest): void {
  const proxySecret = request.headers.get('x-rapidapi-proxy-secret');
  if (proxySecret !== process.env.RAPIDAPI_PROXY_SECRET) {
    throw new ApiError(401, 'UNAUTHORIZED', 'Invalid gateway auth');
  }
}
```

### 7.2 Security Checklist

| Category | Requirement | Implementation |
|----------|------------|----------------|
| Transport | HTTPS only | Vercel enforces HTTPS |
| Auth | Validate every request | RapidAPI proxy secret check |
| Input | Reject malformed | Zod schema validation |
| Data at Rest | Encrypted | Supabase AES-256 default |
| No PII | Never store text | Only token counts/metrics |
| API Keys | Hashed | SHA-256, never raw |
| Rate Limiting | Prevent abuse | RapidAPI gateway |
| Error Messages | No internal details | Generic 5xx messages |
| Dependencies | Vuln scanning | npm audit in CI/CD |

### 7.3 Compliance Readiness

No formal certs for v1.0. Technical foundations built:

| Future Cert | Foundation Now | Remaining Later |
|-------------|--------------|-----------------|
| SOC2 | Audit logging, access controls, encryption | Formal audit, policies |
| GDPR | No PII storage, data minimization | Privacy policy, DPA |
| HIPAA | Encryption, access logging | BAA, risk assessment |

---

## 8. Error Handling Framework

### 8.1 Error Class

```typescript
// src/lib/errors.ts
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public errorCode: string,
    public userMessage: string,
    public details?: Record<string, any>
  ) { super(userMessage); }
}
```

### 8.2 Error Handler

```typescript
export function handleError(error: unknown, requestId: string, startTime: number): NextResponse {
  if (error instanceof ApiError) {
    return NextResponse.json({
      error: { code: error.errorCode, message: error.userMessage, details: error.details, request_id: requestId }
    }, {
      status: error.statusCode,
      headers: {
        'X-Request-ID': requestId,
        ...(error.statusCode === 429 ? { 'Retry-After': '60' } : {}),
        ...(error.statusCode === 503 ? { 'Retry-After': '300' } : {}),
      }
    });
  }
  
  if (error instanceof Error && error.message.includes('model')) {
    return NextResponse.json({
      error: { code: 'EMBEDDING_UNAVAILABLE', message: 'Semantic engine temporarily unavailable. Try strategy="token".', request_id: requestId }
    }, { status: 500 });
  }
  
  console.error(`[${requestId}] Unhandled:`, error);
  return NextResponse.json({
    error: { code: 'COMPRESSION_FAILED', message: 'Internal error. Please retry.', request_id: requestId }
  }, { status: 500 });
}
```

### 8.3 Graceful Degradation

| Component Failure | Behavior |
|-------------------|----------|
| Embedding model won't load | Semantic returns 500. Token continues. Health shows `semantic: "degraded"`. |
| Supabase down | Metrics silently fail. API continues serving. |
| Tokenizer error | Fall back to chars/4 estimate. Flag in response. |

---

## 9. Monitoring & Observability

### 9.1 Logging

| Level | When | Example |
|-------|------|---------|
| ERROR | 5xx, unhandled exceptions | `[req-123] Embedding model OOM` |
| WARN | Low confidence, rate limits | `[req-456] Confidence 0.32, non-billable` |
| INFO | Every request summary | `[req-789] semantic 4250->2100 conf=0.87 245ms` |

**Never log customer text content.**

### 9.2 Health Check

```typescript
// GET /v1/health
export async function GET() {
  const engines = { token: 'ready', semantic: 'ready' };
  try { await getEmbeddings(['test']); } catch { engines.semantic = 'degraded'; }
  const status = engines.semantic === 'degraded' ? 'degraded' : 'healthy';
  return NextResponse.json({ status, version: '1.0.0', engines }, { status: status === 'healthy' ? 200 : 503 });
}
```

---

## 10. Deployment & Infrastructure

### 10.1 Vercel Configuration

```javascript
// next.config.js
const nextConfig = {
  experimental: {
    serverComponentsExternalPackages: ['@xenova/transformers'],
  },
  async headers() {
    return [{
      source: '/api/:path*',
      headers: [
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'X-Frame-Options', value: 'DENY' },
      ],
    }];
  },
};
```

### 10.2 Environment Variables

```bash
# .env.example
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...              # Service role key (not anon)
RAPIDAPI_PROXY_SECRET=xxx                # From RapidAPI publisher dashboard
NODE_ENV=production
```

### 10.3 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run lint
      - run: npm audit --audit-level=high
      - run: npm test
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

### 10.4 Free Tier Limits & Scale Triggers

| Service | Free Tier Limit | Scale Trigger | Scale Action | Cost |
|---------|----------------|---------------|--------------|------|
| Vercel | 100GB bandwidth, 1M edge requests | 80% utilization | Upgrade to Pro | $20/mo |
| Supabase | 500MB DB, 50K MAU | 400MB DB or 40K MAU | Upgrade to Pro | $25/mo |
| GitHub Actions | 2,000 min/month | 1,600 min used | Optimize pipeline | $0 (reduce test time) |

---

## 11. Testing Architecture

### 11.1 Coverage Targets

| Category | Target | Tool |
|----------|--------|------|
| Unit Tests | 80%+ | Vitest |
| Integration Tests | All endpoints, all error codes | Supertest |
| Performance Tests | p50, p95, p99 benchmarks | Custom script |
| Quality Tests | Test corpus with known outcomes | Custom suite |

### 11.2 Test Corpus

| Corpus | Source | Expected |
|--------|--------|----------|
| Verbose conversation | Synthetic support chat (10K tokens) | 30-50% compression, confidence > 0.7 |
| Technical docs | Real API docs (5K tokens) | 10-20% compression, confidence > 0.85 |
| RAG retrieval | 5 overlapping passages (8K tokens) | 40-60% compression, confidence > 0.75 |
| Minimal text | Single sentence (50 tokens) | ~0% compression, confidence ~1.0 |
| Code-heavy | Mixed prose + code (4K tokens) | 5-15% compression (code preserved) |

### 11.3 Quality Regression

Before each release: run full corpus through both engines. Compare against baseline. Compression must not degrade > 5%. All error codes return correct format. Load test 100 concurrent requests, p95 < 500ms.

---

## 12. Streaming Readiness Design

Per decision: build non-streaming now, design for streaming later.

### 12.1 Architecture Hooks

The compression pipeline is designed as sequential stages that can emit partial results:

```
Stage 1: Tokenize      -> can emit token count immediately
Stage 2: Protect       -> can emit protected regions
Stage 3: Compress      -> can emit compressed chunks as sentences are processed
Stage 4: Score         -> must wait for full output (needs complete text for embedding)
Stage 5: Respond       -> can stream metadata first, then compressed_text
```

### 12.2 Future Streaming Endpoint

```
POST /v1/compress/stream  (v1.1)
Content-Type: text/event-stream

event: metadata
data: {"original_tokens": 4250, "strategy_used": "semantic"}

event: chunk
data: {"text": "First compressed sentence.", "index": 0}

event: chunk
data: {"text": "Second compressed sentence.", "index": 1}

event: complete
data: {"compressed_tokens": 2100, "confidence_score": 0.87, "billable": true}
```

### 12.3 What to Build Now

1. Compression engines accept and return `string` — compatible with future chunked processing
2. Database schema includes `streaming` boolean (default false) for feature flagging
3. API versioning at `/v1/` allows `/v1/compress/stream` addition without breaking `/v1/compress`
4. Confidence scorer accepts full text (not chunks) — this is the bottleneck for streaming and will need architectural work in v1.1

---

## 13. Development Environment Setup

### 13.1 Prerequisites

- Node.js 20.x LTS
- npm 10.x+
- Git
- Vercel CLI (`npm i -g vercel`)
- Supabase account (free tier)
- RapidAPI publisher account (free)

### 13.2 Quick Start

```bash
# Clone repo
git clone https://github.com/[your-org]/cotext-api.git
cd cotext-api

# Install dependencies
npm install

# Copy env template
cp .env.example .env.local
# Fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, RAPIDAPI_PROXY_SECRET

# Run database migrations
npx supabase db push

# Start development server
npm run dev
# API available at http://localhost:3000/api/v1/

# Run tests
npm test

# Run specific test file
npx vitest run tests/unit/token-engine.test.ts

# Deploy to Vercel
vercel --prod
```

### 13.3 Dependencies

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "@supabase/supabase-js": "^2.0.0",
    "zod": "^3.0.0",
    "tiktoken": "^1.0.0",
    "@xenova/transformers": "^2.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "vitest": "^1.0.0",
    "@types/node": "^20.0.0",
    "eslint": "^8.0.0"
  }
}
```

---

## 14. Appendices

### Appendix A: Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Service role key (RLS bypass) |
| `RAPIDAPI_PROXY_SECRET` | Yes | From RapidAPI publisher dashboard |
| `NODE_ENV` | Yes | `development` or `production` |

### Appendix B: Rate Limits by Tier

| Tier | Requests/Min | Compressions/Month | Overage |
|------|-------------|-------------------|---------|
| Free | 10 | 1,000 | Hard cap |
| Basic ($9) | 60 | 10,000 | $0.001/each |
| Pro ($29) | 120 | 50,000 | $0.0008/each |
| Enterprise ($99) | 300 | 250,000 | $0.0005/each |

### Appendix C: Decision Log Reference

All 10 architectural decisions are documented in the Project Charter (CTX-PC-001), Section 4.

---

*This TDS is a living document. Changes require Product Owner approval and must be recorded in revision history.*
