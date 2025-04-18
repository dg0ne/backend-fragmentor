"""
향상된 React/JSX 코드 파싱 모듈 - lifesub-web 프로젝트용
"""

import os
import re
import json
import esprima
from esprima import parseModule
from typing import Dict, List, Any, Tuple, Optional

class EnhancedJSXParser:
    """lifesub-web 프로젝트의 React JSX 코드를 파싱하는 클래스"""
    
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
        
        # React 훅 패턴
        self.hook_pattern = re.compile(r'(use[A-Z][a-zA-Z0-9]*)')
        
        # JSX 요소 패턴 (복잡한 중첩 구조를 고려한 단순화된 버전)
        self.jsx_element_pattern = re.compile(r'<([A-Z][a-zA-Z0-9]*)[\s\w=>"/\'\.:\-\(\)]*>[\s\S]*?</\1>', re.DOTALL)
        
        # MUI 컴포넌트 감지 패턴
        self.mui_import_pattern = re.compile(r'import\s+\{(.*?)\}\s+from\s+[\'"]@mui/material[\'"](.*?);')
        
        # 파일 필터 패턴 (lifesub-web에 맞게 조정)
        self.ignore_patterns = [
            r'\.git',
            r'node_modules',
            r'\.idea',
            r'build',
            r'public',
            r'\.env'
        ]
        
    def should_ignore_file(self, file_path: str) -> bool:
        """
        무시해야 할 파일 경로인지 확인
        
        Args:
            file_path: 확인할 파일 경로
            
        Returns:
            bool: 무시해야 하면 True, 그렇지 않으면 False
        """
        for pattern in self.ignore_patterns:
            if re.search(pattern, file_path):
                return True
        return False
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        JSX/JS 파일을 파싱하여 AST 및 주요 컴포넌트 정보 추출
        
        Args:
            file_path: 파싱할 파일 경로
            
        Returns:
            Dict: 파싱 결과와 메타데이터 포함한 딕셔너리
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        # 무시해야 할 파일인지 확인
        if self.should_ignore_file(file_path):
            return {
                'file_info': {
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'ignored': True
                },
                'ignored': True
            }
        
        # 파일 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except UnicodeDecodeError:
            # 인코딩 문제 발생 시 latin-1로 시도
            with open(file_path, 'r', encoding='latin-1') as f:
                code = f.read()
        
        # 파일 메타데이터
        file_info = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'extension': os.path.splitext(file_path)[1],
            'size': os.path.getsize(file_path),
        }
        
        # lifesub-web 관련 추가 메타데이터
        file_info.update(self._extract_lifesub_metadata(file_path, code))
        
        try:
            # AST 파싱 시도
            ast = parseModule(code, jsx=True, tolerant=True)
            
            # 컴포넌트 식별
            components = self._identify_components(code)
            
            # 훅 식별
            hooks = self._identify_hooks(code)
            
            # JSX 요소 식별
            jsx_elements = self._identify_jsx_elements(code)
            
            # MUI 컴포넌트 사용 감지
            mui_components = self._detect_mui_components(code)
            
            return {
                'file_info': file_info,
                'ast': ast,
                'components': components,
                'hooks': hooks,
                'jsx_elements': jsx_elements,
                'mui_components': mui_components,
                'raw_code': code
            }
        except Exception as e:
            # 파싱 오류 발생 시
            return {
                'file_info': file_info,
                'error': str(e),
                'raw_code': code
            }
    
    def _extract_lifesub_metadata(self, file_path: str, code: str) -> Dict[str, Any]:
        """
        lifesub-web 프로젝트 특화 메타데이터 추출
        
        Args:
            file_path: 파일 경로
            code: 파일 내용
            
        Returns:
            Dict: 추가 메타데이터
        """
        metadata = {}
        
        # 파일 경로에서 카테고리 추출
        path_parts = file_path.split(os.path.sep)
        if 'src' in path_parts:
            src_idx = path_parts.index('src')
            if len(path_parts) > src_idx + 1:
                category = path_parts[src_idx + 1]
                metadata['category'] = category
        
        # 컴포넌트 설명 주석 추출
        description_match = re.search(r'/\*\s*(.*?)\s*\*/', code, re.DOTALL)
        if description_match:
            metadata['description'] = description_match.group(1).strip()
        
        # 코드 내 주요 기능 라벨 추출
        if 'auth' in code.lower() or 'login' in code.lower():
            metadata['features'] = metadata.get('features', []) + ['인증']
        if 'subscription' in code.lower() or '구독' in code.lower():
            metadata['features'] = metadata.get('features', []) + ['구독']
        if 'recommend' in code.lower() or '추천' in code.lower():
            metadata['features'] = metadata.get('features', []) + ['추천']
        
        return metadata
    
    def _identify_components(self, code: str) -> List[Dict[str, Any]]:
        """코드에서 React 컴포넌트 식별"""
        components = []
        
        for pattern in self.component_patterns:
            matches = pattern.finditer(code)
            for match in matches:
                name = match.group(1)
                start_pos = match.start()
                
                # 컴포넌트 코드 블록 추출
                component_code = self._extract_component_code(code, start_pos)
                
                # 컴포넌트 props 추출
                props = self._extract_props(component_code)
                
                # 컴포넌트 상태 (useState) 추출
                states = self._extract_states(component_code)
                
                components.append({
                    'name': name,
                    'start_pos': start_pos,
                    'code': component_code,
                    'props': props,
                    'states': states,
                    'pattern_type': pattern.pattern
                })
        
        return components
    
    def _extract_props(self, component_code: str) -> List[str]:
        """컴포넌트 코드에서 props 추출"""
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
        """컴포넌트 코드에서 상태(useState) 추출"""
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
    
    def _identify_hooks(self, code: str) -> List[Dict[str, Any]]:
        """코드에서 React 훅 사용 식별"""
        hooks = []
        
        # 커스텀 훅 함수 찾기
        custom_hook_matches = re.finditer(r'function\s+(use[A-Z][a-zA-Z0-9]*)\s*\(', code)
        for match in custom_hook_matches:
            hook_name = match.group(1)
            start_pos = match.start()
            hook_code = self._extract_component_code(code, start_pos)
            
            hooks.append({
                'name': hook_name,
                'type': 'custom',
                'start_pos': start_pos,
                'code': hook_code
            })
        
        # 내장 훅 사용 찾기
        builtin_hooks = ['useState', 'useEffect', 'useContext', 'useReducer', 'useCallback', 'useMemo', 'useRef']
        for hook in builtin_hooks:
            hook_matches = re.finditer(fr'{hook}\(', code)
            for match in hook_matches:
                # 이미 커스텀 훅 내부에서 사용된 것인지 확인
                is_inside_custom = False
                for custom_hook in hooks:
                    if custom_hook['type'] == 'custom' and \
                       custom_hook['start_pos'] < match.start() and \
                       match.start() < custom_hook['start_pos'] + len(custom_hook['code']):
                        is_inside_custom = True
                        break
                
                if not is_inside_custom:
                    hooks.append({
                        'name': hook,
                        'type': 'builtin',
                        'start_pos': match.start()
                    })
        
        return hooks
    
    def _identify_jsx_elements(self, code: str) -> List[Dict[str, Any]]:
        """코드에서 주요 JSX 요소 식별"""
        jsx_elements = []
        
        # JSX 요소 패턴 매칭
        matches = self.jsx_element_pattern.finditer(code)
        
        for match in matches:
            element_name = match.group(1)
            jsx_code = match.group(0)
            
            # 일정 크기 이상의 JSX 요소만 추출
            if len(jsx_code) > 50:  # 임계값 설정
                jsx_elements.append({
                    'name': element_name,
                    'start_pos': match.start(),
                    'code': jsx_code
                })
        
        return jsx_elements
    
    def _detect_mui_components(self, code: str) -> Dict[str, Any]:
        """Material-UI 컴포넌트 사용 감지"""
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
    
    def _extract_component_code(self, code: str, start_pos: int) -> str:
        """
        주어진 시작 위치에서 컴포넌트 코드 블록 추출
        괄호 매칭을 통해 블록 끝 찾기
        """
        # 함수형 컴포넌트 또는 클래스 컴포넌트의 끝을 찾기 위한 방법
        bracket_count = 0
        found_opening = False
        end_pos = start_pos
        
        for i in range(start_pos, len(code)):
            if code[i] == '{':
                bracket_count += 1
                found_opening = True
            elif code[i] == '}':
                bracket_count -= 1
                
            if found_opening and bracket_count == 0:
                end_pos = i + 1
                break
                
        # 괄호를 찾지 못했거나 잘못된 경우, 최소한의 코드라도 반환
        if end_pos <= start_pos:
            # 화살표 함수 간단 표현식인 경우 괄호 매칭
            if '=> (' in code[start_pos:start_pos+100]:
                paren_count = 0
                found_opening_paren = False
                
                for i in range(start_pos, len(code)):
                    if code[i] == '(' and not found_opening_paren:
                        # 화살표 다음의 첫 여는 괄호
                        if '=> ' in code[start_pos:i]:
                            paren_count += 1
                            found_opening_paren = True
                    elif code[i] == '(' and found_opening_paren:
                        paren_count += 1
                    elif code[i] == ')':
                        paren_count -= 1
                        
                    if found_opening_paren and paren_count == 0:
                        end_pos = i + 1
                        break
            
            # 여전히 찾지 못한 경우 적당한 길이 반환
            if end_pos <= start_pos:
                end_pos = min(start_pos + 500, len(code))
            
        return code[start_pos:end_pos]
    
    def scan_directory(self, directory_path: str, extensions: List[str] = ['.jsx', '.js', '.tsx', '.ts']) -> Dict[str, Dict]:
        """
        디렉토리 내 React 파일들 스캔하여 파싱
        
        Args:
            directory_path: 스캔할 디렉토리 경로
            extensions: 처리할 파일 확장자
            
        Returns:
            Dict: 파일경로를 키로, 파싱 결과를 값으로 하는 딕셔너리
        """
        results = {}
        files_processed = 0
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    
                    # 무시해야 할 파일 건너뛰기
                    if self.should_ignore_file(file_path):
                        continue
                        
                    try:
                        files_processed += 1
                        if files_processed % 10 == 0:
                            print(f"처리 중... {files_processed}개 파일 완료")
                            
                        results[file_path] = self.parse_file(file_path)
                    except Exception as e:
                        print(f"파일 파싱 오류: {file_path} - {str(e)}")
        
        return results


