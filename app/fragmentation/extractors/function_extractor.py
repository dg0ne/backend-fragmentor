"""
함수 추출기
"""

import re
import uuid
from typing import List, Dict, Any, Optional

from app.fragmentation.base import CodeExtractor
from app.fragmentation.utils import normalize_code, extract_code_block

class FunctionExtractor(CodeExtractor):
    """함수 추출을 위한 추출기"""
    
    def __init__(self):
        # 일반 함수 패턴
        self.function_pattern = re.compile(r'(function\s+([a-z][a-zA-Z0-9]*)\s*\([^)]*\)\s*{)')
        # 화살표 함수 패턴
        self.arrow_func_pattern = re.compile(r'const\s+([a-z][a-zA-Z0-9]*)\s*=\s*(?:async\s*)?\(\s*.*?\)\s*=>\s*{')
    
    def extract(self, code: str, metadata: Dict[str, Any], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        코드에서 함수 추출
        
        Args:
            code: 분석할 소스 코드
            metadata: 파일 메타데이터 정보
            parent_id: 부모 파편 ID (있는 경우)
            
        Returns:
            List[Dict[str, Any]]: 추출된 함수 파편 목록
        """
        functions = []
        
        # 1. 일반 함수 추출
        for match in self.function_pattern.finditer(code):
            func_start = match.start()
            func_name = match.group(2)
            func_code = extract_code_block(code, func_start)
            
            if func_code:
                # 함수 메타데이터 생성
                func_metadata = self._create_function_metadata(
                    func_name, func_code, func_start, metadata, parent_id, 'regular'
                )
                
                # 파편 생성
                functions.append(self._create_fragment(
                    str(uuid.uuid4()),
                    'function',
                    func_name,
                    normalize_code(func_code),
                    func_metadata
                ))
        
        # 2. 화살표 함수 추출
        for match in self.arrow_func_pattern.finditer(code):
            func_start = match.start()
            func_name = match.group(1)
            func_code = extract_code_block(code, func_start)
            
            if func_code:
                # 함수 메타데이터 생성
                func_metadata = self._create_function_metadata(
                    func_name, func_code, func_start, metadata, parent_id, 'arrow'
                )
                
                # 파편 생성
                functions.append(self._create_fragment(
                    str(uuid.uuid4()),
                    'function',
                    func_name,
                    normalize_code(func_code),
                    func_metadata
                ))
        
        return functions
    
    def _create_function_metadata(self, name: str, code: str, start_pos: int, 
                                 file_metadata: Dict[str, Any], parent_id: Optional[str], 
                                 func_type: str) -> Dict[str, Any]:
        """
        함수 메타데이터 생성
        
        Args:
            name: 함수 이름
            code: 함수 코드
            start_pos: 시작 위치
            file_metadata: 파일 메타데이터
            parent_id: 부모 파편 ID
            func_type: 함수 타입 (regular, arrow)
            
        Returns:
            Dict[str, Any]: 함수 메타데이터
        """
        # 기본 메타데이터
        func_metadata = {
            'file_path': file_metadata.get('file_path', ''),
            'file_name': file_metadata.get('file_name', ''),
            'start_pos': start_pos,
            'length': len(code),
            'function_type': func_type
        }
        
        # 부모 파편 ID가 있으면 추가
        if parent_id:
            func_metadata['parent_id'] = parent_id
        
        # 함수 목적 추론
        if name.startswith('handle') or name.endswith('Handler'):
            func_metadata['purpose'] = '이벤트 핸들러'
        elif name.startswith('fetch') or name.startswith('get') or name.startswith('load'):
            func_metadata['purpose'] = '데이터 가져오기'
        elif name.startswith('save') or name.startswith('update') or name.startswith('set'):
            func_metadata['purpose'] = '데이터 저장/수정'
        elif name.startswith('format') or name.startswith('convert'):
            func_metadata['purpose'] = '데이터 포맷팅'
        elif name.startswith('validate') or name.startswith('check'):
            func_metadata['purpose'] = '유효성 검사'
        elif name.startswith('render'):
            func_metadata['purpose'] = 'UI 렌더링'
        else:
            func_metadata['purpose'] = '기타 유틸리티'
        
        # 비동기 함수 여부
        if 'async' in code[:50]:
            func_metadata['is_async'] = True
        
        # 이벤트 핸들러 여부
        if 'event' in code[:100] or 'preventDefault' in code or 'stopPropagation' in code:
            func_metadata['is_event_handler'] = True
        
        return func_metadata