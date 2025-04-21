"""
React 컴포넌트 처리 모듈
"""

import re
from typing import Dict, List, Any, Optional

from app.parser.base import CodeProcessor
from app.parser.utils import (
    COMPONENT_PATTERNS, 
    extract_code_block, 
    detect_component_type
)

class ComponentProcessor(CodeProcessor):
    """
    React 컴포넌트 파싱 프로세서
    """
    
    def process(self, code: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        코드에서 React 컴포넌트 추출
        
        Args:
            code: 처리할 코드
            file_info: 파일 메타데이터
            
        Returns:
            List[Dict[str, Any]]: 추출된 컴포넌트 목록
        """
        components = []
        
        # 각 컴포넌트 패턴으로 컴포넌트 추출
        for pattern in COMPONENT_PATTERNS:
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
                
                # 컴포넌트 타입 감지
                component_type = detect_component_type(component_code)
                
                # props 추출
                props = self._extract_props(component_code)
                
                # 상태(useState) 추출
                states = self._extract_states(component_code)
                
                # 컴포넌트 객체 생성
                components.append({
                    'name': name,
                    'code': component_code,
                    'start_pos': start_pos,
                    'component_type': component_type,
                    'props': props,
                    'states': states,
                    'pattern_type': pattern.pattern
                })
        
        return components
    
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
    
    def find_component_by_name(self, code: str, component_name: str) -> Optional[Dict[str, Any]]:
        """
        코드에서 특정 이름의 컴포넌트 찾기
        
        Args:
            code: 소스 코드
            component_name: 찾을 컴포넌트 이름
            
        Returns:
            Optional[Dict[str, Any]]: 찾은 컴포넌트 또는 None
        """
        components = self.process(code, {})
        
        for component in components:
            if component['name'] == component_name:
                return component
                
        return None
    
    def get_component_hierarchy(self, components: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        컴포넌트 계층 구조 분석
        
        Args:
            components: 컴포넌트 목록
            
        Returns:
            Dict[str, List[str]]: 컴포넌트 이름을 키로, 자식 컴포넌트 목록을 값으로 하는 딕셔너리
        """
        hierarchy = {}
        
        # 각 컴포넌트 코드에서 다른 컴포넌트 사용 검사
        for component in components:
            name = component['name']
            code = component['code']
            
            # 이 컴포넌트가 사용하는 다른 컴포넌트들
            used_components = []
            
            for other in components:
                other_name = other['name']
                
                # 자기 자신은 제외
                if other_name == name:
                    continue
                    
                # 정규 표현식으로 사용 여부 확인
                pattern = fr'<{other_name}[\s/>]'
                if re.search(pattern, code):
                    used_components.append(other_name)
            
            hierarchy[name] = used_components
            
        return hierarchy