def parse_react_project(project_path: str) -> Dict[str, Any]:
    """
    React 프로젝트 전체 파싱 헬퍼 함수 - lifesub-web에 최적화
    
    Args:
        project_path: React 프로젝트 디렉토리 경로
        
    Returns:
        Dict: 파싱 결과 및 요약 정보
    """
    parser = EnhancedJSXParser()
    print(f"lifesub-web 프로젝트 파싱 중: {project_path}")
    parsed_files = parser.scan_directory(project_path)
    
    # 프로젝트 요약 정보
    summary = {
        'total_files': len(parsed_files),
        'components_count': sum(len(data.get('components', [])) for _, data in parsed_files.items() if 'error' not in data),
        'hooks_usage': {},
        'mui_components': {},
        'file_extensions': {}
    }
    
    # 요약 통계 계산
    for _, data in parsed_files.items():
        if 'error' in data or data.get('ignored', False):
            continue
            
        # 파일 확장자 통계
        ext = data['file_info']['extension']
        if ext in summary['file_extensions']:
            summary['file_extensions'][ext] += 1
        else:
            summary['file_extensions'][ext] = 1
        
        # 훅 사용 통계
        for hook in data.get('hooks', []):
            hook_name = hook['name']
            if hook_name in summary['hooks_usage']:
                summary['hooks_usage'][hook_name] += 1
            else:
                summary['hooks_usage'][hook_name] = 1
                
        # MUI 컴포넌트 사용 통계
        if data.get('mui_components', {}).get('used', False):
            for comp in data.get('mui_components', {}).get('components', []):
                if comp in summary['mui_components']:
                    summary['mui_components'][comp] += 1
                else:
                    summary['mui_components'][comp] = 1
    
    # 특화된 lifesub-web 통계
    summary['lifesub_stats'] = extract_lifesub_specific_stats(parsed_files)
    
    return {
        'parsed_files': parsed_files,
        'summary': summary
    }

def extract_lifesub_specific_stats(parsed_files: Dict[str, Dict]) -> Dict[str, Any]:
    """
    lifesub-web 프로젝트 특화 통계 추출
    
    Args:
        parsed_files: 파싱된 파일 정보
        
    Returns:
        Dict: lifesub-web 특화 통계
    """
    stats = {
        'feature_categories': {},
        'components_by_category': {}
    }
    
    for file_path, data in parsed_files.items():
        if 'error' in data or data.get('ignored', False):
            continue
            
        # 카테고리 기반 통계
        category = data.get('file_info', {}).get('category', 'uncategorized')
        if category not in stats['components_by_category']:
            stats['components_by_category'][category] = 0
            
        stats['components_by_category'][category] += len(data.get('components', []))
        
        # 기능 기반 통계
        features = data.get('file_info', {}).get('features', [])
        for feature in features:
            if feature in stats['feature_categories']:
                stats['feature_categories'][feature] += 1
            else:
                stats['feature_categories'][feature] = 1
    
    return stats