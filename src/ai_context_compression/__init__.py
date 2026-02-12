"""
AI Context Compression Engine

Core compression algorithms for reducing token usage in AI conversations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import json


class CompressionStrategy(ABC):
    """Abstract base class for compression strategies."""
    
    @abstractmethod
    def compress(self, context: List[Dict[str, Any]]) -> bytes:
        """Compress context into bytes."""
        pass
    
    @abstractmethod
    def decompress(self, compressed: bytes) -> List[Dict[str, Any]]:
        """Decompress bytes back to context."""
        pass
    
    @abstractmethod
    def get_compression_ratio(self) -> float:
        """Return target compression ratio (0.0-1.0)."""
        pass


class ZstdCompressor(CompressionStrategy):
    """Zstandard compression strategy."""
    
    def __init__(self, ratio_target: float = 0.2):
        self.ratio_target = ratio_target
    
    def compress(self, context: List[Dict[str, Any]]) -> bytes:
        import zstandard as zstd
        data = json.dumps(context).encode('utf-8')
        cctx = zstd.ZstdCompressor(level=3)
        return cctx.compress(data)
    
    def decompress(self, compressed: bytes) -> List[Dict[str, Any]]:
        import zstandard as zstd
        dctx = zstd.ZstdDecompressor()
        data = dctx.decompress(compressed)
        return json.loads(data.decode('utf-8'))
    
    def get_compression_ratio(self) -> float:
        return self.ratio_target


class LZ4Compressor(CompressionStrategy):
    """LZ4 compression strategy (faster, slightly less compression)."""
    
    def __init__(self, ratio_target: float = 0.25):
        self.ratio_target = ratio_target
    
    def compress(self, context: List[Dict[str, Any]]) -> bytes:
        import lz4.frame
        data = json.dumps(context).encode('utf-8')
        return lz4.frame.compress(data)
    
    def decompress(self, compressed: bytes) -> List[Dict[str, Any]]:
        import lz4.frame
        data = lz4.frame.decompress(compressed)
        return json.loads(data.decode('utf-8'))
    
    def get_compression_ratio(self) -> float:
        return self.ratio_target


class ContextManager:
    """
    Manages context window with priority-based retention.
    """
    
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
    
    def prioritize(
        self, 
        context: List[Dict[str, Any]], 
        priority_rules: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retain most important context based on priority rules.
        
        Args:
            context: List of context items (messages, system prompts, etc.)
            priority_rules: Dict mapping item types to priority weights
            
        Returns:
            Prioritized context within token limit
        """
        if priority_rules is None:
            priority_rules = {
                "system": 1.0,
                "user": 0.8,
                "assistant": 0.6,
                "function_call": 0.9,
                "function_result": 0.7
            }
        
        # Sort by priority
        scored = []
        for item in context:
            item_type = item.get("role", "user")
            score = priority_rules.get(item_type, 0.5)
            item_tokens = self._estimate_tokens(item)
            score_per_token = score / item_tokens if item_tokens > 0 else 0
            scored.append((score_per_token, item))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Select items until token limit
        selected = []
        total_tokens = 0
        for _, item in scored:
            item_tokens = self._estimate_tokens(item)
            if total_tokens + item_tokens <= self.max_tokens:
                selected.append(item)
                total_tokens += item_tokens
        
        return selected
    
    def _estimate_tokens(self, item: Dict[str, Any]) -> int:
        """Rough token estimation."""
        text = json.dumps(item)
        return len(text) // 4  # Approximate: 4 chars per token


class Compressor:
    """
    Main compressor class combining compression strategies and context management.
    """
    
    def __init__(
        self, 
        algorithm: str = "zstd",
        ratio_target: float = 0.2,
        max_tokens: int = 8000
    ):
        self.ratio_target = ratio_target
        self.context_manager = ContextManager(max_tokens)
        
        if algorithm == "zstd":
            self.strategy = ZstdCompressor(ratio_target)
        elif algorithm == "lz4":
            self.strategy = LZ4Compressor(ratio_target)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def compress(
        self, 
        context: List[Dict[str, Any]],
        priority_rules: Optional[Dict[str, float]] = None
    ) -> bytes:
        """
        Compress conversation context.
        
        Args:
            context: List of conversation messages
            priority_rules: Optional custom priority rules
            
        Returns:
            Compressed bytes
        """
        # Prioritize context first
        prioritized = self.context_manager.prioritize(context, priority_rules)
        return self.strategy.compress(prioritized)
    
    def decompress(self, compressed: bytes) -> List[Dict[str, Any]]:
        """Decompress context back to original form."""
        return self.strategy.decompress(compressed)
    
    def get_compression_ratio(self) -> float:
        """Return target compression ratio."""
        return self.strategy.get_compression_ratio()
