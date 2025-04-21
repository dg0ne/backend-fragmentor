"""
React 훅 처리 모듈
"""

import re
from typing import Dict, List, Any, Optional

from app.parser.base import CodeProcessor
from app.parser.utils import extract_code_block

class HookProcessor(CodeProcessor):
    """
    React 훅 파싱 프로세서
    """
    
    def __init__(self):
        # 커스텀 훅 함수 패턴
        self.custom_hook_pattern = re.compile(r'function\s+(use[A-Z][a-zA-Z0-9]*)\s*\(')
        
        # 내장 훅 패턴
        self.builtin_hooks = [
            'useState', 'useEffect', 'useContext', 'useReducer',
            'useCallback', 'useMemo', 'useRef', 'useLayoutEffect',
            'useImperativeHandle', 'useDebugValue'
        ]
    
    def process(self, code: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        코드에서 React 훅 추출
        
        Args:
            code: 처리할 코드
            file_info: 파일 메타데이터
            
        Returns:
            List[Dict[str, Any]]: 추출된 훅 목록
        """
        hooks = []
        
        # 1. 커스텀 훅 함수 추출
        custom_hooks = self._extract_custom_hooks(code)
        hooks.extend(custom_hooks)
        
        # 2. 내장 훅 사용 추출
        builtin_hooks = self._extract_builtin_hooks(code, custom_hooks)
        hooks.extend(builtin_hooks)
        
        return hooks
    
    def _extract_custom_hooks(self, code: str) -> List[Dict[str, Any]]:
        """
        커스텀 훅 함수 추출
        
        Args:
            code: 소스 코드
            
        Returns:
            List[Dict[str, Any]]: 추출된 커스텀 훅 목록
        """
        custom_hooks = []
        
        # 커스텀 훅 함수 찾기
        matches = self.custom_hook_pattern.finditer(code)
        
        for match in matches:
            hook_name = match.group(1)
            start_pos = match.start()
            
            # 훅 코드 블록 추출
            hook_code = extract_code_block(code, start_pos)
            if not hook_code:
                # 추출 실패 시 적당한 길이만큼 추출
                hook_code = code[start_pos:min(start_pos + 500, len(code))]
            
            # 이 훅이 사용하는 다른 내장 훅들 추출
            used_hooks = self._find_used_hooks(hook_code)
            
            custom_hooks.append({
                'name': hook_name,
                'code': hook_code,
                'start_pos': start_pos,
                'type': 'custom',
                'used_hooks': used_hooks
            })
        
        return custom_hooks
    
    def _extract_builtin_hooks(self, code: str, custom_hooks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        내장 훅 사용 추출
        
        Args:
            code: 소스 코드
            custom_hooks: 이미 추출된 커스텀 훅 목록
            
        Returns:
            List[Dict[str, Any]]: 추출된 내장 훅 사용 목록
        """
        builtin_hook_usages = []
        
        # 커스텀 훅 코드 위치 범위 계산
        custom_hook_ranges = [
            (hook['start_pos'], hook['start_pos'] + len(hook['code'])) 
            for hook in custom_hooks
        ]
        
        # 각 내장 훅에 대해 검색
        for hook_name in self.builtin_hooks:
            hook_pattern = re.compile(fr'{hook_name}\(')
            matches = hook_pattern.finditer(code)
            
            for match in matches:
                start_pos = match.start()
                
                # 이미 커스텀 훅 내부에서 사용된 것인지 확인
                is_inside_custom = False
                for start, end in custom_hook_ranges:
                    if start <= start_pos < end:
                        is_inside_custom = True
                        break
                
                if not is_inside_custom:
                    # 훅 사용 위치 기록
                    builtin_hook_usages.append({
                        'name': hook_name,
                        'start_pos': start_pos,
                        'type': 'builtin'
                    })
        
        return builtin_hook_usages
    
    def _find_used_hooks(self, hook_code: str) -> List[str]:
        """
        훅 코드 내에서 사용된 내장 훅 찾기
        
        Args:
            hook_code: 훅 코드
            
        Returns:
            List[str]: 사용된 내장 훅 이름 목록
        """
        used_hooks = []
        
        for hook_name in self.builtin_hooks:
            pattern = re.compile(fr'{hook_name}\(')
            if pattern.search(hook_code):
                used_hooks.append(hook_name)
        
        return used_hooks
    
    def analyze_hook_dependencies(self, hook_code: str) -> Dict[str, List[str]]:
        """
        훅의 의존성 분석
        
        Args:
            hook_code: 훅 코드
            
        Returns:
            Dict[str, List[str]]: 훅 이름을 키로, 의존성 목록을 값으로 하는 딕셔너리
        """
        dependencies = {}
        
        # useEffect 의존성 추출
        effect_matches = re.finditer(r'useEffect\(\s*\(\s*\)\s*=>\s*{.*?}\s*,\s*\[(.*?)\]\s*\)', hook_code, re.DOTALL)
        
        for i, match in enumerate(effect_matches):
            deps_str = match.group(1).strip()
            deps = [d.strip() for d in deps_str.split(',') if d.strip()]
            dependencies[f'useEffect_{i}'] = deps
        
        # useCallback, useMemo 의존성 추출
        callback_matches = re.finditer(r'(useCallback|useMemo)\(\s*.*?,\s*\[(.*?)\]\s*\)', hook_code, re.DOTALL)
        
        for i, match in enumerate(callback_matches):
            hook_type = match.group(1)
            deps_str = match.group(2).strip()
            deps = [d.strip() for d in deps_str.split(',') if d.strip()]
            dependencies[f'{hook_type}_{i}'] = deps
        
        return dependencies