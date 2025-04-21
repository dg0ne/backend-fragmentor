"""
임베딩 캐싱 관리 모듈
"""

import os
import pickle
import numpy as np
from typing import Dict, Optional, List

from app.embedding.base import CacheManager

class FileSystemCacheManager(CacheManager):
    """
    파일 시스템 기반 임베딩 캐시 관리자
    """
    
    def __init__(self, cache_dir: str):
        """
        Args:
            cache_dir: 캐시 디렉토리 경로
        """
        self.cache_dir = cache_dir
        
        # 캐시 디렉토리 생성
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get(self, cache_key: str) -> Optional[np.ndarray]:
        """
        캐시에서 임베딩 가져오기
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            Optional[np.ndarray]: 캐시된 임베딩 벡터 또는 None
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"캐시 로드 오류: {str(e)}")
                return None
        
        return None
    
    def save(self, cache_key: str, embedding: np.ndarray) -> None:
        """
        임베딩을 캐시에 저장
        
        Args:
            cache_key: 캐시 키
            embedding: 저장할 임베딩 벡터
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            print(f"캐시 저장 오류: {str(e)}")
    
    def contains(self, cache_key: str) -> bool:
        """
        캐시에 키가 존재하는지 확인
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            bool: 존재 여부
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        return os.path.exists(cache_path)
    
    def clear(self) -> None:
        """
        모든 캐시 삭제
        """
        for file_name in os.listdir(self.cache_dir):
            if file_name.endswith('.pkl'):
                file_path = os.path.join(self.cache_dir, file_name)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"캐시 파일 삭제 오류: {str(e)}")
    
    def get_stats(self) -> Dict[str, int]:
        """
        캐시 통계 정보
        
        Returns:
            Dict[str, int]: 통계 정보
        """
        files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
        
        total_size = 0
        for file_name in files:
            file_path = os.path.join(self.cache_dir, file_name)
            total_size += os.path.getsize(file_path)
        
        return {
            'cache_count': len(files),
            'cache_size_bytes': total_size,
            'cache_size_mb': total_size / (1024 * 1024)
        }
    
    def get_multi(self, cache_keys: List[str]) -> Dict[str, np.ndarray]:
        """
        여러 키에 대한 임베딩 가져오기
        
        Args:
            cache_keys: 캐시 키 목록
            
        Returns:
            Dict[str, np.ndarray]: 키와 임베딩 벡터 매핑
        """
        result = {}
        for key in cache_keys:
            embedding = self.get(key)
            if embedding is not None:
                result[key] = embedding
        
        return result

class MemoryCacheManager(CacheManager):
    """
    메모리 기반 임베딩 캐시 관리자
    """
    
    def __init__(self, max_items: int = 1000):
        """
        Args:
            max_items: 최대 캐시 항목 수
        """
        self.cache = {}
        self.max_items = max_items
    
    def get(self, cache_key: str) -> Optional[np.ndarray]:
        """
        캐시에서 임베딩 가져오기
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            Optional[np.ndarray]: 캐시된 임베딩 벡터 또는 None
        """
        return self.cache.get(cache_key)
    
    def save(self, cache_key: str, embedding: np.ndarray) -> None:
        """
        임베딩을 캐시에 저장
        
        Args:
            cache_key: 캐시 키
            embedding: 저장할 임베딩 벡터
        """
        # 캐시 크기 제한
        if len(self.cache) >= self.max_items and cache_key not in self.cache:
            # LRU 정책을 적용하려면 여기서 가장 오래된 항목 제거
            # 간단한 구현으로 무작위로 하나 제거
            self.cache.pop(next(iter(self.cache)))
        
        self.cache[cache_key] = embedding
    
    def contains(self, cache_key: str) -> bool:
        """
        캐시에 키가 존재하는지 확인
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            bool: 존재 여부
        """
        return cache_key in self.cache
    
    def clear(self) -> None:
        """
        모든 캐시 삭제
        """
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """
        캐시 통계 정보
        
        Returns:
            Dict[str, int]: 통계 정보
        """
        return {
            'cache_count': len(self.cache),
            'max_items': self.max_items
        }
    
    def get_multi(self, cache_keys: List[str]) -> Dict[str, np.ndarray]:
        """
        여러 키에 대한 임베딩 가져오기
        
        Args:
            cache_keys: 캐시 키 목록
            
        Returns:
            Dict[str, np.ndarray]: 키와 임베딩 벡터 매핑
        """
        return {k: self.cache[k] for k in cache_keys if k in self.cache}