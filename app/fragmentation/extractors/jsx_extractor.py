"""
JSX 요소 추출기
"""

import re
import uuid
from typing import List, Dict, Any, Optional

from app.fragmentation.base import CodeExtractor
from app.fragmentation.utils import normalize_code, extract_jsx_element

class JSXExtractor(CodeExtractor):
    """JSX 요소 추출을 위한 추출기"""
    
    def __init__(self):
        # JSX 요소 패턴 (복잡한 중첩 구조를 고려한 단순화된 버전)
        self.jsx_element_pattern = re.compile(r'<([A-Z][a-zA-Z0-9]*)[\s\w=>"/\'\.:\-\(\)]*>[\s\S]*?</\1>', re.DOTALL)
    
    def extract(self, code: str, metadata: Dict[str, Any], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        코드에서 JSX 요소 추출
        
        Args:
            code: 분석할 소스 코드
            metadata: 파일 메타데이터 정보
            parent_id: 부모 파편 ID (있는 경우)
            
        Returns:
            List[Dict[str, Any]]: 추출된 JSX 요소 파편 목록
        """
        jsx_elements = []
        
        # JSX 요소 패턴 매칭
        matches = self.jsx_element_pattern.finditer(code)
        
        for match in matches:
            element_name = match.group(1)
            jsx_code = match.group(0)
            start_pos = match.start()
            
            # 일정 크기 이상의 JSX 요소만 추출 (너무 작은 것은 의미 없음)
            if len(jsx_code) <= 50:
                continue
                
            # 코드 정규화
            normalized_code = normalize_code(jsx_code)
            
            # 파편 메타데이터 생성
            jsx_metadata = {
                'file_path': metadata.get('file_path', ''),
                'file_name': metadata.get('file_name', ''),
                'start_pos': start_pos,
                'length': len(jsx_code)
            }
            
            # 부모 파편 ID가 있으면 추가
            if parent_id:
                jsx_metadata['parent_id'] = parent_id
            
            # 특정 JSX 요소에 대한 추가 메타데이터
            if 'Card' in element_name or 'Paper' in element_name:
                jsx_metadata['ui_type'] = 'card'
            elif 'List' in element_name:
                jsx_metadata['ui_type'] = 'list'
            elif 'Form' in element_name:
                jsx_metadata['ui_type'] = 'form'
            elif 'Button' in element_name:
                jsx_metadata['ui_type'] = 'button'
            elif 'Container' in element_name or 'Box' in element_name:
                jsx_metadata['ui_type'] = 'container'
            
            # 파편 생성
            jsx_elements.append(self._create_fragment(
                str(uuid.uuid4()),
                'jsx_element',
                element_name,
                normalized_code,
                jsx_metadata
            ))
        
        return jsx_elements
    
    def extract_nested_jsx(self, code: str, parent_metadata: Dict[str, Any], parent_id: str) -> List[Dict[str, Any]]:
        """
        컴포넌트 내부의 중첩된 JSX 요소 추출
        
        Args:
            code: 컴포넌트 코드
            parent_metadata: 부모 컴포넌트 메타데이터
            parent_id: 부모 컴포넌트 ID
            
        Returns:
            List[Dict[str, Any]]: 추출된 중첩 JSX 요소 목록
        """
        nested_jsx = []
        
        # JSX 요소 패턴 매칭
        matches = self.jsx_element_pattern.finditer(code)
        
        # 부모 파일 정보
        file_metadata = {
            'file_path': parent_metadata.get('file_path', ''),
            'file_name': parent_metadata.get('file_name', '')
        }
        
        for match in matches:
            jsx_name = match.group(1)
            jsx_code = match.group(0)
            
            # 일정 크기 이상의 JSX 요소만 파편화
            if len(jsx_code) > 80:
                start_pos = match.start()
                
                # 메타데이터에 부모 정보 추가
                jsx_metadata = {
                    **file_metadata,
                    'start_pos': start_pos,
                    'length': len(jsx_code),
                    'parent_id': parent_id
                }
                
                # 파편 생성
                nested_jsx.append(self._create_fragment(
                    str(uuid.uuid4()),
                    'jsx_element',
                    jsx_name,
                    normalize_code(jsx_code),
                    jsx_metadata
                ))
        
        return nested_jsx