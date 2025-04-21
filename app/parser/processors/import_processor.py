"""
Import 문 처리 모듈
"""

import re
from typing import Dict, List, Any, Optional

from app.parser.base import CodeProcessor
from app.parser.utils import MUI_IMPORT_PATTERN

class ImportProcessor(CodeProcessor):
    """
    Import 문 파싱 프로세서
    """
    
    def __init__(self):
        # import 문 패턴
        self.import_pattern = re.compile(r'^import.*?;$', re.MULTILINE)
        
        # 라이브러리 패턴
        self.library_patterns = {
            'react': r'import\s+.*?[\'"]react[\'"]',
            'react-router': r'import\s+.*?[\'"]react-router.*?[\'"]',
            'mui': r'import\s+.*?[\'"]@mui/.*?[\'"]',
            'api': r'import\s+.*?[\'"].*?(/api/|services/api|api\.).*?[\'"]',
            'hooks': r'import\s+.*?[\'"].*?(/hooks/|contexts/|useAuth).*?[\'"]',
            'redux': r'import\s+.*?[\'"].*?(redux|useDispatch|useSelector).*?[\'"]',
            'formik': r'import\s+.*?[\'"].*?(formik|useFormik).*?[\'"]',
            'axios': r'import\s+.*?[\'"]axios[\'"]'
        }
    
    def process(self, code: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        코드에서 Import 문 분석
        
        Args:
            code: 처리할 코드
            file_info: 파일 메타데이터
            
        Returns:
            List[Dict[str, Any]]: 분석된 Import 정보
        """
        # import 문 패턴 매칭
        matches = list(self.import_pattern.finditer(code))
        
        if not matches:
            return []
            
        # 모든 import 문 결합
        imports_text = '\n'.join(code[m.start():m.end()] for m in matches)
        
        if imports_text:
            # 라이브러리 사용 분석
            libraries = self._analyze_libraries(imports_text)
            
            # 가져온 컴포넌트 분석
            imported_components = self._extract_imported_components(imports_text)
            
            # MUI 컴포넌트 분석
            mui_components = self._extract_mui_components(imports_text)
            
            return [{
                'imports_text': imports_text,
                'imports_count': len(matches),
                'libraries': libraries,
                'imported_components': imported_components,
                'mui_components': mui_components
            }]
        
        return []
    
    def _analyze_libraries(self, imports_text: str) -> Dict[str, bool]:
        """
        Import 문에서 사용된 라이브러리 분석
        
        Args:
            imports_text: Import 문 텍스트
            
        Returns:
            Dict[str, bool]: 라이브러리 사용 여부
        """
        libraries = {}
        
        for lib_name, pattern in self.library_patterns.items():
            libraries[lib_name] = bool(re.search(pattern, imports_text, re.IGNORECASE))
        
        return libraries
    
    def _extract_imported_components(self, imports_text: str) -> List[str]:
        """
        Import 문에서 가져온 컴포넌트 이름 추출
        
        Args:
            imports_text: Import 문 텍스트
            
        Returns:
            List[str]: 가져온 컴포넌트 이름 목록
        """
        components = []
        
        # 중괄호 내 컴포넌트 추출
        component_pattern = re.compile(r'import\s+\{(.*?)\}\s+from', re.DOTALL)
        matches = component_pattern.finditer(imports_text)
        
        for match in matches:
            components_str = match.group(1)
            # 쉼표로 구분된 이름 추출
            components.extend([c.strip() for c in components_str.split(',') if c.strip()])
        
        # 단일 컴포넌트 import 추출
        single_pattern = re.compile(r'import\s+([A-Z][a-zA-Z0-9]*)\s+from')
        single_matches = single_pattern.finditer(imports_text)
        
        for match in single_matches:
            component_name = match.group(1)
            if component_name not in components:
                components.append(component_name)
        
        return components
    
    def _extract_mui_components(self, imports_text: str) -> List[str]:
        """
        Material UI 컴포넌트 추출
        
        Args:
            imports_text: Import 문 텍스트
            
        Returns:
            List[str]: MUI 컴포넌트 이름 목록
        """
        mui_components = []
        
        # MUI import 문 확인
        mui_imports = MUI_IMPORT_PATTERN.finditer(imports_text)
        
        for match in mui_imports:
            components_str = match.group(1)
            # 쉼표로 구분된 컴포넌트 이름 추출
            mui_components.extend([c.strip() for c in components_str.split(',') if c.strip()])
        
        return mui_components
    
    def analyze_dependencies(self, imports_text: str) -> Dict[str, List[str]]:
        """
        Import 문에서 모듈 의존성 분석
        
        Args:
            imports_text: Import 문 텍스트
            
        Returns:
            Dict[str, List[str]]: 모듈 유형별 의존성 목록
        """
        dependencies = {
            'external': [],  # 외부 패키지
            'internal': [],  # 프로젝트 내부 모듈
            'relative': []   # 상대 경로 모듈
        }
        
        # 각 import 문 분석
        import_lines = imports_text.split('\n')
        
        for line in import_lines:
            # from 구문 추출
            from_match = re.search(r'from\s+[\'"](.+?)[\'"]', line)
            if not from_match:
                continue
                
            import_path = from_match.group(1)
            
            # 외부 패키지 (node_modules)
            if not import_path.startswith('.') and not import_path.startswith('/'):
                # 특정 경로를 포함하지 않으면 외부 패키지로 간주
                if '/' not in import_path or import_path.split('/')[0].startswith('@'):
                    dependencies['external'].append(import_path)
                else:
                    dependencies['internal'].append(import_path)
            # 상대 경로 모듈
            else:
                dependencies['relative'].append(import_path)
        
        return dependencies