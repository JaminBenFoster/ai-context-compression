"""
CoText - AI Context Compression API

Reduce token usage by 80%+ in AI-to-AI communication.

Usage:
    from ai_context_compression import Compressor
    
    compressor = Compressor(algorithm="token")
    result = compressor.compress(conversation_history)
    print(f"Reduced from {result.original_tokens} to {result.compressed_tokens} tokens")
"""

from ai_context_compression.engines import (
    TokenCompressor,
    SemanticCompressor,
    StrategySelector,
    CompressionResult,
    Tokenizer
)
from ai_context_compression.api import CompressRequest, APIServer

__version__ = "0.1.0"

__all__ = [
    "Tokenizer",
    "TokenCompressor", 
    "SemanticCompressor",
    "StrategySelector",
    "CompressionResult",
    "CompressRequest",
    "APIServer",
]

class Compressor:
    """
    Main compressor class for easy use.
    
    Args:
        algorithm: 'token' or 'semantic'
        ratio_target: Target compression ratio (0.1-0.9)
    
    Example:
        >>> from ai_context_compression import Compressor
        >>> compressor = Compressor(algorithm="token", ratio_target=0.5)
        >>> result = compressor.compress(conversation_history)
        >>> print(f"Reduced by {1-result.compression_ratio:.1%}")
    """
    
    def __init__(
        self,
        algorithm: str = "token",
        ratio_target: float = 0.5
    ):
        self.algorithm = algorithm
        self.ratio_target = ratio_target
        
        if algorithm == "token":
            self.engine = TokenCompressor()
        elif algorithm == "semantic":
            self.engine = SemanticCompressor()
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def compress(
        self,
        text: str,
        preserve_keywords: list = None,
        strategy: str = None
    ) -> CompressionResult:
        """
        Compress text.
        
        Args:
            text: Text to compress
            preserve_keywords: Keywords to preserve verbatim
            strategy: Override strategy selection
            
        Returns:
            CompressionResult with compressed text and metadata
        """
        # Auto-select strategy if not specified
        if strategy is None or strategy == "auto":
            selector = StrategySelector()
            strategy = selector.select(text, self.ratio_target)
        
        return self.engine.compress(
            text,
            target_ratio=self.ratio_target,
            preserve_keywords=preserve_keywords,
            strategy=strategy
        )
    
    def compress_messages(
        self,
        messages: list,
        preserve_system: bool = True
    ) -> tuple[str, dict]:
        """
        Compress a list of chat messages.
        
        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
            preserve_system: Whether to always keep system messages
            
        Returns:
            Tuple of (compressed_text, metadata)
        """
        # Format messages as text
        text_parts = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "system" and preserve_system:
                # Always include system messages
                text_parts.append(f"System: {content}")
            else:
                text_parts.append(f"{role.title()}: {content}")
        
        text = "\n".join(text_parts)
        
        # Compress (system messages will be preserved by the engine)
        result = self.compress(text)
        
        return result.compressed_text, result.to_dict()
