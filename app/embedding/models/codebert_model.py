"""
CodeBERT 모델 구현
"""

import numpy as np
from typing import List, Optional
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

from app.embedding.models.embedding_model import EmbeddingModel

class CodeBERTModel(EmbeddingModel):
    """
    CodeBERT 기반 임베딩 모델 구현
    SentenceTransformer를 사용하여 코드 임베딩 생성
    """
    
    def __init__(self, model_name: str = 'microsoft/codebert-base'):
        """
        Args:
            model_name: SentenceTransformer 모델 이름
        """
        self._model_name = model_name
        self._model = SentenceTransformer(model_name)
        self._embedding_dim = self._model.get_sentence_embedding_dimension()
        self._max_seq_length = 512  # CodeBERT 기본 최대 시퀀스 길이
    
    def encode(self, text: str) -> np.ndarray:
        """
        단일 텍스트 인코딩
        
        Args:
            text: 인코딩할 텍스트
            
        Returns:
            np.ndarray: 임베딩 벡터
        """
        preprocessed_text = self.preprocess_text(text)
        return self._model.encode(preprocessed_text)
    
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        여러 텍스트 배치 인코딩
        
        Args:
            texts: 인코딩할 텍스트 목록
            batch_size: 배치 크기
            
        Returns:
            List[np.ndarray]: 인코딩된 임베딩 벡터 목록
        """
        # 텍스트 전처리
        preprocessed_texts = [self.preprocess_text(text) for text in texts]
        
        # 배치 처리
        embeddings = []
        for i in tqdm(range(0, len(preprocessed_texts), batch_size), desc="인코딩 중"):
            batch_texts = preprocessed_texts[i:i+batch_size]
            batch_embeddings = self._model.encode(batch_texts)
            
            # 단일 임베딩이 반환된 경우 (배치 크기 1)
            if len(batch_texts) == 1 and batch_embeddings.ndim == 1:
                embeddings.append(batch_embeddings)
            else:
                # 여러 임베딩이 2D 배열로 반환된 경우
                embeddings.extend([emb for emb in batch_embeddings])
        
        return embeddings
    
    @property
    def embedding_dim(self) -> int:
        """
        임베딩 벡터 차원 수
        
        Returns:
            int: 벡터 차원 수
        """
        return self._embedding_dim
    
    @property
    def name(self) -> str:
        """
        모델 이름
        
        Returns:
            str: 모델 이름
        """
        return self._model_name
    
    def max_sequence_length(self) -> int:
        """
        모델이 처리할 수 있는 최대 시퀀스 길이
        
        Returns:
            int: 최대 시퀀스 길이
        """
        return self._max_seq_length
    
    def preprocess_text(self, text: str) -> str:
        """
        모델 입력을 위한 텍스트 전처리
        
        Args:
            text: 원본 텍스트
            
        Returns:
            str: 전처리된 텍스트
        """
        # 텍스트 길이 제한
        if len(text) > self._max_seq_length * 4:  # 문자 기준 대략적인 토큰 수 추정
            # 앞부분과 뒷부분을 유지하고 중간 부분 생략
            max_half_length = (self._max_seq_length * 4) // 2
            text = text[:max_half_length] + "..." + text[-max_half_length:]
        
        # 특수 문자 처리 (필요시)
        # CodeBERT는 대부분의 코드 특수 문자를 잘 처리하므로 최소한의 전처리만 수행
        
        return text