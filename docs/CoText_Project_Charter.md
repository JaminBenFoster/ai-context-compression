# CoText — Context Compression API
## Project Charter v1.0

---

## Document Control

| Field | Value |
|-------|-------|
| **Document Title** | CoText Project Charter |
| **Document ID** | CTX-PC-001 |
| **Version** | 1.0 |
| **Status** | Approved |
| **Product Owner** | Trong |
| **Created Date** | February 12, 2026 |
| **Last Updated** | February 12, 2026 |

### Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | Feb 12, 2026 | Solution Architect | Initial charter with all decisions finalized |

---

## 1. Executive Summary

**CoText** is a developer-facing API that compresses LLM context windows — reducing token usage, lowering API costs, and enabling longer conversations within model limits. It is the first product in the OpenClaw API suite for the AI agent economy.

CoText solves a problem that LLM providers (OpenAI, Anthropic, Google) are disincentivized to solve: their revenue increases with more token consumption. CoText reduces it. This creates a natural market where no incumbent will compete.

**Business Model:** Usage-based API monetized through RapidAPI marketplace (MVP), with a pathway to direct Stripe billing for enterprise customers.

**Target:** $200 MRR within 60 days of launch. $500 MRR within 90 days.

---

## 2. Problem Statement

### The Pain
Developers building AI applications face escalating costs from LLM API usage. Context windows fill with redundant information — conversation history, repeated system prompts, verbose RAG retrievals — driving up token costs without proportional value.

### Quantified Impact
- Average LLM API call contains **30-50% redundant tokens** in context
- GPT-4 Turbo costs $10/1M input tokens; Claude 3.5 Sonnet costs $3/1M input tokens
- A chatbot processing 1M conversations/month at 4K tokens average = **4B tokens = $12,000-$40,000/month** in input costs alone
- **30% compression = $3,600-$12,000/month saved** per customer

### Why Now
- LLM adoption is accelerating (enterprise AI spending up 40% YoY)
- Context windows are getting larger (128K-1M tokens) but costs scale linearly
- No dominant API-first compression service exists — only Python libraries (LLMLingua, etc.) that require self-hosting
- The AI agent economy creates compounding context (agents passing context between each other)

---

## 3. Vision & Objectives

### Vision
Become the default context optimization layer for AI applications — the "Cloudflare for LLM tokens."

### Success Criteria

| Metric | Target | Timeline |
|--------|--------|----------|
| **MRR** | $200 | 60 days post-launch |
| **MRR** | $500 | 90 days post-launch |
| **Free-tier users** | 50+ | 30 days post-launch |
| **Paid conversions** | 10%+ of free users | 90 days post-launch |
| **API latency** | <500ms p95 for 4K token input | Launch |
| **Compression ratio** | 30-50% token reduction | Launch |
| **Semantic fidelity** | >90% meaning preservation (measured by embedding similarity) | Launch |

### Non-Goals (v1.0)
- Streaming compression responses
- SOC2 / HIPAA / formal compliance certifications
- Enterprise self-hosted deployment
- Prompt compression (framework-specific logic)
- Android/iOS SDKs
- Multi-language support beyond English

---

## 4. Key Decisions Log

All architectural decisions have been finalized by the Product Owner.

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | **Deployment Model** | **A) RapidAPI only** for MVP. Design for hybrid (add Stripe direct billing later). | Fastest to market. Zero billing infrastructure. 4M+ developer discovery. Upgrade to hybrid at $500 MRR or first enterprise inquiry. |
| 2 | **Pricing Strategy** | **C) Hybrid tiered + overage** with upgrade path | Captures both indie developers (flat tiers) and high-volume users (overage billing). Route to upgrade built in from day one. |
| 3 | **Compression Algorithms** | **C) Token + Semantic** | Token compression for high-volume/chatbot use cases. Semantic compression for RAG/research. Covers 80% of use cases. Prompt compression deferred to v2. |
| 4 | **Data Storage** | **B) Metadata only** | Store compression metrics (token counts, ratios, timestamps) for analytics and billing. Never store customer text content. Privacy-first positioning. |
| 5 | **Error Handling** | **C) Tiered confidence scores + fair billing** | Return compression with confidence score. Don't charge for low-confidence results. Customers decide their own threshold. |
| 6 | **Streaming** | **Non-streaming now, design for streaming later** | Simpler MVP. Architecture will include hooks for streaming upgrade without breaking changes. |
| 7 | **Compliance** | **Skip formal certifications. Build technical foundations.** | No SOC2/HIPAA/GDPR certification until enterprise customers demand it. But build with encryption, audit logging, and data isolation from day one so certification is achievable when needed. |
| 8 | **Company/Product Name** | **CoText** (working name, may change to Tessier) | Use CoText for all documentation. Can rebrand later — API contracts use versioned endpoints, not brand names. |
| 9 | **Uptime SLA** | **99% target, no contractual SLA** | 7.2 hours downtime/month acceptable for dev tools. Upgrade to 99.9% SLA when first enterprise customer asks. |
| 10 | **Infrastructure Budget** | **$0/month MVP (free tiers only)** | Vercel free tier, Supabase free tier, RapidAPI free publisher. Scale spending only when revenue justifies it. |

