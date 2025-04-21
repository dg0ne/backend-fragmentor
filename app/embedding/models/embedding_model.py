"""
임베딩 모델 추상화 클래스
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

class EmbeddingModel(ABC):
    """
    임베딩 모델 추상화 클래스
    다양한 임베딩 모델을 위한 통일된 인터페이스 제공
    """
    
    @abstractmethod
    def encode(self, text: str) -> np.ndarray:
        """
        단일 텍스트 인코딩
        
        Args:
            text: 인코딩할 텍스트
            
        Returns:
            np.ndarray: 임베딩 벡터
        """
        pass
    
    @abstractmethod
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        여러 텍스트 배치 인코딩
        
        Args:
            texts: 인코딩할 텍스트 목록
            batch_size: 배치 크기
            
        Returns:
            List[np.ndarray]: 인코딩된 임베딩 벡터 목록
        """
        pass
    
    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """
        임베딩 벡터 차원 수
        
        Returns:
            int: 벡터 차원 수
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        모델 이름
        
        Returns:
            str: 모델 이름
        """
        pass
    
    @abstractmethod
    def max_sequence_length(self) -> int:
        """
        모델이 처리할 수 있는 최대 시퀀스 길이
        
        Returns:
            int: 최대 시퀀스 길이
        """
        pass
    
    @abstractmethod
    def preprocess_text(self, text: str) -> str:
        """
        모델 입력을 위한 텍스트 전처리
        
        Args:
            text: 원본 텍스트
            
        Returns:
            str: 전처리된 텍스트
        """
        pass