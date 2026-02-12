"""
CoText API - POST /v1/compress

REST API for context compression.
"""

import json
import time
from typing import Optional
from dataclasses import dataclass
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


@dataclass
class CompressRequest:
    """Request body for compress endpoint."""
    text: str
    strategy: str = "auto"
    target_ratio: float = 0.5
    preserve_keywords: Optional[list] = None
    output_format: str = "json"
    
    @classmethod
    def from_json(cls, data: dict) -> "CompressRequest":
        return cls(
            text=data.get("text", ""),
            strategy=data.get("strategy", "auto"),
            target_ratio=float(data.get("target_ratio", 0.5)),
            preserve_keywords=data.get("preserve_keywords"),
            output_format=data.get("output_format", "json")
        )
    
    def validate(self) -> tuple[bool, str]:
        """Validate request."""
        if not self.text or len(self.text.strip()) == 0:
            return False, "text is required"
        
        if len(self.text) > 100000:
            return False, "text must be <= 100,000 characters"
        
        if self.target_ratio < 0.1 or self.target_ratio > 0.9:
            return False, "target_ratio must be between 0.1 and 0.9"
        
        valid_strategies = ["auto", "token", "semantic", "selective_context", "compressible", "llmlingua"]
        if self.strategy not in valid_strategies:
            return False, f"strategy must be one of {valid_strategies}"
        
        return True, ""


class CompressHandler(BaseHTTPRequestHandler):
    """HTTP handler for compress endpoint."""
    
    def log_message(self, format, *args):
        """Custom logging."""
        print(f"[{self.log_date_time_string()}] {format % args}")
    
    def _send_json(self, status: int, data: dict):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path != "/v1/compress":
            self._send_json(404, {"error": "Not found"})
            return
        
        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send_json(400, {"error": "Request body required"})
            return
        
        try:
            body = self.rfile.read(content_length)
            data = json.loads(body.decode())
        except json.JSONDecodeError as e:
            self._send_json(400, {"error": f"Invalid JSON: {str(e)}"})
            return
        
        # Parse and validate request
        try:
            request = CompressRequest.from_json(data)
        except Exception as e:
            self._send_json(400, {"error": f"Invalid request: {str(e)}"})
            return
        
        valid, error_msg = request.validate()
        if not valid:
            self._send_json(400, {"error": error_msg})
            return
        
        # Import engines
        from ai_context_compression.engines import TokenCompressor, SemanticCompressor, StrategySelector
        
        start_time = time.time()
        
        # Select strategy
        selector = StrategySelector()
        if request.strategy == "auto":
            strategy = selector.select(request.text, request.target_ratio)
        else:
            strategy = request.strategy
        
        # Apply compression
        if strategy in ["token", "selective_context", "compressible", "llmlingua"]:
            compressor = TokenCompressor()
            result = compressor.compress(
                request.text,
                target_ratio=request.target_ratio,
                preserve_keywords=request.preserve_keywords,
                strategy=strategy
            )
        else:  # semantic
            compressor = SemanticCompressor()
            result = compressor.compress(
                request.text,
                target_ratio=request.target_ratio,
                preserve_keywords=request.preserve_keywords
            )
        
        # Build response
        processing_time_ms = (time.time() - start_time) * 1000
        
        response_data = {
            "compressed_text": result.compressed_text,
            "metadata": {
                "original_tokens": result.original_tokens,
                "compressed_tokens": result.compressed_tokens,
                "compression_ratio": result.compression_ratio,
                "confidence_score": result.confidence_score,
                "strategy_used": result.strategy_used,
                "processing_time_ms": round(processing_time_ms, 2),
                "billable": result.billable
            }
        }
        
        self._send_json(200, response_data)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/v1/health":
            self._send_json(200, {"status": "healthy", "service": "CoText API"})
        elif self.path == "/":
            self._send_json(200, {
                "service": "CoText - Context Compression API",
                "version": "1.0.0",
                "endpoints": {
                    "POST /v1/compress": "Compress text context",
                    "GET /v1/health": "Health check"
                }
            })
        else:
            self._send_json(404, {"error": "Not found"})


class APIServer:
    """Simple HTTP API server."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the API server."""
        self.server = HTTPServer((self.host, self.port), CompressHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        print(f"🚀 CoText API running on http://{self.host}:{self.port}")
    
    def stop(self):
        """Stop the API server."""
        if self.server:
            self.server.shutdown()
            print("🛑 CoText API stopped")


# Run server if executed directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CoText API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    args = parser.parse_args()
    
    server = APIServer(args.host, args.port)
    
    try:
        server.start()
        print("Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
