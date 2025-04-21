"""
향상된 코드 파편화(Fragmentation) 모듈 - React 프로젝트용
"""

import re
import uuid
import json
from typing import List, Dict, Any, Tuple, Optional

class ReactFragmenter:
    """React 코드를 의미 단위로 파편화하는 클래스"""
    
    def __init__(self):
        # 파편화 단위 정의
        self.fragment_units = [
            'component',      # 리액트 컴포넌트
            'hook',           # 커스텀 훅
            'function',       # 일반 함수
            'jsx_element',    # JSX 요소
            'style_block',    # 스타일 정의
            'import_block',   # import 문 블록
            'api_call',       # API 호출 코드
            'mui_component',  # Material UI 컴포넌트 사용
            'state_logic',    # 상태 관리 로직
            'routing'         # 라우팅 관련 코드
        ]
        
        # 정규화 및 필터링 패턴
        self.whitespace_pattern = re.compile(r'\s+')
        self.comments_pattern = re.compile(r'//.*?$|/\*.*?\*/', re.MULTILINE | re.DOTALL)
        
        # lifesub-web 특화 패턴
        self.api_call_pattern = re.compile(r'(mySubscriptionApi|authApi|recommendApi)\.(get|post|put|delete).*?\(.*?\)')
        self.router_pattern = re.compile(r'(useNavigate|useParams|useLocation|Navigate|Routes|Route)')
        self.mui_component_pattern = re.compile(r'<(Box|Typography|Button|Card|Paper|Grid|TextField|Container|CircularProgress)')
        
        # 파편화 최소 크기 설정 추가
        self.min_component_size = 150  # 최소 150자 이상
        self.min_function_size = 80    # 최소 80자 이상
        self.min_jsx_size = 120        # 최소 120자 이상
        self.min_api_call_size = 100   # 최소 100자 이상
        self.min_style_block_size = 150  # 최소 150자 이상
        self.min_routing_size = 100    # 최소 100자 이상
        self.min_hook_size = 120       # 최소 120자 이상
        
    def fragment_file(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        파싱된 파일에서 의미 있는 코드 파편들을 추출
        
        Args:
            parsed_file: JSXParser로 파싱된 파일 정보
            
        Returns:
            List[Dict]: 추출된 코드 파편 목록
        """
        fragments = []
        
        # 무시된 파일이거나 파싱 오류가 있는 경우 처리
        if parsed_file.get('ignored', False):
            return fragments
            
        if 'error' in parsed_file:
            # 간단한 텍스트 기반 파편화 시도
            fragments.extend(self._fallback_fragmentation(parsed_file))
            return fragments
        
        file_info = parsed_file['file_info']
        
        # 컴포넌트 파편화 (크기 체크 추가)
        for component in parsed_file.get('components', []):
            if len(component['code']) >= self.min_component_size:  # 크기 체크 추가
                fragment = self._create_component_fragment(component, file_info)
                fragments.append(fragment)
                
                # 컴포넌트 내부 함수 및 JSX 요소 추가 파편화
                sub_fragments = self._extract_subfragments(component['code'], fragment['id'], file_info)
                fragments.extend(sub_fragments)
        
        # JSX 요소 파편화 (컴포넌트 외부에 있는 JSX) (크기 체크 추가)
        for jsx_element in parsed_file.get('jsx_elements', []):
            # 이미 컴포넌트의 일부로 파편화된 것 건너뛰기
            is_already_fragmented = False
            for component in parsed_file.get('components', []):
                if jsx_element['start_pos'] >= component['start_pos'] and \
                   jsx_element['start_pos'] < component['start_pos'] + len(component['code']):
                    is_already_fragmented = True
                    break
                    
            if not is_already_fragmented and len(jsx_element['code']) >= self.min_jsx_size:  # 크기 체크 추가
                fragment = self._create_jsx_fragment(jsx_element, file_info)
                fragments.append(fragment)
        
        # 훅 파편화 (크기 체크 추가)
        for hook in parsed_file.get('hooks', []):
            if hook['type'] == 'custom' and 'code' in hook and len(hook['code']) >= self.min_hook_size:  # 커스텀 훅만 독립 파편으로, 크기 체크 추가
                fragment = self._create_hook_fragment(hook, file_info)
                fragments.append(fragment)
        
        # import 문 파편화
        import_fragment = self._extract_import_statements(parsed_file['raw_code'], file_info)
        if import_fragment:
            fragments.append(import_fragment)
        
        # API 호출 파편화 (크기 체크 추가)
        api_fragments = self._extract_api_calls(parsed_file['raw_code'], file_info)
        api_fragments = [f for f in api_fragments if len(f['content']) >= self.min_api_call_size]  # 크기 필터링
        fragments.extend(api_fragments)
        
        # 라우팅 관련 코드 파편화 (크기 체크 추가)
        routing_fragments = self._extract_routing_code(parsed_file['raw_code'], file_info)
        routing_fragments = [f for f in routing_fragments if len(f['content']) >= self.min_routing_size]  # 크기 필터링
        fragments.extend(routing_fragments)
        
        return fragments
    
    def _create_component_fragment(self, component: Dict[str, Any], file_info: Dict[str, Any]) -> Dict[str, Any]:
        """컴포넌트 파편 생성"""
        # 코드 정규화
        code = self._normalize_code(component['code'])
        
        # lifesub-web 전용 메타데이터 추출
        component_metadata = {
            'file_path': file_info['file_path'],
            'file_name': file_info['file_name'],
            'start_pos': component['start_pos'],
            'length': len(component['code']),
            'component_type': self._detect_component_type(code),
            'props': component.get('props', []),
            'states': component.get('states', [])
        }
        
        # 카테고리 추가 (파일 정보에서 가져오기)
        if 'category' in file_info:
            component_metadata['category'] = file_info['category']
        
        # 컴포넌트의 기능 목적 추정
        if 'Auth' in component['name'] or 'Login' in component['name']:
            component_metadata['purpose'] = '인증'
        elif 'Subscription' in component['name']:
            component_metadata['purpose'] = '구독'
        elif 'List' in component['name'] or 'Item' in component['name']:
            component_metadata['purpose'] = '목록'
        elif 'Detail' in component['name']:
            component_metadata['purpose'] = '상세'
        elif 'Form' in component['name']:
            component_metadata['purpose'] = '양식'
        else:
            component_metadata['purpose'] = '기타'
        
        return {
            'id': str(uuid.uuid4()),
            'type': 'component',
            'name': component['name'],
            'content': code,
            'metadata': component_metadata
        }
    
    def _create_jsx_fragment(self, jsx_element: Dict[str, Any], file_info: Dict[str, Any]) -> Dict[str, Any]:
        """JSX 요소 파편 생성"""
        # 코드 정규화
        code = self._normalize_code(jsx_element['code'])
        
        return {
            'id': str(uuid.uuid4()),
            'type': 'jsx_element',
            'name': jsx_element['name'],
            'content': code,
            'metadata': {
                'file_path': file_info['file_path'],
                'file_name': file_info['file_name'],
                'start_pos': jsx_element['start_pos'],
                'length': len(jsx_element['code'])
            }
        }
    
    def _create_hook_fragment(self, hook: Dict[str, Any], file_info: Dict[str, Any]) -> Dict[str, Any]:
        """커스텀 훅 파편 생성"""
        # 코드 정규화
        code = self._normalize_code(hook['code'])
        
        return {
            'id': str(uuid.uuid4()),
            'type': 'hook',
            'name': hook['name'],
            'content': code,
            'metadata': {
                'file_path': file_info['file_path'],
                'file_name': file_info['file_name'],
                'start_pos': hook['start_pos'],
                'length': len(hook['code'])
            }
        }
    
    def _extract_subfragments(self, component_code: str, parent_id: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """컴포넌트 내부에서 추가 파편 추출"""
        sub_fragments = []
        
        # 내부 함수 추출
        function_pattern = re.compile(r'(function\s+([a-z][a-zA-Z0-9]*)\s*\([^)]*\)\s*{)')
        for match in function_pattern.finditer(component_code):
            func_start = match.start()
            func_name = match.group(2)
            func_code = self._extract_code_block(component_code, func_start)
            
            if func_code and len(func_code) >= self.min_function_size:  # 크기 체크 추가
                sub_fragments.append({
                    'id': str(uuid.uuid4()),
                    'type': 'function',
                    'name': func_name,
                    'content': self._normalize_code(func_code),
                    'metadata': {
                        'file_path': file_info['file_path'],
                        'file_name': file_info['file_name'],
                        'parent_id': parent_id,
                        'start_pos': func_start,
                        'length': len(func_code)
                    }
                })
        
        # 화살표 함수 추출 (이벤트 핸들러 등)
        arrow_func_pattern = re.compile(r'const\s+([a-z][a-zA-Z0-9]*)\s*=\s*(?:async\s*)?\(\s*.*?\)\s*=>\s*{')
        for match in arrow_func_pattern.finditer(component_code):
            func_start = match.start()
            func_name = match.group(1)
            func_code = self._extract_code_block(component_code, func_start)
            
            if func_code and len(func_code) >= self.min_function_size:  # 크기 체크 추가
                sub_fragments.append({
                    'id': str(uuid.uuid4()),
                    'type': 'function',
                    'name': func_name,
                    'content': self._normalize_code(func_code),
                    'metadata': {
                        'file_path': file_info['file_path'],
                        'file_name': file_info['file_name'],
                        'parent_id': parent_id,
                        'start_pos': func_start,
                        'length': len(func_code),
                        'function_type': 'arrow'
                    }
                })
        
        # useEffect 블록 추출 (상태 관리 로직)
        useeffect_pattern = re.compile(r'useEffect\(\s*\(\s*\)\s*=>\s*{')
        for match in useeffect_pattern.finditer(component_code):
            effect_start = match.start()
            effect_code = self._extract_effect_block(component_code, effect_start)
            
            if effect_code and len(effect_code) >= self.min_function_size:  # 크기 체크 추가
                dependencies = self._extract_effect_dependencies(effect_code)
                
                sub_fragments.append({
                    'id': str(uuid.uuid4()),
                    'type': 'state_logic',
                    'name': 'useEffect',
                    'content': self._normalize_code(effect_code),
                    'metadata': {
                        'file_path': file_info['file_path'],
                        'file_name': file_info['file_name'],
                        'parent_id': parent_id,
                        'start_pos': effect_start,
                        'length': len(effect_code),
                        'dependencies': dependencies
                    }
                })
        
        # JSX 요소 추출 (복잡한 JSX 구문 추출을 위한 간단한 접근법)
        jsx_pattern = re.compile(r'<([A-Z][a-zA-Z0-9]*)[^>]*>.*?</\1>', re.DOTALL)
        for match in jsx_pattern.finditer(component_code):
            jsx_start = match.start()
            jsx_name = match.group(1)
            jsx_code = match.group(0)
            
            # 일정 크기 이상의 JSX 요소만 파편화
            if len(jsx_code) >= self.min_jsx_size:  # 크기 체크 강화
                sub_fragments.append({
                    'id': str(uuid.uuid4()),
                    'type': 'jsx_element',
                    'name': jsx_name,
                    'content': self._normalize_code(jsx_code),
                    'metadata': {
                        'file_path': file_info['file_path'],
                        'file_name': file_info['file_name'],
                        'parent_id': parent_id,
                        'start_pos': jsx_start,
                        'length': len(jsx_code)
                    }
                })
        
        # Material UI 컴포넌트 사용 추출
        mui_matches = self.mui_component_pattern.finditer(component_code)
        for match in mui_matches:
            mui_start = match.start()
            mui_name = match.group(1)
            
            # 해당 JSX 요소 전체 추출 시도
            jsx_code = self._extract_jsx_element(component_code, mui_start)
            
            if jsx_code and len(jsx_code) >= self.min_jsx_size:  # 크기 체크 추가
                sub_fragments.append({
                    'id': str(uuid.uuid4()),
                    'type': 'mui_component',
                    'name': mui_name,
                    'content': self._normalize_code(jsx_code),
                    'metadata': {
                        'file_path': file_info['file_path'],
                        'file_name': file_info['file_name'],
                        'parent_id': parent_id,
                        'start_pos': mui_start,
                        'length': len(jsx_code),
                        'component_library': 'material-ui'
                    }
                })
        
        # 스타일 블록 추출
        style_pattern = re.compile(r'(const\s+styles\s*=\s*{|const\s+[a-zA-Z0-9]*Styles\s*=\s*{|sx\s*=\s*{)')
        for match in style_pattern.finditer(component_code):
            style_start = match.start()
            style_code = self._extract_code_block(component_code, style_start)
            
            if style_code and len(style_code) >= self.min_style_block_size:  # 크기 체크 추가
                sub_fragments.append({
                    'id': str(uuid.uuid4()),
                    'type': 'style_block',
                    'name': 'styles',
                    'content': self._normalize_code(style_code),
                    'metadata': {
                        'file_path': file_info['file_path'],
                        'file_name': file_info['file_name'],
                        'parent_id': parent_id,
                        'start_pos': style_start,
                        'length': len(style_code)
                    }
                })
                
        return sub_fragments
    
    def _extract_effect_block(self, code: str, start_pos: int) -> Optional[str]:
        """useEffect 블록 추출"""
        # useEffect(() => { ... }, [dependencies]) 형태 추출
        bracket_count = 0
        in_callback = False
        callback_end = None
        dependencies_start = None
        dependencies_end = None
        
        for i in range(start_pos, len(code)):
            if code[i] == '{' and not in_callback:
                bracket_count += 1
                in_callback = True
            elif code[i] == '{' and in_callback:
                bracket_count += 1
            elif code[i] == '}':
                bracket_count -= 1
                
            if in_callback and bracket_count == 0:
                callback_end = i + 1
                dependencies_start = code.find('[', callback_end)
                if dependencies_start > 0:
                    dependencies_end = code.find(']', dependencies_start)
                    if dependencies_end > 0:
                        return code[start_pos:dependencies_end + 1]
                    else:
                        return code[start_pos:callback_end]
                else:
                    return code[start_pos:callback_end]
        
        return None
    
    def _extract_effect_dependencies(self, effect_code: str) -> List[str]:
        """useEffect 의존성 배열 추출"""
        dependencies = []
        
        # 의존성 배열 찾기
        dep_match = re.search(r'\[(.*?)\]$', effect_code)
        if dep_match:
            deps_str = dep_match.group(1)
            # 쉼표로 구분된 의존성 추출
            dependencies = [d.strip() for d in deps_str.split(',') if d.strip()]
            
        return dependencies
    
    def _extract_jsx_element(self, code: str, start_pos: int) -> Optional[str]:
        """주어진 위치에서 JSX 요소 전체 추출"""
        # 태그 이름 추출
        tag_match = re.search(r'<([A-Z][a-zA-Z0-9]*)', code[start_pos:])
        if not tag_match:
            return None
            
        tag_name = tag_match.group(1)
        open_tags = 1
        current_pos = start_pos + tag_match.end()
        
        # 닫는 태그 찾기
        while current_pos < len(code) and open_tags > 0:
            open_tag_pos = code.find(f'<{tag_name}', current_pos)
            close_tag_pos = code.find(f'</{tag_name}>', current_pos)
            
            if close_tag_pos == -1:
                # 닫는 태그를 찾지 못함
                return None
                
            if open_tag_pos != -1 and open_tag_pos < close_tag_pos:
                open_tags += 1
                current_pos = open_tag_pos + 1
            else:
                open_tags -= 1
                current_pos = close_tag_pos + len(f'</{tag_name}>') if open_tags == 0 else close_tag_pos + 1
        
        if open_tags == 0:
            return code[start_pos:current_pos]
            
        return None
    
    def _extract_import_statements(self, code: str, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """import 문 블록 추출"""
        import_pattern = re.compile(r'^import.*?;$', re.MULTILINE)
        matches = list(import_pattern.finditer(code))
        
        if not matches:
            return None
            
        # 모든 import 문 결합
        imports_text = '\n'.join(code[m.start():m.end()] for m in matches)
        
        if imports_text:
            # 중요 라이브러리 사용 분석
            libraries = {
                'react': False,
                'react-router': False,
                'mui': False,
                'api': False,
                'hooks': False
            }
            
            if 'import React' in imports_text:
                libraries['react'] = True
            if 'react-router' in imports_text:
                libraries['react-router'] = True
            if '@mui/material' in imports_text:
                libraries['mui'] = True
            if 'services/api' in imports_text:
                libraries['api'] = True
            if 'contexts/' in imports_text or 'useAuth' in imports_text:
                libraries['hooks'] = True
            
            return {
                'id': str(uuid.uuid4()),
                'type': 'import_block',
                'name': 'imports',
                'content': imports_text,
                'metadata': {
                    'file_path': file_info['file_path'],
                    'file_name': file_info['file_name'],
                    'imports_count': len(matches),
                    'libraries': libraries
                }
            }
        
        return None
    
    def _extract_api_calls(self, code: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """API 호출 코드 파편 추출"""
        fragments = []
        
        # API 호출 패턴 매칭
        matches = self.api_call_pattern.finditer(code)
        
        for match in matches:
            api_code = match.group(0)
            api_start = match.start()
            
            # 함수 내부에서 호출되는 경우 문맥 파악
            context_start = max(0, api_start - 100)
            context_end = min(len(code), api_start + len(api_code) + 100)
            context_code = code[context_start:context_end]
            
            # API 이름 및 HTTP 메서드 추출
            api_parts = api_code.split('.')
            api_service = api_parts[0] if len(api_parts) > 0 else ""
            method = api_parts[1].split('(')[0] if len(api_parts) > 1 else ""
            
            fragments.append({
                'id': str(uuid.uuid4()),
                'type': 'api_call',
                'name': f"{api_service}.{method}",
                'content': context_code,
                'metadata': {
                    'file_path': file_info['file_path'],
                    'file_name': file_info['file_name'],
                    'api_service': api_service,
                    'http_method': method,
                    'context': api_code
                }
            })
        
        return fragments
    
    def _extract_routing_code(self, code: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """라우팅 관련 코드 파편 추출"""
        fragments = []
        
        # 라우팅 패턴 매칭
        matches = self.router_pattern.finditer(code)
        
        for match in matches:
            router_code = match.group(0)
            router_start = match.start()
            
            # 라우팅 컨텍스트 파악
            context_start = max(0, router_start - 50)
            context_end = min(len(code), router_start + len(router_code) + 150)
            context_code = code[context_start:context_end]
            
            # 중복 방지 (이미 추출된 컨텍스트인 경우 건너뛰기)
            if any(fragment['content'] == context_code for fragment in fragments):
                continue
            
            fragments.append({
                'id': str(uuid.uuid4()),
                'type': 'routing',
                'name': match.group(1),
                'content': context_code,
                'metadata': {
                    'file_path': file_info['file_path'],
                    'file_name': file_info['file_name'],
                    'router_api': match.group(1)
                }
            })
        
        return fragments
    
    def _fallback_fragmentation(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """파싱 실패 시 fallback 파편화 로직"""
        fragments = []
        file_info = parsed_file['file_info']
        code = parsed_file['raw_code']
        
        # 간단한 텍스트 기반 컴포넌트 추출
        component_pattern = re.compile(r'(function\s+([A-Z][a-zA-Z0-9]*)|class\s+([A-Z][a-zA-Z0-9]*)|const\s+([A-Z][a-zA-Z0-9]*)\s*=)')
        
        for match in component_pattern.finditer(code):
            start_pos = match.start()
            # 컴포넌트 이름 (세 개의 캡처 그룹 중 None이 아닌 것)
            name_groups = match.groups()[1:]  # 첫 번째는 전체 매치
            comp_name = next((g for g in name_groups if g is not None), "UnknownComponent")
            
            # 간단한 방법으로 코드 블록 추출
            comp_code = self._extract_code_block(code, start_pos)
            if not comp_code:
                # 추출 실패 시, 적당한 길이만큼만 추출
                comp_code = code[start_pos:min(start_pos + 500, len(code))]
            
            # 크기 체크 추가
            if len(comp_code) >= self.min_component_size:
                fragments.append({
                    'id': str(uuid.uuid4()),
                    'type': 'component',
                    'name': comp_name,
                    'content': self._normalize_code(comp_code),
                    'metadata': {
                        'file_path': file_info['file_path'],
                        'file_name': file_info['file_name'],
                        'start_pos': start_pos,
                        'length': len(comp_code),
                        'fallback_extraction': True
                    }
                })
            
        # import 문 추출 시도
        import_fragment = self._extract_import_statements(code, file_info)
        if import_fragment:
            fragments.append(import_fragment)
            
        # API 호출 추출 시도
        api_fragments = self._extract_api_calls(code, file_info)
        api_fragments = [f for f in api_fragments if len(f['content']) >= self.min_api_call_size]  # 크기 필터링
        fragments.extend(api_fragments)
        
        return fragments
    
    def _extract_code_block(self, code: str, start_pos: int) -> Optional[str]:
        """괄호 매칭을 통한 코드 블록 추출"""
        # { 기호 위치 찾기
        bracket_pos = code.find('{', start_pos)
        if bracket_pos == -1:
            return None
            
        # 괄호 매칭
        bracket_count = 1
        end_pos = bracket_pos + 1
        
        while bracket_count > 0 and end_pos < len(code):
            if code[end_pos] == '{':
                bracket_count += 1
            elif code[end_pos] == '}':
                bracket_count -= 1
            end_pos += 1
            
        if bracket_count == 0:
            return code[start_pos:end_pos]
        return None
    
    def _normalize_code(self, code: str) -> str:
        """코드 정규화: 주석 제거, 들여쓰기 정리"""
        # 주석 제거
        code = self.comments_pattern.sub('', code)
        # 과도한 공백 정규화
        code = self.whitespace_pattern.sub(' ', code)
        # 양쪽 공백 제거
        code = code.strip()
        return code
    
    def _detect_component_type(self, code: str) -> str:
        """컴포넌트 타입 감지 (함수형/클래스/메모/훅)"""
        if code.startswith('function'):
            return 'functional'
        elif code.startswith('class'):
            return 'class'
        elif 'React.memo' in code or 'memo(' in code:
            return 'memo'
        elif code.startswith('const') and 'use' in code[:20]:
            return 'hook'
        elif code.startswith('const') and '=>' in code[:50]:
            return 'arrow_function'
        else:
            return 'unknown'
            
    def fragment_project(self, parsed_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        파싱된 프로젝트 전체 파편화
        
        Args:
            parsed_project: parse_react_project()로 파싱된 프로젝트 정보
            
        Returns:
            Dict: 파편화 결과와 메타데이터
        """
        all_fragments = []
        file_stats = {}
        
        # 각 파일별로 파편화
        for file_path, parsed_file in parsed_project['parsed_files'].items():
            file_fragments = self.fragment_file(parsed_file)
            all_fragments.extend(file_fragments)
            
            # 파일별 통계
            file_stats[file_path] = {
                'fragments_count': len(file_fragments),
                'types': {}
            }
            
            # 파편 타입별 카운트
            for fragment in file_fragments:
                frag_type = fragment['type']
                if frag_type in file_stats[file_path]['types']:
                    file_stats[file_path]['types'][frag_type] += 1
                else:
                    file_stats[file_path]['types'][frag_type] = 1
        
        # 전체 파편 통계
        fragment_stats = self._calculate_fragment_stats(all_fragments)
        
        return {
            'fragments': all_fragments,
            'file_stats': file_stats,
            'fragment_stats': fragment_stats
        }
        
    def _calculate_fragment_stats(self, fragments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        파편 통계 계산
        
        Args:
            fragments: 모든 파편 목록
            
        Returns:
            Dict: 통계 정보
        """
        stats = {
            'total_count': len(fragments),
            'by_type': {},
            'by_component_type': {},
            'by_category': {},
            'by_purpose': {}
        }
        
        for fragment in fragments:
            # 타입별 통계
            frag_type = fragment['type']
            if frag_type in stats['by_type']:
                stats['by_type'][frag_type] += 1
            else:
                stats['by_type'][frag_type] = 1
                
            # 컴포넌트 타입별 통계 (컴포넌트인 경우만)
            if frag_type == 'component' and 'component_type' in fragment['metadata']:
                comp_type = fragment['metadata']['component_type']
                if comp_type in stats['by_component_type']:
                    stats['by_component_type'][comp_type] += 1
                else:
                    stats['by_component_type'][comp_type] = 1
                    
            # 카테고리별 통계
            if 'category' in fragment['metadata']:
                category = fragment['metadata']['category']
                if category in stats['by_category']:
                    stats['by_category'][category] += 1
                else:
                    stats['by_category'][category] = 1
                    
            # 목적별 통계
            if 'purpose' in fragment['metadata']:
                purpose = fragment['metadata']['purpose']
                if purpose in stats['by_purpose']:
                    stats['by_purpose'][purpose] += 1
                else:
                    stats['by_purpose'][purpose] = 1
                    
        return stats