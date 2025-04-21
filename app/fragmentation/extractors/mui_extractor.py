"""
Material UI 컴포넌트 추출기
"""

import re
import uuid
from typing import List, Dict, Any, Optional

from app.fragmentation.base import CodeExtractor
from app.fragmentation.utils import normalize_code, extract_jsx_element

class MUIExtractor(CodeExtractor):
    """Material UI 컴포넌트 추출을 위한 추출기"""
    
    def __init__(self):
        # MUI 컴포넌트 감지 패턴
        self.mui_component_pattern = re.compile(r'<(Box|Typography|Button|Card|Paper|Grid|TextField|Container|CircularProgress)')
        # MUI import 패턴
        self.mui_import_pattern = re.compile(r'import\s+\{(.*?)\}\s+from\s+[\'"]@mui/material[\'"](.*?);')
    
    def extract(self, code: str, metadata: Dict[str, Any], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        코드에서 Material UI 컴포넌트 추출
        
        Args:
            code: 분석할 소스 코드
            metadata: 파일 메타데이터 정보
            parent_id: 부모 파편 ID (있는 경우)
            
        Returns:
            List[Dict[str, Any]]: 추출된 MUI 컴포넌트 파편 목록
        """
        mui_components = []
        
        # MUI import 문 확인 (MUI를 사용하지 않는 파일은 건너뛰기)
        mui_imports = self.mui_import_pattern.finditer(code)
        imported_components = []
        
        for match in mui_imports:
            components_str = match.group(1)
            imported_components.extend([c.strip() for c in components_str.split(',')])
        
        # MUI 컴포넌트를 사용하지 않는 경우 빈 결과 반환
        if not imported_components:
            return mui_components
        
        # MUI 컴포넌트 패턴 매칭
        matches = self.mui_component_pattern.finditer(code)
        
        for match in matches:
            mui_start = match.start()
            mui_name = match.group(1)
            
            # 해당 JSX 요소 전체 추출 시도
            jsx_code = extract_jsx_element(code, mui_start)
            
            # 유효하고 일정 크기 이상인 경우만 추출
            if jsx_code and len(jsx_code) > 50:
                # 파편 메타데이터 생성
                mui_metadata = {
                    'file_path': metadata.get('file_path', ''),
                    'file_name': metadata.get('file_name', ''),
                    'start_pos': mui_start,
                    'length': len(jsx_code),
                    'component_library': 'material-ui',
                    'mui_component': mui_name
                }
                
                # 부모 파편 ID가 있으면 추가
                if parent_id:
                    mui_metadata['parent_id'] = parent_id
                
                # MUI 컴포넌트별 추가 메타데이터
                if mui_name == 'Card' or mui_name == 'Paper':
                    mui_metadata['ui_type'] = 'container'
                    mui_metadata['purpose'] = '컨텐츠 그룹화'
                elif mui_name == 'Grid':
                    mui_metadata['ui_type'] = 'layout'
                    mui_metadata['purpose'] = '레이아웃 구성'
                elif mui_name == 'Typography':
                    mui_metadata['ui_type'] = 'text'
                    mui_metadata['purpose'] = '텍스트 표시'
                elif mui_name == 'Button':
                    mui_metadata['ui_type'] = 'action'
                    mui_metadata['purpose'] = '사용자 상호작용'
                elif mui_name == 'TextField':
                    mui_metadata['ui_type'] = 'input'
                    mui_metadata['purpose'] = '사용자 입력'
                elif mui_name == 'CircularProgress':
                    mui_metadata['ui_type'] = 'feedback'
                    mui_metadata['purpose'] = '로딩 상태 표시'
                
                # 중복 방지
                is_duplicate = False
                for existing_mui in mui_components:
                    if existing_mui['content'] == normalize_code(jsx_code):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    # 파편 생성
                    mui_components.append(self._create_fragment(
                        str(uuid.uuid4()),
                        'mui_component',
                        mui_name,
                        normalize_code(jsx_code),
                        mui_metadata
                    ))
        
        return mui_components
    
    def detect_mui_usage(self, code: str) -> Dict[str, Any]:
        """
        코드에서 MUI 사용 감지
        
        Args:
            code: 분석할 소스 코드
            
        Returns:
            Dict[str, Any]: MUI 사용 정보
        """
        mui_data = {
            'used': False,
            'components': []
        }
        
        # MUI import 문 확인
        mui_imports = self.mui_import_pattern.finditer(code)
        for match in mui_imports:
            mui_data['used'] = True
            components_str = match.group(1)
            imported_components = [c.strip() for c in components_str.split(',')]
            mui_data['components'].extend(imported_components)
            
        return mui_data