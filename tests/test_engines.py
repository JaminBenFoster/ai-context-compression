"""
Comprehensive tests for CoText Token Compression Engine.
"""

import pytest
from ai_context_compression import (
    Compressor,
    Tokenizer,
    TokenCompressor,
    SemanticCompressor,
    StrategySelector,
    CompressionResult
)


class TestTokenizer:
    """Test token counting."""
    
    def test_count_tokens_english(self):
        """Test token counting for English text."""
        tokenizer = Tokenizer()
        
        # ~4 chars per token rough estimate
        text = "Hello, world! This is a test sentence."
        tokens = tokenizer.count_tokens(text)
        
        # Should be around 10-15 tokens for this text
        assert 5 <= tokens <= 20
    
    def test_count_tokens_empty(self):
        """Test empty string returns 0 tokens."""
        tokenizer = Tokenizer()
        assert tokenizer.count_tokens("") == 0


class TestTokenCompressor:
    """Test token compression strategies."""
    
    def setup_method(self):
        """Set up compressor for tests."""
        self.compressor = TokenCompressor()
    
    def test_selective_context_compression(self):
        """Test selective context compression."""
        text = """
        System: You are a helpful AI assistant. Your name is CoText.
        
        User: Hello, I need help with compression.
        
        Assistant: Hello! I'd be happy to help you with compression. What specifically do you need help with?
        
        User: I want to reduce token usage in my AI applications.
        
        Assistant: That's a great use case for CoText! Our token compression can reduce usage by 30-50%.
        """
        
        result = self.compressor.compress(text, target_ratio=0.7)
        
        # Should reduce tokens
        assert result.compressed_tokens < result.original_tokens
        # Should be billable (confidence should be decent)
        assert result.billable == True
        # Strategy should be recorded
        assert result.strategy_used == "selective_context"
    
    def test_compressible_compression(self):
        """Test compression of repeated sequences."""
        text = "The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog."
        
        result = self.compressor.compress(text, target_ratio=0.5, strategy="compressible")
        
        # Should remove repeated phrases
        assert result.compressed_tokens < result.original_tokens
        assert "The quick brown fox" in result.compressed_text
    
    def test_target_ratio_respected(self):
        """Test that target ratio is approximately respected."""
        text = " ".join([f"This is sentence {i} with some content." for i in range(20)])
        
        result = self.compressor.compress(text, target_ratio=0.5)
        
        # Should be close to target ratio
        actual_ratio = result.compressed_tokens / result.original_tokens
        assert 0.4 <= actual_ratio <= 0.6
    
    def test_preserve_keywords(self):
        """Test keyword preservation."""
        text = "The quick brown fox jumps over the lazy dog. Important: remember to include the keywords."
        
        result = self.compressor.compress(
            text,
            target_ratio=0.3,
            preserve_keywords=["keywords"]
        )
        
        # Keywords should be preserved
        assert "keywords" in result.compressed_text.lower()
    
    def test_confidence_score(self):
        """Test confidence score calculation."""
        text = "This is a short test message."
        
        result = self.compressor.compress(text)
        
        # Confidence should be reasonable for short text
        assert 0.0 <= result.confidence_score <= 1.0
    
    def test_llmlingua_strategy(self):
        """Test LLMLingua-style compression."""
        text = """
        System: You are a helpful AI assistant.
        
        User: What is the capital of France?
        
        Assistant: The capital of France is Paris.
        """
        
        result = self.compressor.compress(text, strategy="llmlingua")
        
        # System message should be preserved
        assert "helpful AI assistant" in result.compressed_text or "System:" in result.compressed_text


