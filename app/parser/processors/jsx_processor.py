"""
JSX 요소 처리 모듈
"""

import re
from typing import Dict, List, Any, Optional

from app.parser.base import CodeProcessor
from app.parser.utils import JSX_ELEMENT_PATTERN

class JSXProcessor(CodeProcessor):
    """
    JSX 요소 파싱 프로세서
    """
    
    def __init__(self, min_size: int = 50):
        """
        Args:
            min_size: 추출할 최소 JSX 크기
        """
        self.min_size = min_size
    
    def process(self, code: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        코드에서 JSX 요소 추출
        
        Args:
            code: 처리할 코드
            file_info: 파일 메타데이터
            
        Returns:
            List[Dict[str, Any]]: 추출된 JSX 요소 목록
        """
        jsx_elements = []
        
        # JSX 요소 패턴 매칭
        matches = JSX_ELEMENT_PATTERN.finditer(code)
        
        for match in matches:
            element_name = match.group(1)
            jsx_code = match.group(0)
            start_pos = match.start()
            
            # 최소 크기 이상인 JSX 요소만 추출
            if len(jsx_code) > self.min_size:
                jsx_elements.append({
                    'name': element_name,
                    'code': jsx_code,
                    'start_pos': start_pos
                })
        
        return jsx_elements
    
    def extract_props(self, jsx_code: str) -> Dict[str, str]:
        """
        JSX 요소에서 props 추출
        
        Args:
            jsx_code: JSX 코드
            
        Returns:
            Dict[str, str]: 추출된 props와 값
        """
        props = {}
        
        # 여는 태그 찾기
        opening_tag_match = re.search(r'<([A-Z][a-zA-Z0-9]*)(.*?)>', jsx_code)
        if not opening_tag_match:
            return props
            
        props_text = opening_tag_match.group(2)
        
        # props 추출
        # 1. 문자열 값을 가진 props: prop="value" 또는 prop='value'
        string_props = re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', props_text)
        for match in string_props:
            props[match.group(1)] = match.group(2)
        
        # 2. 표현식 값을 가진 props: prop={expression}
        expr_props = re.finditer(r'(\w+)\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', props_text)
        for match in expr_props:
            props[match.group(1)] = f"{{{match.group(2)}}}"
        
        # 3. 불리언 props: prop
        bool_props = re.finditer(r'(\s+)(\w+)(\s+|>|$)', props_text)
        for match in bool_props:
            prop_name = match.group(2)
            if prop_name not in props and not prop_name.startswith('on') and len(prop_name) > 1:  # 이벤트 핸들러 제외
                props[prop_name] = 'true'
        
        return props
    
    def extract_children(self, jsx_code: str) -> List[Dict[str, Any]]:
        """
        JSX 요소에서 자식 요소 추출
        
        Args:
            jsx_code: JSX 코드
            
        Returns:
            List[Dict[str, Any]]: 추출된 자식 요소 정보
        """
        children = []
        
        # 여는 태그와 닫는 태그 사이의 내용 추출
        element_name = re.search(r'<([A-Z][a-zA-Z0-9]*)', jsx_code).group(1)
        content_match = re.search(fr'<{element_name}[^>]*>(.*?)</{element_name}>', jsx_code, re.DOTALL)
        
        if not content_match:
            return children
            
        content = content_match.group(1)
        
        # 자식 JSX 요소 찾기
        child_matches = JSX_ELEMENT_PATTERN.finditer(content)
        
        for match in child_matches:
            child_name = match.group(1)
            child_code = match.group(0)
            
            children.append({
                'name': child_name,
                'code': child_code
            })
        
        return children
    
    def classify_jsx_element(self, jsx_code: str) -> str:
        """
        JSX 요소의 역할/목적 분류
        
        Args:
            jsx_code: JSX 코드
            
        Returns:
            str: 분류된 역할 (container, list, form, button, text, layout, mixed)
        """
        element_name = re.search(r'<([A-Z][a-zA-Z0-9]*)', jsx_code).group(1)
        
        # 이름 기반 분류
        if any(container in element_name for container in ['Container', 'Box', 'Wrapper', 'Panel', 'Section']):
            return 'container'
        if any(list_item in element_name for list_item in ['List', 'Items', 'Collection', 'Grid']):
            return 'list'
        if any(form in element_name for form in ['Form', 'Input', 'Field', 'Select']):
            return 'form'
        if 'Button' in element_name:
            return 'button'
        if any(text in element_name for text in ['Text', 'Typography', 'Label', 'Title', 'Heading']):
            return 'text'
        if any(layout in element_name for layout in ['Layout', 'Row', 'Column', 'Flex']):
            return 'layout'
        
        # 내용 기반 분류
        if '.map(' in jsx_code:
            return 'list'
        if 'onChange=' in jsx_code or 'onSubmit=' in jsx_code or '<input' in jsx_code.lower():
            return 'form'
        if 'onClick=' in jsx_code or '<button' in jsx_code.lower():
            return 'button'
        
        # 기본 분류
        return 'mixed'