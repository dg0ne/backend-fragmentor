"""
코드 임베딩 생성 패키지
"""

__version__ = "0.2.0"

# 주요 클래스들을 패키지 레벨에서 쉽게 접근할 수 있도록 노출
from app.embedding.base import EmbeddingGenerator, ContextEnhancer, CacheManager
from app.embedding.embedder import CodeEmbedder
from app.embedding.cache_manager import FileSystemCacheManager, MemoryCacheManager
from app.embedding.context_enhancer import CodeContextEnhancer

# 사용 예시:
# from app.embedding import CodeEmbedder, FileSystemCacheManager