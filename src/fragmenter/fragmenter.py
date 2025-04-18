"""
코드 파편화(Fragmentation) 모듈
"""

import re
import uuid
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
            'import_block'    # import 문 블록
        ]
        
        # 정규화 및 필터링 패턴
        self.whitespace_pattern = re.compile(r'\s+')
        self.comments_pattern = re.compile(r'//.*?$|/\*.*?\*/', re.MULTILINE | re.DOTALL)
        
    def fragment_file(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        파싱된 파일에서 의미 있는 코드 파편들을 추출
        
        Args:
            parsed_file: JSXParser로 파싱된 파일 정보
            
        Returns:
            List[Dict]: 추출된 코드 파편 목록
        """
        fragments = []
        
        # 파싱 오류가 있는 경우 처리
        if 'error' in parsed_file:
            # 간단한 텍스트 기반 파편화 시도
            fragments.extend(self._fallback_fragmentation(parsed_file))
            return fragments
        
        # 컴포넌트 파편화
        for component in parsed_file.get('components', []):
            fragment = self._create_component_fragment(component, parsed_file['file_info'])
            fragments.append(fragment)
            
            # 컴포넌트 내부 함수 및 JSX 요소 추가 파편화
            sub_fragments = self._extract_subfragments(component['code'], fragment['id'], parsed_file['file_info'])
            fragments.extend(sub_fragments)
        
        # import 문 파편화
        import_fragment = self._extract_import_statements(parsed_file['raw_code'], parsed_file['file_info'])
        if import_fragment:
            fragments.append(import_fragment)
        
        return fragments
    
    def _create_component_fragment(self, component: Dict[str, Any], file_info: Dict[str, Any]) -> Dict[str, Any]:
        """컴포넌트 파편 생성"""
        # 코드 정규화
        code = self._normalize_code(component['code'])
        
        return {
            'id': str(uuid.uuid4()),
            'type': 'component',
            'name': component['name'],
            'content': code,
            'metadata': {
                'file_path': file_info['file_path'],
                'file_name': file_info['file_name'],
                'start_pos': component['start_pos'],
                'length': len(component['code']),
                'component_type': self._detect_component_type(code)
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
            
            if func_code:
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
        
        # JSX 요소 추출 (복잡한 JSX 구문 추출을 위한 간단한 접근법)
        jsx_pattern = re.compile(r'<([A-Z][a-zA-Z0-9]*)[^>]*>.*?</\1>', re.DOTALL)
        for match in jsx_pattern.finditer(component_code):
            jsx_start = match.start()
            jsx_name = match.group(1)
            jsx_code = match.group(0)
            
            # 일정 크기 이상의 JSX 요소만 파편화
            if len(jsx_code) > 50:  # 크기 기준은 필요에 따라 조정
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
        
        # 스타일 블록 추출
        style_pattern = re.compile(r'(const\s+styles\s*=\s*{|const\s+[a-zA-Z0-9]*Styles\s*=\s*{)')
        for match in style_pattern.finditer(component_code):
            style_start = match.start()
            style_code = self._extract_code_block(component_code, style_start)
            
            if style_code:
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
    
    def _extract_import_statements(self, code: str, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """import 문 블록 추출"""
        import_pattern = re.compile(r'^import.*?;$', re.MULTILINE)
        matches = list(import_pattern.finditer(code))
        
        if not matches:
            return None
            
        # 모든 import 문 결합
        imports_text = '\n'.join(code[m.start():m.end()] for m in matches)
        
        if imports_text:
            return {
                'id': str(uuid.uuid4()),
                'type': 'import_block',
                'name': 'imports',
                'content': imports_text,
                'metadata': {
                    'file_path': file_info['file_path'],
                    'file_name': file_info['file_name'],
                    'imports_count': len(matches)
                }
            }
        
        return None
    
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
        fragment_stats = {
            'total_count': len(all_fragments),
            'by_type': {},
            'by_component_type': {}
        }
        
        for fragment in all_fragments:
            # 타입별 통계
            frag_type = fragment['type']
            if frag_type in fragment_stats['by_type']:
                fragment_stats['by_type'][frag_type] += 1
            else:
                fragment_stats['by_type'][frag_type] = 1
                
            # 컴포넌트 타입별 통계 (컴포넌트인 경우만)
            if frag_type == 'component' and 'component_type' in fragment['metadata']:
                comp_type = fragment['metadata']['component_type']
                if comp_type in fragment_stats['by_component_type']:
                    fragment_stats['by_component_type'][comp_type] += 1
                else:
                    fragment_stats['by_component_type'][comp_type] = 1
        
        return {
            'fragments': all_fragments,
            'file_stats': file_stats,
            'fragment_stats': fragment_stats
        }