---

## 5. Scope

### In Scope (v1.0 MVP)

| Feature | Description | Priority |
|---------|-------------|----------|
| **Token Compression** | Rule-based token reduction (filler removal, deduplication, abbreviation) | Must Have |
| **Semantic Compression** | Embedding-based redundancy detection and removal | Must Have |
| **REST API** | Single endpoint: `POST /v1/compress` | Must Have |
| **Confidence Scoring** | Return confidence score (0-1) with every compression result | Must Have |
| **Fair Billing** | Don't count low-confidence results against usage quota | Must Have |
| **RapidAPI Integration** | Listed on marketplace with free + paid tiers | Must Have |
| **Usage Analytics** | Dashboard showing compression stats, token savings, API calls | Must Have |
| **Rate Limiting** | Per-tier rate limits enforced at API gateway level | Must Have |
| **API Key Auth** | RapidAPI-managed authentication | Must Have |
| **Health Check** | `GET /v1/health` endpoint | Must Have |
| **Error Responses** | Standardized error format with actionable messages | Must Have |

### Out of Scope (Future Versions)

| Feature | Target Version | Trigger |
|---------|---------------|---------|
| Streaming responses | v1.1 | Architecture designed for it; implement when customers request |
| Prompt compression | v2.0 | Enterprise demand |
| Direct Stripe billing | v1.1 | $500 MRR or first enterprise inquiry |
| SDKs (Python, Node, Go) | v1.1 | 50+ active API users |
| SOC2 certification | v2.0+ | Enterprise customer requirement |
| Self-hosted deployment | v3.0 | Enterprise demand with $10K+ ACV |
| Batch compression | v1.1 | High-volume customer request |
| Custom compression profiles | v2.0 | Power user demand |
| Multi-language compression | v2.0 | International expansion |

---

## 6. Technical Architecture Overview

### High-Level Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│                 │     │                  │     │                  │
│   Developer     │────▶│   RapidAPI       │────▶│   CoText API     │
│   Application   │◀────│   Gateway        │◀────│   (Vercel)       │
│                 │     │                  │     │                  │
└─────────────────┘     │  • Auth          │     │  • Token Engine  │
                        │  • Rate Limit    │     │  • Semantic Eng. │
                        │  • Billing       │     │  • Scoring       │
                        │  • Analytics     │     │  • Metrics       │
                        └──────────────────┘     └────────┬─────────┘
                                                          │
                                                          ▼
                                                 ┌──────────────────┐
                                                 │   Supabase       │
                                                 │                  │
                                                 │  • Usage metrics │
                                                 │  • Compression   │
                                                 │    statistics    │
                                                 │  • API key maps  │
                                                 └──────────────────┘
