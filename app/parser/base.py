"""
코드 파싱을 위한 기본 인터페이스 및 추상 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple

class CodeParser(ABC):
    """
    코드 파싱을 위한 기본 인터페이스
    모든 언어별 파서는 이 클래스를 상속해야 함
    """
    
    @abstractmethod
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        단일 파일 파싱
        
        Args:
            file_path: 파싱할 파일 경로
            
        Returns:
            Dict[str, Any]: 파싱 결과
        """
        pass
    
    @abstractmethod
    def parse_code(self, code: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        코드 문자열 파싱
        
        Args:
            code: 파싱할 코드 문자열
            file_info: 파일 메타데이터
            
        Returns:
            Dict[str, Any]: 파싱 결과
        """
        pass
    
    @abstractmethod
    def parse_project(self, project_path: str, extensions: List[str] = None) -> Dict[str, Any]:
        """
        프로젝트 전체 파싱
        
        Args:
            project_path: 프로젝트 경로
            extensions: 처리할 파일 확장자 목록
            
        Returns:
            Dict[str, Any]: 프로젝트 파싱 결과
        """
        pass

class CodeProcessor(ABC):
    """
    코드 구성 요소 처리를 위한 인터페이스
    다양한 코드 요소(컴포넌트, 훅 등)를 추출하는 프로세서의 기본 클래스
    """
    
    @abstractmethod
    def process(self, code: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        코드에서 특정 요소 추출 및 처리
        
        Args:
            code: 처리할 코드
            file_info: 파일 메타데이터
            
        Returns:
            List[Dict[str, Any]]: 추출된 요소 목록
        """
        pass

class MetadataExtractor(ABC):
    """
    파일 및 코드 메타데이터 추출을 위한 인터페이스
    """
    
    @abstractmethod
    def extract_file_metadata(self, file_path: str, code: str) -> Dict[str, Any]:
        """
        파일 메타데이터 추출
        
        Args:
            file_path: 파일 경로
            code: 파일 내용
            
        Returns:
            Dict[str, Any]: 추출된 메타데이터
        """
        pass
    
    @abstractmethod
    def extract_component_metadata(self, component: Dict[str, Any], file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        컴포넌트 메타데이터 추출
        
        Args:
            component: 컴포넌트 정보
            file_info: 파일 메타데이터
            
        Returns:
            Dict[str, Any]: 추출된 메타데이터
        """
        pass