"""
향상된 코드 임베딩(Embedding) 생성 모듈 - lifesub-web 프로젝트용
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional
from tqdm import tqdm

from app.embedding.base import EmbeddingGenerator
from app.embedding.cache_manager import FileSystemCacheManager
from app.embedding.context_enhancer import CodeContextEnhancer
from app.embedding.models.codebert_model import CodeBERTModel

class CodeEmbedder(EmbeddingGenerator):
    """
    lifesub-web 코드 조각을 SentenceTransformer를 이용해 벡터로 변환
    """
    
    def __init__(self, model_name: str = 'microsoft/codebert-base', cache_dir: Optional[str] = None):
        """
        Args:
            model_name: SentenceTransformer 모델 이름
            cache_dir: 임베딩 캐싱 디렉토리 (None인 경우 캐싱 비활성화)
        """
        self._model_name = model_name
        
        # 모델 초기화
        self.model = CodeBERTModel(model_name)
        self._vector_dim = self.model.embedding_dim
        
        # 캐시 관리자 초기화
        self.cache_dir = cache_dir
        self.cache_manager = None
        
        if cache_dir:
            self.cache_manager = FileSystemCacheManager(cache_dir)
        
        # 컨텍스트 향상기 초기화
        self.context_enhancer = CodeContextEnhancer()
    
    @property
    def vector_dim(self) -> int:
        """
        임베딩 벡터의 차원 수
        
        Returns:
            int: 벡터 차원 수
        """
        return self._vector_dim
    
    @property
    def model_name(self) -> str:
        """
        모델 이름
        
        Returns:
            str: 모델 이름
        """
        return self._model_name
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            np.ndarray: 임베딩 벡터
        """
        return self.model.encode(text)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        여러 텍스트를 배치로 임베딩
        
        Args:
            texts: 임베딩할 텍스트 목록
            batch_size: 배치 크기
            
        Returns:
            List[np.ndarray]: 임베딩 벡터 목록
        """
        return self.model.encode_batch(texts, batch_size)
    
    def embed_fragment(self, fragment: Dict[str, Any]) -> np.ndarray:
        """
        단일 코드 파편 임베딩
        
        Args:
            fragment: 코드 파편 객체
            
        Returns:
            np.ndarray: 임베딩 벡터
        """
        # 캐시 확인
        fragment_id = fragment['id']
        if self.cache_manager and self.cache_manager.contains(fragment_id):
            cached_embedding = self.cache_manager.get(fragment_id)
            if cached_embedding is not None:
                return cached_embedding
        
        # 임베딩 생성을 위한 텍스트 구성
        embedding_text = self.context_enhancer.enhance(fragment)
        
        # 임베딩 생성
        embedding = self.model.encode(embedding_text)
        
        # 캐시 저장
        if self.cache_manager:
            self.cache_manager.save(fragment_id, embedding)
        
        return embedding
    
    def embed_fragments(self, fragments: List[Dict[str, Any]], batch_size: int = 32) -> Dict[str, np.ndarray]:
        """
        다수의 코드 파편 임베딩 (배치 처리)
        
        Args:
            fragments: 코드 파편 목록
            batch_size: 배치 크기
            
        Returns:
            Dict[str, np.ndarray]: fragment_id를 키로, 임베딩 벡터를 값으로 하는 딕셔너리
        """
        embeddings = {}
        texts_to_embed = []
        ids_to_embed = []
        
        print(f"총 {len(fragments)}개 파편 임베딩 생성 중...")
        
        # 1. 캐시 확인 및 임베딩 필요한 파편 확인
        for fragment in fragments:
            fragment_id = fragment['id']
            
            # 캐시 확인
            if self.cache_manager and self.cache_manager.contains(fragment_id):
                cached_embedding = self.cache_manager.get(fragment_id)
                if cached_embedding is not None:
                    embeddings[fragment_id] = cached_embedding
                    continue
            
            # 임베딩 필요한 파편 추가
            embedding_text = self.context_enhancer.enhance(fragment)
            texts_to_embed.append(embedding_text)
            ids_to_embed.append(fragment_id)
        
        # 2. 임베딩이 필요한 것이 있을 경우만 처리
        if texts_to_embed:
            # 배치 처리
            batch_embeddings = []
            for i in tqdm(range(0, len(texts_to_embed), batch_size), desc="임베딩 생성"):
                batch_texts = texts_to_embed[i:i+batch_size]
                current_batch_embeddings = self.model.encode_batch(batch_texts)
                batch_embeddings.extend(current_batch_embeddings)
            
            # 결과 저장 및 캐싱
            for i, fragment_id in enumerate(ids_to_embed):
                embeddings[fragment_id] = batch_embeddings[i]
                
                # 캐시 저장
                if self.cache_manager:
                    self.cache_manager.save(fragment_id, batch_embeddings[i])
        
        return embeddings
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 정보 반환
        
        Returns:
            Dict[str, Any]: 캐시 통계 정보
        """
        if not self.cache_manager:
            return {"cache_enabled": False}
            
        stats = self.cache_manager.get_stats()
        stats["cache_enabled"] = True
        return stats
    
    def clear_cache(self) -> None:
        """
        캐시 초기화
        """
        if self.cache_manager:
            self.cache_manager.clear()
            print("임베딩 캐시가 초기화되었습니다.")
            
    def get_similar_texts(self, query_text: str, texts: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        쿼리 텍스트와 가장 유사한 텍스트 찾기
        
        Args:
            query_text: 쿼리 텍스트
            texts: 비교할 텍스트 목록
            top_k: 반환할 결과 수
            
        Returns:
            List[Dict[str, Any]]: 유사한 텍스트 정보 목록
        """
        # 쿼리 임베딩 생성
        query_embedding = self.embed_text(query_text)
        
        # 모든 텍스트 임베딩 생성
        embeddings = self.embed_batch(texts)
        
        # 유사도 계산 및 정렬
        similarities = []
        for i, embedding in enumerate(embeddings):
            # 코사인 유사도 계산
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            similarities.append({
                "index": i,
                "text": texts[i],
                "similarity": float(similarity)
            })
        
        # 유사도 기준 내림차순 정렬
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        # 상위 K개 결과 반환
        return similarities[:top_k]