```

### Technology Stack

| Component | Technology | Cost (MVP) |
|-----------|------------|------------|
| **Runtime** | Node.js / TypeScript | — |
| **Framework** | Next.js API Routes (Vercel) | $0 (free tier: 100GB bandwidth, 1M edge requests) |
| **Database** | Supabase PostgreSQL | $0 (free tier: 500MB, 50K monthly active users) |
| **Embedding Model** | all-MiniLM-L6-v2 (open-source, self-hosted) | $0 (runs in Vercel serverless function) |
| **Tokenizer** | tiktoken (OpenAI's tokenizer, open-source) | $0 |
| **API Gateway** | RapidAPI | $0 (publisher is free; they take 20% of revenue) |
| **Monitoring** | Vercel Analytics + Supabase Dashboard | $0 |
| **CI/CD** | GitHub Actions | $0 (2,000 min/month free) |

**Total MVP Infrastructure Cost: $0/month**

---

## 7. Pricing Model

### RapidAPI Tiers

| Tier | Price | Included | Overage | Rate Limit |
|------|-------|----------|---------|------------|
| **Free** | $0/month | 1,000 compressions/month | N/A (hard cap) | 10 req/min |
| **Basic** | $9/month | 10,000 compressions/month | $0.001/compression | 60 req/min |
| **Pro** | $29/month | 50,000 compressions/month | $0.0008/compression | 120 req/min |
| **Enterprise** | $99/month | 250,000 compressions/month | $0.0005/compression | 300 req/min |

### Revenue Projections

| Milestone | Timeline | Customers | Revenue (before RapidAPI fee) | Net Revenue (80%) |
|-----------|----------|-----------|-------------------------------|-------------------|
| Launch | Week 0 | 0 | $0 | $0 |
| Traction | Day 30 | 50 free, 5 paid | ~$100 | ~$80 |
| Validation | Day 60 | 100 free, 15 paid | ~$250 | ~$200 |
| Growth | Day 90 | 200 free, 30 paid | ~$625 | ~$500 |

### Fair Billing Policy
- Compressions returning confidence score < 0.5 are **not counted** against the customer's quota
- This is a key differentiator and trust-builder
- Estimated impact: ~5-10% of compressions are low-confidence (acceptable margin)

---

## 8. Timeline

### Development Schedule (4-Week Sprint)

| Week | Phase | Deliverables |
|------|-------|-------------|
| **Week 1** | **Foundation** | Project setup (TypeScript, Vercel, Supabase). Token compression engine. Basic API endpoint. Unit tests. |
| **Week 2** | **Core Engine** | Semantic compression engine (embedding model integration). Confidence scoring system. Usage tracking/metrics. Error handling framework. |
| **Week 3** | **Integration** | RapidAPI listing and configuration. Rate limiting. Analytics dashboard (basic). API documentation (OpenAPI spec). |
| **Week 4** | **Launch Prep** | Load testing. Edge case handling. Landing page on RapidAPI. Beta user outreach. Launch. |

### Key Milestones

| Milestone | Date | Definition of Done |
|-----------|------|-------------------|
| **M1: Engine Working** | Week 1 End | Token compression returns valid results with >20% reduction on test corpus |
| **M2: Full API** | Week 2 End | Both compression types working, confidence scores returning, metrics logging |
| **M3: Marketplace Ready** | Week 3 End | Listed on RapidAPI, all tiers configured, rate limiting active |
| **M4: Launch** | Week 4 End | 5+ beta users testing, documentation complete, monitoring active |

---

## 9. Risk Assessment

| # | Risk | Probability | Impact | Mitigation |
|---|------|-------------|--------|------------|
| 1 | **Compression quality too low** — results are garbled or lose critical meaning | Medium | High | Confidence scoring prevents bad results from reaching customers. Extensive test corpus. Tunable compression levels. |
| 2 | **Latency too high** — embedding model makes API slow | Medium | Medium | Use lightweight model (MiniLM, 22M params). Cache embeddings for repeated content. Set p95 < 500ms target. |
| 3 | **RapidAPI discovery is poor** — no organic traffic | Medium | Medium | Supplement with dev community content (blog posts, Twitter, Reddit). Cross-promote with future OpenClaw APIs. Direct outreach to AI dev communities. |
| 4 | **Free tier abuse** — users create multiple accounts to avoid paying | Low | Low | RapidAPI handles account management. Monitor for patterns. Not worth solving until it's a real problem. |
| 5 | **Competitor launches** — a well-funded company ships a similar API | Low | High | Speed to market is the moat. Deep integration with RapidAPI ecosystem. Expand to multi-API suite (IDEA-012, IDEA-004) to create switching costs. |
| 6 | **Vercel free tier limits hit** — traffic exceeds free allowances | Low | Low | Good problem to have — means revenue is coming. Upgrade to $20/month Vercel Pro when needed. |
| 7 | **Embedding model quality degrades on domain-specific text** — medical, legal, etc. | Medium | Medium | v1.0 targets general English text. Document limitations. Add domain-specific models in v2.0. |

---

## 10. Stakeholders & Roles

| Role | Person | Responsibilities |
|------|--------|-----------------|
| **Product Owner** | Trong | Final decisions on scope, priorities, and business strategy |
| **Solution Architect** | AI Agent | Technical architecture, document creation, code review |
| **Developer** | Claude Code / Cursor | Implementation, testing, deployment |
| **QA** | Trong + automated tests | Acceptance testing, beta user feedback |

---

## 11. Success Metrics & Kill Criteria

### Continue Signals (at Day 60)
- 50+ free-tier users (organic RapidAPI discovery working)
- 5+ paid customers
- API latency < 500ms p95
- Compression ratio > 25% average
- Net revenue > $100/month

### Pivot Signals (at Day 60)
- < 20 free-tier users (discovery not working — consider direct marketing)
- 0 paid customers (value proposition not clear — consider repositioning)
- Compression quality complaints > 20% of feedback

### Kill Criteria (at Day 90)
- < 10 total users (no market demand)
- $0 revenue (free users won't convert)
- Technical blockers that require >$500/month infrastructure

---

## 12. Dependencies

| Dependency | Risk Level | Fallback |
|------------|-----------|----------|
| **RapidAPI marketplace** | Low | Self-hosted with Stripe (planned for v1.1 anyway) |
| **Vercel hosting** | Low | Railway, Fly.io, or AWS Lambda as alternatives |
| **Supabase** | Low | PlanetScale, Neon, or direct PostgreSQL |
| **tiktoken library** | Very Low | Open-source, well-maintained by OpenAI |
| **all-MiniLM-L6-v2** | Low | Multiple equivalent models on HuggingFace |

---

## 13. Future Roadmap (Post-MVP)

### v1.1 (Month 2-3, triggered by customer demand)
- Streaming compression responses
- Python and Node.js SDKs
- Direct Stripe billing option
- Batch compression endpoint

### v2.0 (Month 4-6, triggered by enterprise interest)
- Prompt compression (LangChain, LlamaIndex integration)
- Custom compression profiles
- SOC2 readiness (if enterprise customer requires)
- Multi-language support

### OpenClaw Suite Expansion
- **IDEA-012: Cost Attribution API** — natural upsell ("you compress tokens, now track where costs go")
- **IDEA-004: Agent Negotiation API** — completes the suite ("track costs, then let agents negotiate them")

---

*This charter is a living document. Updates require Product Owner approval and must be recorded in the revision history.*
