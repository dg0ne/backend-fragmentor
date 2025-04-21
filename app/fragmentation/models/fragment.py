"""
코드 파편 모델 클래스
"""

import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class CodeFragment:
    """
    코드 파편 표현을 위한 데이터 클래스
    """
    type: str                          # 파편 유형 (component, function 등)
    name: str                          # 파편 이름
    content: str                       # 파편 코드 내용
    metadata: Dict[str, Any]           # 파편 메타데이터
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # 고유 ID
    parent_id: Optional[str] = None    # 부모 파편 ID (있는 경우)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        파편 객체를 딕셔너리로 변환
        
        Returns:
            Dict[str, Any]: 딕셔너리 형태의 파편
        """
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'content': self.content,
            'metadata': self.metadata,
            'parent_id': self.parent_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeFragment':
        """
        딕셔너리에서 파편 객체 생성
        
        Args:
            data: 딕셔너리 형태의 파편 데이터
            
        Returns:
            CodeFragment: 생성된 파편 객체
        """
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            type=data['type'],
            name=data['name'],
            content=data['content'],
            metadata=data['metadata'],
            parent_id=data.get('parent_id')
        )
    
    def get_content_preview(self, max_length: int = 150) -> str:
        """
        파편 내용의 미리보기 반환
        
        Args:
            max_length: 최대 길이
            
        Returns:
            str: 미리보기 텍스트
        """
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + '...'
    
    def is_component(self) -> bool:
        """컴포넌트 여부 확인"""
        return self.type == 'component'
    
    def is_function(self) -> bool:
        """함수 여부 확인"""
        return self.type == 'function'
    
    def is_jsx_element(self) -> bool:
        """JSX 요소 여부 확인"""
        return self.type == 'jsx_element'
    
    def is_api_call(self) -> bool:
        """API 호출 여부 확인"""
        return self.type == 'api_call'