class TestSemanticCompressor:
    """Test semantic compression."""
    
    def test_semantic_compression(self):
        """Test semantic compression reduces content."""
        text = """
        Paragraph 1: This is the first paragraph with some unique information.
        
        Paragraph 2: This is the second paragraph. This paragraph contains similar information to what was just said. It repeats some concepts.
        
        Paragraph 3: This paragraph introduces new and different information about machine learning.
        """
        
        compressor = SemanticCompressor()
        result = compressor.compress(text, target_ratio=0.6)
        
        # Should reduce tokens
        assert result.compressed_tokens < result.original_tokens
        # Should use semantic strategy
        assert result.strategy_used == "semantic"
    
    def test_semantic_preserves_different_content(self):
        """Test semantic compression keeps different concepts."""
        text = """
        Python is a programming language. Python is popular for data science.
        
        JavaScript is a programming language. JavaScript is used for web development.
        
        Rust is a systems programming language. Rust guarantees memory safety.
        """
        
        compressor = SemanticCompressor()
        result = compressor.compress(text, target_ratio=0.7)
        
        # Should keep at least some content from each topic
        text_lower = result.compressed_text.lower()
        assert "python" in text_lower or "programming" in text_lower


class TestStrategySelector:
    """Test automatic strategy selection."""
    
    def test_short_text_selects_token(self):
        """Short texts should select token strategy."""
        selector = StrategySelector()
        text = "Hello, world!"  # < 500 tokens
        
        strategy = selector.select(text, 0.5)
        
        assert strategy == "token"
    
    def test_long_text_with_paragraphs_selects_semantic(self):
        """Long texts with paragraphs should select semantic."""
        selector = StrategySelector()
        text = "\n\n".join([f"Paragraph {i}: " + "x" * 100 for i in range(10)])
        
        strategy = selector.select(text, 0.5)
        
        assert strategy == "semantic"


class TestCompressor:
    """Test high-level Compressor class."""
    
    def test_compressor_token(self):
        """Test main Compressor class with token."""
        compressor = Compressor(algorithm="token", ratio_target=0.5)
        text = "This is a test message that should be compressed."
        
        result = compressor.compress(text)
        
        assert result.compressed_tokens < result.original_tokens
    
    def test_compressor_messages(self):
        """Test compress_messages method."""
        compressor = Compressor(algorithm="token")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        text, metadata = compressor.compress_messages(messages, preserve_system=True)
        
        assert "System:" in text or "helpful assistant" in text
        assert "original_tokens" in metadata
        assert "compressed_tokens" in metadata


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_text(self):
        """Test compression of empty text."""
        compressor = TokenCompressor()
        
        result = compressor.compress("")
        
        # Should handle gracefully
        assert result.compressed_text == ""
        assert result.compression_ratio == 1.0
    
    def test_very_short_text(self):
        """Test compression of very short text."""
        compressor = TokenCompressor()
        
        result = compressor.compress("Hi")
        
        # Should handle gracefully
        assert result.compressed_text != None
    
    def test_very_high_target_ratio(self):
        """Test very high target ratio (aggressive compression)."""
        compressor = TokenCompressor()
        text = "This is a sentence with some content. " * 10
        
        result = compressor.compress(text, target_ratio=0.9)
        
        # Should respect target
        assert result.compression_ratio >= 0.8
    
    def test_very_low_target_ratio(self):
        """Test very low target ratio (light compression)."""
        compressor = TokenCompressor()
        text = "This is a sentence with some content. " * 10
        
        result = compressor.compress(text, target_ratio=0.2)
        
        # Should respect target
        assert result.compression_ratio >= 0.15


class TestPerformance:
    """Test performance characteristics."""
    
    def test_compression_speed(self):
        """Test that compression completes quickly."""
        import time
        
        compressor = TokenCompressor()
        text = " ".join([f"This is sentence {i} with unique content." for i in range(100)])
        
        start = time.time()
        result = compressor.compress(text)
        elapsed = (time.time() - start) * 1000
        
        # Should complete in under 1 second
        assert elapsed < 1000, f"Compression took {elapsed:.2f}ms"
    
    def test_metadata_completeness(self):
        """Test that all metadata fields are populated."""
        compressor = TokenCompressor()
        text = "This is a test message for metadata completeness."
        
        result = compressor.compress(text)
        
        assert result.original_tokens > 0
        assert result.compressed_tokens > 0
        assert 0.0 <= result.compression_ratio <= 1.0
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.strategy_used in ["selective_context", "compressible", "llmlingua"]
        assert result.processing_time_ms >= 0
        assert isinstance(result.billable, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
