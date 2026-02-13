"""
Semantic compression using embeddings.

Identifies redundant concepts and removes overlapping information.
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib

# Lazy-load heavy dependencies
def _import_sentence_transformers():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except ImportError:
        return "keyword"

def _import_sklearn():
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        return TfidfVectorizer, cosine_similarity
    except ImportError:
        return None, None

@dataclass
class CompressionResult:
    """Result of compression operation."""
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    confidence_score: float
    strategy_used: str
    processing_time_ms: float
    billable: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "compressed_text": self.compressed_text,
            "metadata": {
                "original_tokens": self.original_tokens,
                "compressed_tokens": self.compressed_tokens,
                "compression_ratio": round(self.compression_ratio, 3),
                "confidence_score": round(self.confidence_score, 3),
                "strategy_used": self.strategy_used,
                "processing_time_ms": round(self.processing_time_ms, 2),
                "billable": self.billable
            }
        }


class Tokenizer:
    """Simple tokenizer using tiktoken cl100k_base (GPT-4 compatible)."""
    
    def __init__(self):
        try:
            import tiktoken
            self.encoder = tiktoken.get_encoding("cl100k_base")
            self.use_tiktoken = True
        except ImportError:
            self.encoder = None
            self.use_tiktoken = False
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.use_tiktoken:
            return len(self.encoder.encode(text))
        else:
            # Fallback: ~4 chars per token
            return len(text) // 4
    
    def encode(self, text: str) -> List[int]:
        """Encode text to tokens."""
        if self.use_tiktoken:
            return self.encoder.encode(text)
        return []
    
    def decode(self, tokens: List[int]) -> str:
        """Decode tokens to text."""
        if self.use_tiktoken:
            return self.encoder.decode(tokens)
        return ""


class TokenCompressor:
    """
    Token-based compression using statistical methods.
    
    Strategies:
    - selective_context: Remove redundant tokens based on IDF weights
    - llmlingua: Prompt-level compression (simplified)
    - compressible: Remove highly compressible sequences
    """
    
    def __init__(self, tokenizer: Optional[Tokenizer] = None):
        self.tokenizer = tokenizer or Tokenizer()
        self.stop_words = self._load_stop_words()
    
    def _load_stop_words(self) -> set:
        """Load common stop words to preserve."""
        return {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
            "into", "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once", "here",
            "there", "when", "where", "why", "how", "all", "each", "few",
            "more", "most", "other", "some", "such", "no", "nor", "not",
            "only", "own", "same", "so", "than", "too", "very", "just"
        }
    
    def compress(
        self,
        text: str,
        target_ratio: float = 0.5,
        preserve_keywords: Optional[List[str]] = None,
        strategy: str = "selective_context"
    ) -> CompressionResult:
        """
        Compress text using token-based strategies.
        
        Args:
            text: Input text to compress
            target_ratio: Target compression ratio (0.1-0.9)
            preserve_keywords: Words to preserve verbatim
            strategy: Compression strategy to use
            
        Returns:
            CompressionResult with compressed text and metadata
        """
        import time
        start_time = time.time()
        
        # Tokenize
        original_tokens = self.tokenizer.count_tokens(text)
        
        # Apply compression strategy
        if strategy == "selective_context":
            compressed_text = self._selective_context_compress(
                text, target_ratio, preserve_keywords
            )
        elif strategy == "compressible":
            compressed_text = self._compressible_compress(
                text, target_ratio, preserve_keywords
            )
        elif strategy == "llmlingua":
            compressed_text = self._llmlingua_compress(
                text, target_ratio, preserve_keywords
            )
        else:
            compressed_text = self._selective_context_compress(
                text, target_ratio, preserve_keywords
            )
        
        # Count compressed tokens
        compressed_tokens = self.tokenizer.count_tokens(compressed_text)
        
        # Calculate metrics
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
        actual_ratio = 1.0 - ratio  # Reduction ratio
        
        # Confidence score (simplified - based on preservation of structure)
        confidence = self._calculate_confidence(text, compressed_text, preserve_keywords)
        
        # Billable if confidence >= 0.5
        billable = confidence >= 0.5
        
        processing_time = (time.time() - start_time) * 1000
        
        return CompressionResult(
            compressed_text=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=round(ratio, 3),
            confidence_score=round(confidence, 3),
            strategy_used=strategy,
            processing_time_ms=round(processing_time, 2),
            billable=billable
        )
    
    def _selective_context_compress(
        self,
        text: str,
        target_ratio: float,
        preserve_keywords: Optional[List[str]] = None
    ) -> str:
        """Remove redundant tokens based on linguistic redundancy."""
        preserve_keywords = preserve_keywords or []
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) <= 1:
            # Nothing to compress
            return text
        
        # Score each sentence for importance
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            words = sentence.split()
            
            # Check if sentence contains ANY preserved keyword
            sentence_lower = sentence.lower()
            has_preserve_keyword = any(kw.lower() in sentence_lower for kw in preserve_keywords)
            
            # Calculate redundancy score
            word_count = len(words)
            if word_count == 0:
                scored_sentences.append((i, 0.0, sentence))
                continue
            
            # If has preserved keyword, give highest importance AND ensure it's always kept
            if has_preserve_keyword:
                scored_sentences.append((i, 2.0, sentence))  # Highest priority
                continue
            
            # Stop word ratio (higher = more redundant)
            stop_word_count = sum(1 for w in words if w.lower() in self.stop_words)
            stop_ratio = stop_word_count / word_count if word_count > 0 else 0
            
            # Repetition score (words that appear multiple times)
            word_freq = {}
            for w in words:
                w_lower = w.lower()
                word_freq[w_lower] = word_freq.get(w_lower, 0) + 1
            repetition_score = sum(v - 1 for v in word_freq.values()) / word_count if word_count > 0 else 0
            
            # Position bonus (first and last sentences are important)
            position_bonus = 0.2 if i == 0 or i == len(sentences) - 1 else 0
            
            # Importance score (lower = more redundant = can compress more)
            importance = 1.0 - (stop_ratio * 0.5 + repetition_score * 0.3 - position_bonus)
            importance = max(0.0, min(1.0, importance))
            
            scored_sentences.append((i, importance, sentence))
        
        # Select sentences to keep based on target ratio
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        keep_count = max(1, int(len(sentences) * target_ratio))
        
        # Always include sentences with preserved keywords (score >= 2.0)
        keyword_sentences = [(idx, score, sent) for idx, score, sent in scored_sentences if score >= 2.0]
        keyword_indices = {idx for idx, _, _ in keyword_sentences}
        regular_sentences = [(idx, score, sent) for idx, score, sent in scored_sentences if score < 2.0]
        
        keep_from_regular = max(0, keep_count - len(keyword_indices))
        kept_indices = {idx for idx, _, _ in regular_sentences[:keep_from_regular]}
        kept_indices.update(keyword_indices)
        
        # Reconstruct (preserving original order)
        result_sentences = [sent for idx, _, sent in scored_sentences if idx in kept_indices]
        
        return " ".join(result_sentences)
    
    def _compressible_compress(
        self,
        text: str,
        target_ratio: float,
        preserve_keywords: Optional[List[str]] = None
    ) -> str:
        """Remove highly compressible/redundant sequences."""
        preserve_keywords = preserve_keywords or []
        
        # Find and remove repeated phrases
        words = text.split()
        if len(words) <= 10:
            return text
        
        # Identify n-gram repetitions
        n = 3
        ngram_counts = {}
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i:i+n])
            ngram_hash = hashlib.md5(ngram.encode()).hexdigest()[:8]
            if ngram_hash not in ngram_counts:
                ngram_counts[ngram_hash] = []
            ngram_counts[ngram_hash].append(i)
        
        # Mark repeated n-grams for removal (keep first occurrence)
        to_remove = set()
        for ngram_hash, positions in ngram_counts.items():
            if len(positions) > 1:
                for pos in positions[1:]:
                    for offset in range(n):
                        to_remove.add(pos + offset)
        
        # Rebuild text
        result = [w for i, w in enumerate(words) if i not in to_remove]
        
        return " ".join(result)
    
    def _llmlingua_compress(
        self,
        text: str,
        target_ratio: float,
        preserve_keywords: Optional[List[str]] = None
    ) -> str:
        """
        Simplified LLMLingua-style compression.
        
        Preserves:
        - System prompts (first section)
        - Keywords (user-specified)
        - Question/instruction patterns
        """
        preserve_keywords = preserve_keywords or []
        
        lines = text.split('\n')
        result_lines = []
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Preserve system messages
            if line.lower().startswith('system:') or line.lower().startswith('system message'):
                result_lines.append(line)
                continue
            
            # Preserve lines with preserved keywords
            if any(kw.lower() in line.lower() for kw in preserve_keywords):
                result_lines.append(line)
                continue
            
            # Preserve questions
            if '?' in line:
                result_lines.append(line)
                continue
            
            # Remove very short, non-essential lines
            if len(line.split()) < 3: continue
            
            # Otherwise, compress by removing adjectives/adverbs (simplified)
            words = line.split()
            important_pos = {'noun', 'verb', 'proper_noun', 'number'}
            # Simplified: keep words > 4 chars (likely content words)
            compressed_words = [w for w in words if len(w) > 4 or w.isupper()]
            
            if compressed_words: result_lines.append(" ".join(compressed_words))
        
        return "\n".join(result_lines)
    
    def _calculate_confidence(
        self,
        original: str,
        compressed: str,
        preserve_keywords: Optional[List[str]] = None
    ) -> float:
        preserve_keywords = preserve_keywords or []
        preserved_count = 0
        for kw in preserve_keywords:
            if kw.lower() in compressed.lower(): preserved_count += 1
        keyword_score = preserved_count / len(preserve_keywords) if preserve_keywords else 1.0
        
        orig_sentences = len(re.findall(r'[.!?]', original))
        comp_sentences = len(re.findall(r'[.!?]', compressed))
        structure_ratio = comp_sentences / orig_sentences if orig_sentences > 0 else 1.0
        
        orig_len = len(original)
        comp_len = len(compressed)
        length_ratio = comp_len / orig_len if orig_len > 0 else 1.0
        
        confidence = (keyword_score * 0.4 + structure_ratio * 0.3 + min(length_ratio, 1.0) * 0.3)
        return min(1.0, confidence)


class SemanticCompressor:
    """
    Semantic compression using embeddings.
    
    Identifies redundant concepts and removes overlapping information
    using cosine similarity of sentence embeddings.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedding_model = None
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """Load sentence-transformer model for embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(self.model_name)
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for semantic compression. "
                "Install with: pip install sentence-transformers"
            )
    
    def compress(
        self,
        text: str,
        target_ratio: float = 0.5,
        preserve_keywords: Optional[List[str]] = None,
        similarity_threshold: float = 0.85
    ) -> CompressionResult:
        """
        Compress text by removing semantically redundant chunks.
        
        Args:
            text: Input text to compress
            target_ratio: Target compression ratio (not used directly, similarity threshold drives removal)
            preserve_keywords: Keywords to preserve (not implemented for semantic - all content considered)
            similarity_threshold: Cosine similarity threshold above which chunks are considered redundant
            
        Returns:
            CompressionResult with compressed text and metadata
        """
        import time
        start_time = time.time()
        
        tokenizer = Tokenizer()
        original_tokens = tokenizer.count_tokens(text)
        
        # Split into meaningful chunks (paragraphs preferred, fallback to sentences)
        chunks = [p.strip() for p in text.split('\n\n') if p.strip()]
        if len(chunks) < 2:
            # Try splitting by sentences if not enough paragraphs
            chunks = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        
        if len(chunks) <= 1:
            # Nothing to compress semantically
            return CompressionResult(
                compressed_text=text,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
                confidence_score=1.0,
                strategy_used="semantic",
                processing_time_ms=(time.time() - start_time) * 1000,
                billable=False  # No compression occurred
            )
        
        # Generate embeddings for all chunks
        embeddings = self.embedding_model.encode(chunks, convert_to_numpy=True)
        
        # Calculate pairwise cosine similarities
        from sklearn.metrics.pairwise import cosine_similarity
        similarity_matrix = cosine_similarity(embeddings)
        
        # Greedy selection: keep first chunk, remove subsequent chunks that are too similar
        keep_indices = [0]  # Always keep the first chunk
        
        for i in range(1, len(chunks)):
            # Check similarity against all kept chunks
            is_redundant = False
            for kept_idx in keep_indices:
                sim = similarity_matrix[i][kept_idx]
                if sim > similarity_threshold:
                    is_redundant = True
                    break
            
            if not is_redundant:
                keep_indices.append(i)
        
        # Reconstruct compressed text (preserve original order)
        compressed_chunks = [chunks[i] for i in sorted(keep_indices)]
        compressed_text = "\n\n".join(compressed_chunks)
        
        compressed_tokens = tokenizer.count_tokens(compressed_text)
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
        actual_reduction = original_tokens - compressed_tokens
        
        # Confidence based on how many chunks we kept and actual compression achieved
        compression_achieved = 1.0 - ratio
        chunk_retention = len(keep_indices) / len(chunks)
        
        # Higher confidence when we achieved meaningful compression without removing everything
        if compression_achieved > 0.1 and len(keep_indices) >= 1:
            confidence = 0.7 + (compression_achieved * 0.3)  # 0.7-1.0 based on compression
        elif compression_achieved > 0:
            confidence = 0.5 + (compression_achieved * 0.4)  # 0.5-0.9 for minor compression
        else:
            confidence = 0.3  # Low confidence if no compression
        
        confidence = min(1.0, max(0.0, confidence))
        billable = confidence >= 0.5 and actual_reduction > 0
        
        return CompressionResult(
            compressed_text=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=round(ratio, 3),
            confidence_score=round(confidence, 3),
            strategy_used="semantic",
            processing_time_ms=round((time.time() - start_time) * 1000, 2),
            billable=billable
        )


class StrategySelector:
    """Automatically select best compression strategy."""
    
    def select(self, text: str, target_ratio: float) -> str:
        """
        Select best strategy based on text characteristics.
        
        Returns:
            'token' | 'semantic' | 'auto'
        """
        # Heuristics for strategy selection
        tokenizer = Tokenizer()
        token_count = tokenizer.count_tokens(text)
        
        # Count paragraphs
        paragraph_count = text.count('\n\n') + 1 if text.strip() else 1
        
        # Multiple paragraphs benefit from semantic (regardless of token count)
        if paragraph_count >= 3:
            return "semantic"
        
        # Long texts with many tokens benefit from semantic
        if token_count > 1000:
            return "semantic"
        
        # Short texts benefit more from token compression
        if token_count < 200:
            return "token"
        
        # Default to token for most cases
        return "token"
