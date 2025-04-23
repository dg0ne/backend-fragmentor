"""
코드 임베딩 생성 모듈
"""

import os
import pickle
import numpy as np
from typing import Dict, List, Any, Optional
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

class CodeEmbedder:
    """
    코드 조각을 벡터로 변환하는 임베딩 생성기
    """
    
    def __init__(self, model_name: str = 'jhgan/ko-sroberta-multitask', 
                normalize_embeddings: bool = True, 
                cache_dir: Optional[str] = None):        
        """
        Args:
            model_name: SentenceTransformer 모델 이름
            cache_dir: 임베딩 캐싱 디렉토리
        """
        self._model_name = model_name
        
        # 모델 초기화
        self.model = SentenceTransformer(model_name, trust_remote_code=True)
        self._vector_dim = self.model.get_sentence_embedding_dimension()
        
        # 캐시 디렉토리 설정
        self.cache_dir = cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
    
    @property
    def vector_dim(self) -> int:
        """임베딩 벡터의 차원 수"""
        return self._vector_dim
    
    @property
    def model_name(self) -> str:
        """모델 이름"""
        return self._model_name
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            np.ndarray: 임베딩 벡터
        """
        return self.model.encode(text, normalize_embeddings=self.normalize_embeddings)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        여러 텍스트를 배치로 임베딩
        
        Args:
            texts: 임베딩할 텍스트 목록
            batch_size: 배치 크기
            
        Returns:
            List[np.ndarray]: 임베딩 벡터 목록
        """
        return self.model.encode(texts, batch_size=batch_size)
    
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
        cached_vector = self._get_from_cache(fragment_id)
        if cached_vector is not None:
            return cached_vector
        
        # 임베딩 생성을 위한 텍스트 구성
        embedding_text = self._create_embedding_text(fragment)
        
        # 임베딩 생성
        embedding = self.model.encode(embedding_text)
        
        # 캐시 저장
        self._save_to_cache(fragment_id, embedding)
        
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
            cached_vector = self._get_from_cache(fragment_id)
            if cached_vector is not None:
                embeddings[fragment_id] = cached_vector
                continue
            
            # 임베딩 필요한 파편 추가
            embedding_text = self._create_embedding_text(fragment)
            texts_to_embed.append(embedding_text)
            ids_to_embed.append(fragment_id)
        
        # 2. 임베딩이 필요한 것이 있을 경우만 처리
        if texts_to_embed:
            # 배치 처리
            batch_count = (len(texts_to_embed) + batch_size - 1) // batch_size
            for i in tqdm(range(0, len(texts_to_embed), batch_size), total=batch_count):
                batch_texts = texts_to_embed[i:i+batch_size]
                batch_embeddings = self.model.encode(batch_texts)
                
                # 단일 임베딩이 반환된 경우 (배치 크기 1)
                if len(batch_texts) == 1 and batch_embeddings.ndim == 1:
                    embeddings[ids_to_embed[i]] = batch_embeddings
                else:
                    # 여러 임베딩이 2D 배열로 반환된 경우
                    for j, embedding in enumerate(batch_embeddings):
                        fragment_id = ids_to_embed[i+j]
                        embeddings[fragment_id] = embedding
                        
                        # 캐시 저장
                        self._save_to_cache(fragment_id, embedding)
        
        return embeddings
    
    def _create_embedding_text(self, fragment: Dict[str, Any]) -> str:
        """
        파편 정보를 임베딩 텍스트로 변환
        
        Args:
            fragment: 코드 파편
            
        Returns:
            str: 임베딩을 위한 강화된 텍스트
        """
        # 기본 정보 추출
        content = fragment['content']
        fragment_type = fragment['type']
        name = fragment['name']
        metadata = fragment.get('metadata', {})
        
        # 컨텍스트 정보 추가
        context_parts = []
        
        # 파편 타입별 접두사 추가
        if fragment_type == 'component':
            context_parts.append(f"Vue 컴포넌트: {name}")
            
            # 컴포넌트 정보 추가
            props = metadata.get('props', [])
            if props:
                context_parts.append(f"Props: {', '.join(props)}")
                
            components = metadata.get('components', [])
            if components:
                context_parts.append(f"Components: {', '.join(components)}")
                
        elif fragment_type == 'template':
            context_parts.append(f"템플릿 섹션: {metadata.get('component_name', name)}")
            
        elif fragment_type == 'script':
            context_parts.append(f"스크립트 섹션: {metadata.get('component_name', name)}")
            
        elif fragment_type == 'style':
            context_parts.append(f"스타일 섹션: {metadata.get('component_name', name)}")
        
        # 파일 정보 추가
        if 'file_name' in metadata:
            context_parts.append(f"파일: {metadata['file_name']}")
        
        # 컨텍스트 결합
        context = " | ".join(context_parts)
        
        # 최종 텍스트 구성 (컨텍스트 + 내용)
        embedding_text = f"{context}\n\n{content}"
        
        return embedding_text
    
    def _get_from_cache(self, fragment_id: str) -> Optional[np.ndarray]:
        """캐시에서 임베딩 벡터 가져오기"""
        if not self.cache_dir:
            return None
            
        cache_path = os.path.join(self.cache_dir, f"{fragment_id}.pkl")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"캐시 로드 오류: {str(e)}")
                return None
        
        return None
    
    def _save_to_cache(self, fragment_id: str, embedding: np.ndarray) -> None:
        """임베딩 벡터를 캐시에 저장"""
        if not self.cache_dir:
            return
            
        cache_path = os.path.join(self.cache_dir, f"{fragment_id}.pkl")
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            print(f"캐시 저장 오류: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        if not self.cache_dir:
            return {"cache_enabled": False}
            
        stats = {
            "cache_enabled": True,
            "cache_dir": self.cache_dir
        }
        
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
            stats["cache_count"] = len(cache_files)
            
            total_size = 0
            for file_name in cache_files:
                file_path = os.path.join(self.cache_dir, file_name)
                total_size += os.path.getsize(file_path)
                
            stats["cache_size_bytes"] = total_size
            stats["cache_size_mb"] = total_size / (1024 * 1024)
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    def clear_cache(self) -> None:
        """캐시 초기화"""
        if not self.cache_dir:
            return
            
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
            for file_name in cache_files:
                file_path = os.path.join(self.cache_dir, file_name)
                os.remove(file_path)
            print(f"캐시가 성공적으로 초기화되었습니다. (삭제된 파일: {len(cache_files)}개)")
        except Exception as e:
            print(f"캐시 초기화 오류: {str(e)}")