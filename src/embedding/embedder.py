"""
코드 임베딩(Embedding) 생성 모듈
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Union, Optional
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

class CodeEmbedder:
    """
    코드 조각을 SentenceTransformer를 이용해 벡터로 변환
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', cache_dir: Optional[str] = None):
        """
        Args:
            model_name: SentenceTransformer 모델 이름
            cache_dir: 임베딩 캐싱 디렉토리 (None인 경우 캐싱 비활성화)
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.vector_dim = self.model.get_sentence_embedding_dimension()
        self.cache_dir = cache_dir
        
        # 캐시 디렉토리 생성
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def embed_fragment(self, fragment: Dict[str, Any]) -> np.ndarray:
        """
        단일 코드 파편 임베딩
        
        Args:
            fragment: 코드 파편 객체
            
        Returns:
            np.ndarray: 임베딩 벡터
        """
        # 캐시 확인
        if self.cache_dir:
            cache_path = os.path.join(self.cache_dir, f"{fragment['id']}.pkl")
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
        
        # 임베딩 생성을 위한 텍스트 구성
        embedding_text = self._prepare_embedding_text(fragment)
        
        # 임베딩 생성
        embedding = self.model.encode(embedding_text)
        
        # 캐시 저장
        if self.cache_dir:
            with open(cache_path, 'wb') as f:
                pickle.dump(embedding, f)
        
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
        
        # 캐시 확인 및 임베딩 필요한 파편 확인
        for fragment in fragments:
            fragment_id = fragment['id']
            
            # 캐시 확인
            if self.cache_dir:
                cache_path = os.path.join(self.cache_dir, f"{fragment_id}.pkl")
                if os.path.exists(cache_path):
                    with open(cache_path, 'rb') as f:
                        embeddings[fragment_id] = pickle.load(f)
                        continue
            
            # 임베딩 필요한 파편 추가
            embedding_text = self._prepare_embedding_text(fragment)
            texts_to_embed.append(embedding_text)
            ids_to_embed.append(fragment_id)
        
        # 임베딩이 필요한 것이 있을 경우만 처리
        if texts_to_embed:
            # 배치 처리
            for i in tqdm(range(0, len(texts_to_embed), batch_size)):
                batch_texts = texts_to_embed[i:i+batch_size]
                batch_ids = ids_to_embed[i:i+batch_size]
                
                # 배치 임베딩 생성
                batch_embeddings = self.model.encode(batch_texts)
                
                # 결과 저장 및 캐싱
                for j, fragment_id in enumerate(batch_ids):
                    embeddings[fragment_id] = batch_embeddings[j]
                    
                    # 캐시 저장
                    if self.cache_dir:
                        cache_path = os.path.join(self.cache_dir, f"{fragment_id}.pkl")
                        with open(cache_path, 'wb') as f:
                            pickle.dump(batch_embeddings[j], f)
        
        return embeddings
    
    def _prepare_embedding_text(self, fragment: Dict[str, Any]) -> str:
        """
        임베딩을 위한 텍스트 준비
        파편 유형과 메타데이터를 포함하여 컨텍스트 풍부한 임베딩 생성
        
        Args:
            fragment: 코드 파편
            
        Returns:
            str: 임베딩을 위한 텍스트
        """
        content = fragment['content']
        frag_type = fragment['type']
        name = fragment['name']
        
        # 파편 타입별 텍스트 구성
        prefix = ""
        if frag_type == 'component':
            comp_type = fragment['metadata'].get('component_type', 'unknown')
            prefix = f"React {comp_type} component {name}: "
        elif frag_type == 'function':
            prefix = f"Function {name}: "
        elif frag_type == 'jsx_element':
            prefix = f"JSX element {name}: "
        elif frag_type == 'import_block':
            prefix = "Import statements: "
        elif frag_type == 'style_block':
            prefix = f"Style definitions {name}: "
        elif frag_type == 'hook':
            prefix = f"React hook {name}: "
        
        # 최대 텍스트 길이 제한 (모델 한계 고려)
        max_length = 512 - len(prefix)
        if len(content) > max_length:
            content = content[:max_length]
        
        return prefix + content