"""
Import 문 추출기
"""

import re
import uuid
from typing import List, Dict, Any, Optional

from app.fragmentation.base import CodeExtractor
from app.fragmentation.utils import normalize_code

class ImportExtractor(CodeExtractor):
    """Import 문 추출을 위한 추출기"""
    
    def __init__(self):
        # import 문 패턴
        self.import_pattern = re.compile(r'^import.*?;$', re.MULTILINE)
    
    def extract(self, code: str, metadata: Dict[str, Any], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        코드에서 import 문 추출
        
        Args:
            code: 분석할 소스 코드
            metadata: 파일 메타데이터 정보
            parent_id: 부모 파편 ID (있는 경우)
            
        Returns:
            List[Dict[str, Any]]: 추출된 import 파편 목록 (최대 1개)
        """
        # import 문 패턴 매칭
        matches = list(self.import_pattern.finditer(code))
        
        if not matches:
            return []
            
        # 모든 import 문 결합
        imports_text = '\n'.join(code[m.start():m.end()] for m in matches)
        
        if imports_text:
            # 중요 라이브러리 사용 분석
            libraries = self._analyze_imports(imports_text)
            
            # 파편 메타데이터 생성
            import_metadata = {
                'file_path': metadata.get('file_path', ''),
                'file_name': metadata.get('file_name', ''),
                'imports_count': len(matches),
                'libraries': libraries
            }
            
            # 파편 생성
            return [self._create_fragment(
                str(uuid.uuid4()),
                'import_block',
                'imports',
                imports_text,
                import_metadata
            )]
        
        return []
    
    def _analyze_imports(self, imports_text: str) -> Dict[str, bool]:
        """
        import 문 분석하여 사용된 주요 라이브러리 확인
        
        Args:
            imports_text: import 문 텍스트
            
        Returns:
            Dict[str, bool]: 주요 라이브러리 사용 여부
        """
        libraries = {
            'react': False,
            'react-router': False,
            'mui': False,
            'api': False,
            'hooks': False,
            'redux': False,
            'formik': False,
            'axios': False
        }
        
        # 라이브러리 사용 여부 분석
        if 'import React' in imports_text:
            libraries['react'] = True
        if 'react-router' in imports_text:
            libraries['react-router'] = True
        if '@mui/material' in imports_text:
            libraries['mui'] = True
        if 'services/api' in imports_text or '/api/' in imports_text:
            libraries['api'] = True
        if 'contexts/' in imports_text or 'useAuth' in imports_text:
            libraries['hooks'] = True
        if 'redux' in imports_text or 'useDispatch' in imports_text or 'useSelector' in imports_text:
            libraries['redux'] = True
        if 'formik' in imports_text or 'useFormik' in imports_text:
            libraries['formik'] = True
        if 'axios' in imports_text:
            libraries['axios'] = True
        
        return libraries
    
    def extract_imported_components(self, imports_text: str) -> List[str]:
        """
        import 문에서 가져온 컴포넌트 이름 추출
        
        Args:
            imports_text: import 문 텍스트
            
        Returns:
            List[str]: 추출된 컴포넌트 이름 목록
        """
        components = []
        
        # 중괄호 내 컴포넌트 추출 패턴
        component_pattern = re.compile(r'import\s+\{(.*?)\}\s+from', re.DOTALL)
        matches = component_pattern.finditer(imports_text)
        
        for match in matches:
            components_str = match.group(1)
            # 쉼표로 구분된 이름 추출
            components.extend([c.strip() for c in components_str.split(',') if c.strip()])
        
        # 단일 컴포넌트 import 추출 패턴
        single_pattern = re.compile(r'import\s+([A-Z][a-zA-Z0-9]*)\s+from')
        single_matches = single_pattern.finditer(imports_text)
        
        for match in single_matches:
            component_name = match.group(1)
            if component_name not in components:
                components.append(component_name)
        
        return components