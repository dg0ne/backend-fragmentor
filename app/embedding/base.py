"""
코드 임베딩 생성을 위한 기본 인터페이스 및 추상 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import numpy as np

class EmbeddingGenerator(ABC):
    """
    코드 임베딩 생성을 위한 기본 인터페이스
    모든 임베딩 생성기는 이 클래스를 상속해야 함
    """
    
    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            np.ndarray: 임베딩 벡터
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        여러 텍스트를 배치로 임베딩
        
        Args:
            texts: 임베딩할 텍스트 목록
            
        Returns:
            List[np.ndarray]: 임베딩 벡터 목록
        """
        pass
    
    @property
    @abstractmethod
    def vector_dim(self) -> int:
        """
        임베딩 벡터의 차원 수
        
        Returns:
            int: 벡터 차원 수
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        모델 이름
        
        Returns:
            str: 모델 이름
        """
        pass

class ContextEnhancer(ABC):
    """
    코드 임베딩을 위한 컨텍스트 향상 인터페이스
    코드 파편의 의미 정보를 풍부하게 하기 위한 컨텍스트 추가
    """
    
    @abstractmethod
    def enhance(self, fragment: Dict[str, Any]) -> str:
        """
        코드 파편에 컨텍스트 정보를 추가하여 향상된 텍스트 생성
        
        Args:
            fragment: 코드 파편
            
        Returns:
            str: 컨텍스트가 향상된 텍스트
        """
        pass

class CacheManager(ABC):
    """
    임베딩 캐싱 관리를 위한 인터페이스
    """
    
    @abstractmethod
    def get(self, cache_key: str) -> Optional[np.ndarray]:
        """
        캐시에서 임베딩 가져오기
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            Optional[np.ndarray]: 캐시된 임베딩 벡터 또는 None
        """
        pass
    
    @abstractmethod
    def save(self, cache_key: str, embedding: np.ndarray) -> None:
        """
        임베딩을 캐시에 저장
        
        Args:
            cache_key: 캐시 키
            embedding: 저장할 임베딩 벡터
        """
        pass
    
    @abstractmethod
    def contains(self, cache_key: str) -> bool:
        """
        캐시에 키가 존재하는지 확인
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            bool: 존재 여부
        """
        pass