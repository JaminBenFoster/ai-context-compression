"""
Tests for AI Context Compression Engine.
"""

import pytest
from ai_context_compression import (
    Compressor,
    ContextManager,
    ZstdCompressor,
    LZ4Compressor
)


class TestContextManager:
    """Test context window management."""
    
    def test_prioritize_preserves_system_messages(self):
        """System messages should have highest priority."""
        context = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        
        manager = ContextManager(max_tokens=100)
        result = manager.prioritize(context)
        
        # System message should be preserved
        roles = [item["role"] for item in result]
        assert "system" in roles
    
    def test_prioritize_respects_token_limit(self):
        """Should respect max_tokens limit."""
        long_content = "x" * 1000
        context = [
            {"role": "system", "content": long_content},
            {"role": "user", "content": long_content},
            {"role": "assistant", "content": long_content},
        ]
        
        manager = ContextManager(max_tokens=100)
        result = manager.prioritize(context)
        
        # Total tokens should be under limit
        total_tokens = sum(manager._estimate_tokens(item) for item in result)
        assert total_tokens <= 100
    
    def test_custom_priority_rules(self):
        """Custom priority rules should override defaults."""
        context = [
            {"role": "user", "content": "Important!"},
            {"role": "assistant", "content": "Less important"},
        ]
        
        rules = {"user": 0.1, "assistant": 0.9}
        manager = ContextManager(max_tokens=1000)
        result = manager.prioritize(context, priority_rules=rules)
        
        # Assistant should be prioritized with custom rules
        roles = [item["role"] for item in result]
        assert roles[0] == "assistant"


class TestCompressor:
    """Test main Compressor class."""
    
    def test_zstd_compression(self):
        """Zstd compression should work correctly."""
        context = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "2+2 equals 4."},
        ]
        
        compressor = Compressor(algorithm="zstd", ratio_target=0.5)
        compressed = compressor.compress(context)
        decompressed = compressor.decompress(compressed)
        
        assert decompressed == context
    
    def test_lz4_compression(self):
        """LZ4 compression should work correctly."""
        context = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ]
        
        compressor = Compressor(algorithm="lz4", ratio_target=0.5)
        compressed = compressor.compress(context)
        decompressed = compressor.decompress(compressed)
        
        assert decompressed == context
    
    def test_compression_reduces_size(self):
        """Compression should reduce data size."""
        context = [
            {"role": "system", "content": "x" * 5000},
            {"role": "user", "content": "y" * 5000},
        ]
        
        compressor = Compressor(algorithm="zstd")
        compressed = compressor.compress(context)
        
        original_size = len(str(context).encode('utf-8'))
        
        assert len(compressed) < original_size
    
    def test_unknown_algorithm_raises_error(self):
        """Unknown algorithm should raise ValueError."""
        with pytest.raises(ValueError):
            Compressor(algorithm="unknown")


class TestCompressionRatio:
    """Test compression ratio targeting."""
    
    def test_zstd_ratio_target(self):
        """Zstd should respect ratio target."""
        compressor = ZstdCompressor(ratio_target=0.2)
        assert compressor.get_compression_ratio() == 0.2
    
    def test_lz4_ratio_target(self):
        """LZ4 should respect ratio target."""
        compressor = LZ4Compressor(ratio_target=0.3)
        assert compressor.get_compression_ratio() == 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
