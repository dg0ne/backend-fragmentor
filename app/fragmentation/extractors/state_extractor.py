"""
상태 관리 로직 추출기
"""

import re
import uuid
from typing import List, Dict, Any, Optional

from app.fragmentation.base import CodeExtractor
from app.fragmentation.utils import normalize_code, extract_effect_block, extract_effect_dependencies

class StateLogicExtractor(CodeExtractor):
    """상태 관리 로직 추출을 위한 추출기"""
    
    def __init__(self):
        # useEffect 패턴
        self.useeffect_pattern = re.compile(r'useEffect\(\s*\(\s*\)\s*=>\s*{')
        # useState 패턴
        self.usestate_pattern = re.compile(r'const\s+\[\s*(\w+)\s*,\s*set(\w+)\s*\]\s*=\s*useState\((.*?)\);')
        # useReducer 패턴
        self.usereducer_pattern = re.compile(r'const\s+\[\s*(\w+)\s*,\s*dispatch\s*\]\s*=\s*useReducer\((.*?)\);')
    
    def extract(self, code: str, metadata: Dict[str, Any], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        코드에서 상태 관리 로직 추출
        
        Args:
            code: 분석할 소스 코드
            metadata: 파일 메타데이터 정보
            parent_id: 부모 파편 ID (있는 경우)
            
        Returns:
            List[Dict[str, Any]]: 추출된 상태 관리 로직 파편 목록
        """
        state_logic = []
        
        # 1. useEffect 블록 추출
        for match in self.useeffect_pattern.finditer(code):
            effect_start = match.start()
            effect_code = extract_effect_block(code, effect_start)
            
            if effect_code:
                # 의존성 배열 추출
                dependencies = extract_effect_dependencies(effect_code)
                
                # 파편 메타데이터 생성
                effect_metadata = {
                    'file_path': metadata.get('file_path', ''),
                    'file_name': metadata.get('file_name', ''),
                    'start_pos': effect_start,
                    'length': len(effect_code),
                    'dependencies': dependencies,
                    'hook_type': 'useEffect'
                }
                
                # 부모 파편 ID가 있으면 추가
                if parent_id:
                    effect_metadata['parent_id'] = parent_id
                
                # useEffect 사용 목적 추론
                purpose = self._infer_effect_purpose(effect_code, dependencies)
                if purpose:
                    effect_metadata['purpose'] = purpose
                
                # API 호출 여부 확인
                if self._contains_api_call(effect_code):
                    effect_metadata['contains_api_call'] = True
                
                # 파편 생성
                state_logic.append(self._create_fragment(
                    str(uuid.uuid4()),
                    'state_logic',
                    'useEffect',
                    normalize_code(effect_code),
                    effect_metadata
                ))
        
        # 2. 복잡한 useState 로직 추출 (단순한 선언은 제외)
        # useState가 여러 개 연속으로 나타나는 경우 하나의 파편으로 묶기
        usestate_blocks = self._extract_usestate_blocks(code)
        
        for block in usestate_blocks:
            if block['states_count'] > 1:  # 여러 개의 useState가 연속으로 있는 경우만 추출
                # 파편 메타데이터 생성
                states_metadata = {
                    'file_path': metadata.get('file_path', ''),
                    'file_name': metadata.get('file_name', ''),
                    'start_pos': block['start_pos'],
                    'length': len(block['code']),
                    'states_count': block['states_count'],
                    'state_names': block['state_names'],
                    'hook_type': 'useState'
                }
                
                # 부모 파편 ID가 있으면 추가
                if parent_id:
                    states_metadata['parent_id'] = parent_id
                
                # 파편 생성
                state_logic.append(self._create_fragment(
                    str(uuid.uuid4()),
                    'state_logic',
                    'useState',
                    normalize_code(block['code']),
                    states_metadata
                ))
        
        # 3. useReducer 로직 추출
        for match in self.usereducer_pattern.finditer(code):
            reducer_start = match.start()
            state_name = match.group(1)
            reducer_ref = match.group(2)
            
            # useReducer 코드 블록 추출 (단순 추출)
            end_pos = match.end()
            context_start = max(0, reducer_start - 50)
            context_end = min(len(code), end_pos + 150)
            reducer_code = code[context_start:context_end]
            
            # 파편 메타데이터 생성
            reducer_metadata = {
                'file_path': metadata.get('file_path', ''),
                'file_name': metadata.get('file_name', ''),
                'start_pos': reducer_start,
                'length': len(reducer_code),
                'state_name': state_name,
                'reducer_ref': reducer_ref,
                'hook_type': 'useReducer'
            }
            
            # 부모 파편 ID가 있으면 추가
            if parent_id:
                reducer_metadata['parent_id'] = parent_id
            
            # 파편 생성
            state_logic.append(self._create_fragment(
                str(uuid.uuid4()),
                'state_logic',
                'useReducer',
                normalize_code(reducer_code),
                reducer_metadata
            ))
        
        return state_logic
    
    def _infer_effect_purpose(self, effect_code: str, dependencies: List[str]) -> Optional[str]:
        """
        useEffect 사용 목적 추론
        
        Args:
            effect_code: useEffect 코드
            dependencies: 의존성 배열
            
        Returns:
            Optional[str]: 추론된 목적 또는 None
        """
        # 의존성이 비어있으면 마운트/언마운트 이펙트
        if not dependencies:
            if 'return' in effect_code:
                return '컴포넌트 정리(cleanup)'
            return '컴포넌트 초기화'
        
        # API 호출이 포함된 경우
        if 'fetch' in effect_code or 'axios' in effect_code or '.get(' in effect_code or '.post(' in effect_code:
            return '데이터 페칭'
        
        # 이벤트 리스너 추가/제거
        if 'addEventListener' in effect_code or 'removeEventListener' in effect_code:
            return '이벤트 리스너 관리'
        
        # localStorage 접근
        if 'localStorage' in effect_code:
            return '로컬 스토리지 관리'
        
        # 타이머 설정
        if 'setTimeout' in effect_code or 'setInterval' in effect_code:
            return '타이머 관리'
        
        # 특정 의존성에 따른 상태 업데이트
        if any('set' + dep[0].upper() + dep[1:] in effect_code for dep in dependencies):
            return '의존성 기반 상태 업데이트'
        
        # 기본값
        return '상태 사이드 이펙트'
    
    def _contains_api_call(self, code: str) -> bool:
        """
        코드에 API 호출이 포함되어 있는지 확인
        
        Args:
            code: 검사할 코드
            
        Returns:
            bool: API 호출 포함 여부
        """
        api_patterns = [
            r'fetch\(',
            r'axios\.',
            r'\.get\(',
            r'\.post\(',
            r'\.put\(',
            r'\.delete\(',
            r'mySubscriptionApi',
            r'authApi',
            r'recommendApi'
        ]
        
        for pattern in api_patterns:
            if re.search(pattern, code):
                return True
        
        return False
    
    def _extract_usestate_blocks(self, code: str) -> List[Dict[str, Any]]:
        """
        연속된 useState 블록 추출
        
        Args:
            code: 분석할 소스 코드
            
        Returns:
            List[Dict[str, Any]]: 추출된 useState 블록 정보
        """
        blocks = []
        current_block = None
        
        for match in self.usestate_pattern.finditer(code):
            state_name = match.group(1)
            start_pos = match.start()
            end_pos = match.end()
            
            # 새 블록 시작 여부 확인
            if current_block is None or start_pos > current_block['end_pos'] + 10:
                # 이전 블록이 있으면 저장
                if current_block is not None:
                    blocks.append(current_block)
                
                # 새 블록 시작
                current_block = {
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'code': code[start_pos:end_pos],
                    'states_count': 1,
                    'state_names': [state_name]
                }
            else:
                # 기존 블록에 추가
                current_block['end_pos'] = end_pos
                current_block['code'] = code[current_block['start_pos']:end_pos]
                current_block['states_count'] += 1
                current_block['state_names'].append(state_name)
        
        # 마지막 블록 저장
        if current_block is not None:
            blocks.append(current_block)
        
        return blocks