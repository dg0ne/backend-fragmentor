"""
React 컴포넌트 추출기
"""

import re
import uuid
from typing import List, Dict, Any, Optional

from app.fragmentation.base import CodeExtractor
from app.fragmentation.utils import normalize_code, extract_code_block, detect_component_type

class ComponentExtractor(CodeExtractor):
    """React 컴포넌트 추출을 위한 추출기"""
    
    def __init__(self):
        # React 컴포넌트 패턴들
        self.component_patterns = [
            # 함수형 컴포넌트
            re.compile(r'function\s+([A-Z][a-zA-Z0-9]*)\s*\('),
            # 클래스 컴포넌트
            re.compile(r'class\s+([A-Z][a-zA-Z0-9]*)\s+extends\s+React\.Component'),
            # 화살표 함수 컴포넌트
            re.compile(r'const\s+([A-Z][a-zA-Z0-9]*)\s*=\s*\(.*\)\s*=>\s*{'),
            # 화살표 함수 간단 표현
            re.compile(r'const\s+([A-Z][a-zA-Z0-9]*)\s*=\s*\(.*\)\s*=>\s*\('),
            # memo 래핑된 컴포넌트
            re.compile(r'const\s+([A-Z][a-zA-Z0-9]*)\s*=\s*React\.memo\('),
        ]
    
    def extract(self, code: str, metadata: Dict[str, Any], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        코드에서 React 컴포넌트 추출
        
        Args:
            code: 분석할 소스 코드
            metadata: 파일 메타데이터 정보
            parent_id: 부모 파편 ID (있는 경우)
            
        Returns:
            List[Dict[str, Any]]: 추출된 컴포넌트 파편 목록
        """
        components = []
        
        for pattern in self.component_patterns:
            matches = pattern.finditer(code)
            for match in matches:
                name = match.group(1)
                start_pos = match.start()
                
                # 컴포넌트 코드 블록 추출
                component_code = extract_code_block(code, start_pos)
                if not component_code:
                    # 추출 실패 시 적당한 길이만큼 추출
                    end_pos = min(start_pos + 500, len(code))
                    component_code = code[start_pos:end_pos]
                
                # 코드 정규화
                normalized_code = normalize_code(component_code)
                
                # 컴포넌트 메타데이터 생성
                component_metadata = self._create_component_metadata(
                    normalized_code, 
                    name, 
                    start_pos, 
                    len(component_code),
                    metadata
                )
                
                # 파편 생성
                components.append(self._create_fragment(
                    str(uuid.uuid4()),
                    'component',
                    name,
                    normalized_code,
                    component_metadata
                ))
        
        return components
    
    def _create_component_metadata(self, code: str, name: str, start_pos: int, 
                                  code_length: int, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        컴포넌트 파편 메타데이터 생성
        
        Args:
            code: 컴포넌트 코드
            name: 컴포넌트 이름
            start_pos: 시작 위치
            code_length: 코드 길이
            file_metadata: 파일 메타데이터
            
        Returns:
            Dict[str, Any]: 컴포넌트 메타데이터
        """
        # 기본 메타데이터
        component_metadata = {
            'file_path': file_metadata.get('file_path', ''),
            'file_name': file_metadata.get('file_name', ''),
            'start_pos': start_pos,
            'length': code_length,
            'component_type': detect_component_type(code),
            'props': self._extract_props(code),
            'states': self._extract_states(code)
        }
        
        # 카테고리 추가 (파일 정보에서 가져오기)
        if 'category' in file_metadata:
            component_metadata['category'] = file_metadata['category']
        
        # 컴포넌트의 기능 목적 추정
        if 'Auth' in name or 'Login' in name:
            component_metadata['purpose'] = '인증'
        elif 'Subscription' in name:
            component_metadata['purpose'] = '구독'
        elif 'List' in name or 'Item' in name:
            component_metadata['purpose'] = '목록'
        elif 'Detail' in name:
            component_metadata['purpose'] = '상세'
        elif 'Form' in name:
            component_metadata['purpose'] = '양식'
        else:
            component_metadata['purpose'] = '기타'
        
        return component_metadata
    
    def _extract_props(self, component_code: str) -> List[str]:
        """
        컴포넌트 코드에서 props 추출
        
        Args:
            component_code: 컴포넌트 코드
            
        Returns:
            List[str]: 추출된 props 목록
        """
        props = []
        
        # 함수형 컴포넌트의 파라미터 추출
        func_props_match = re.search(r'(?:function|const)\s+\w+\s*=\s*\(\s*\{(.*?)\}\s*\)', component_code, re.DOTALL)
        if func_props_match:
            props_str = func_props_match.group(1)
            # 쉼표로 구분된 props 추출
            props = [p.strip() for p in props_str.split(',') if p.strip()]
        
        # props 타입 검사 (PropTypes)
        proptypes_match = re.search(r'(\w+)\.propTypes\s*=\s*\{(.*?)\};', component_code, re.DOTALL)
        if proptypes_match:
            props_block = proptypes_match.group(2)
            # 각 프로퍼티 줄별로 추출
            for line in props_block.split(','):
                prop_match = re.search(r'(\w+)', line.strip())
                if prop_match and prop_match.group(1) not in props:
                    props.append(prop_match.group(1))
        
        return props
    
    def _extract_states(self, component_code: str) -> List[Dict[str, str]]:
        """
        컴포넌트 코드에서 상태(useState) 추출
        
        Args:
            component_code: 컴포넌트 코드
            
        Returns:
            List[Dict[str, str]]: 추출된 상태 목록
        """
        states = []
        
        # useState 사용 패턴 찾기
        state_matches = re.finditer(r'const\s+\[\s*(\w+)\s*,\s*set(\w+)\s*\]\s*=\s*useState\((.*?)\);', component_code)
        
        for match in state_matches:
            state_name = match.group(1)
            setter_name = match.group(2)
            initial_value = match.group(3).strip()
            
            states.append({
                'name': state_name,
                'setter': f'set{setter_name}',
                'initial_value': initial_value
            })
        
        return states