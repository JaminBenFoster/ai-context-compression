# AI Context Compression & Transport API

Reduce token usage by 80%+ with intelligent context compression for AI-to-AI communication.

## Overview

This project provides:
- **Core Compression Engine** - Lossless compression algorithms (LZ4, Zstd, custom)
- **Context Window Management** - Smart priority-based context retention
- **Transport Layer** - HTTP/WebSocket streaming for compressed context transfer
- **Python SDK** - Official client library with full API coverage

## Installation

```bash
pip install ai-context-compression
```

## Quick Start

```python
from ai_context_compression import Compressor

compressor = Compressor(algorithm="zstd", ratio_target=0.2)
compressed = compressor.compress(conversation_history)
# Send compressed context to AI endpoint
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Service    │────▶│  Compressor     │────▶│  Transport      │
│   (Provider)    │◀────│  Engine         │◀────│  Layer          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │  Context        │
                     │  Manager        │
                     └─────────────────┘
```

## Phases

- **Phase 1:** Core Engine & API Skeleton
- **Phase 2:** Transport Layer & SDK
- **Phase 3:** Testing & Performance
- **Phase 4:** Documentation & Beta
- **Phase 5:** v1.0.0 Release

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT
