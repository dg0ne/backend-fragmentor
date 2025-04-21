"""
코드 파편화를 위한 기본 인터페이스 및 추상 클래스 정의
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class CodeExtractor(ABC):
    """
    코드 파편 추출을 위한 기본 추상 클래스
    모든 파편 유형별 추출기(Extractor)는 이 클래스를 상속해야 함
    """
    
    @abstractmethod
    def extract(self, code: str, metadata: Dict[str, Any], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        코드에서 특정 유형의 파편을 추출
        
        Args:
            code: 분석할 소스 코드
            metadata: 파일 메타데이터 정보
            parent_id: 부모 파편 ID (있는 경우)
            
        Returns:
            List[Dict[str, Any]]: 추출된 코드 파편 목록
        """
        pass
    
    def normalize_code(self, code: str) -> str:
        """
        코드 정규화: 주석 제거, 공백 처리 등
        
        Args:
            code: 정규화할 코드
            
        Returns:
            str: 정규화된 코드
        """
        # 기본 구현은 원본 코드 반환, 필요에 따라 하위 클래스에서 오버라이드
        return code.strip()
    
    def _create_fragment(self, 
                        fragment_id: str,
                        fragment_type: str,
                        name: str,
                        content: str,
                        metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        표준화된 파편 객체 생성 헬퍼 메소드
        
        Args:
            fragment_id: 파편 ID
            fragment_type: 파편 유형 (component, function 등)
            name: 파편 이름
            content: 파편 코드 내용
            metadata: 파편 메타데이터
            
        Returns:
            Dict[str, Any]: 생성된 파편 객체
        """
        return {
            'id': fragment_id,
            'type': fragment_type,
            'name': name,
            'content': content,
            'metadata': metadata
        }


class FragmenterStrategy(ABC):
    """
    파편화 전략 인터페이스
    다양한 파편화 전략 구현을 위한 기본 클래스
    """
    
    @abstractmethod
    def fragment_file(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        파일 단위 파편화 수행
        
        Args:
            parsed_file: 파싱된 파일 정보
            
        Returns:
            List[Dict[str, Any]]: 추출된 코드 파편 목록
        """
        pass
    
    @abstractmethod
    def fragment_project(self, parsed_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        프로젝트 단위 파편화 수행
        
        Args:
            parsed_project: 파싱된 프로젝트 정보
            
        Returns:
            Dict[str, Any]: 파편화 결과 및 메타데이터
        """
        pass