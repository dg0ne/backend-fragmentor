"""
향상된 코드 파편화(Fragmentation) 모듈 - React 프로젝트용
"""

from typing import List, Dict, Any, Tuple, Optional

from app.fragmentation.base import FragmenterStrategy
from app.fragmentation.extractors import (
    ComponentExtractor, 
    FunctionExtractor, 
    JSXExtractor,
    APICallExtractor,
    MUIExtractor,
    ImportExtractor,
    StateLogicExtractor,
    RoutingExtractor
)

class ReactFragmenter(FragmenterStrategy):
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
        
        # 추출기 초기화
        self.extractors = {
            'component': ComponentExtractor(),
            'function': FunctionExtractor(),
            'jsx_element': JSXExtractor(),
            'api_call': APICallExtractor(),
            'mui_component': MUIExtractor(),
            'import_block': ImportExtractor(),
            'state_logic': StateLogicExtractor(),
            'routing': RoutingExtractor()
        }
    
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
        raw_code = parsed_file['raw_code']
        
        # 1. Import 문 추출 (파일 맨 위 부분)
        import_fragments = self.extractors['import_block'].extract(raw_code, file_info)
        fragments.extend(import_fragments)
        
        # 2. 컴포넌트 추출
        component_fragments = self.extractors['component'].extract(raw_code, file_info)
        fragments.extend(component_fragments)
        
        # 3. 컴포넌트 내부 함수 및 JSX 요소 추가 파편화
        for component in parsed_file.get('components', []):
            component_code = component['code']
            component_id = None
            
            # 해당 컴포넌트의 ID 찾기
            for fragment in component_fragments:
                if fragment['name'] == component['name']:
                    component_id = fragment['id']
                    break
            
            if component_id:
                # 내부 함수 추출
                function_fragments = self.extractors['function'].extract(component_code, file_info, component_id)
                fragments.extend(function_fragments)
                
                # JSX 요소 추출
                jsx_fragments = self.extractors['jsx_element'].extract(component_code, file_info, component_id)
                fragments.extend(jsx_fragments)
                
                # MUI 컴포넌트 추출
                mui_fragments = self.extractors['mui_component'].extract(component_code, file_info, component_id)
                fragments.extend(mui_fragments)
                
                # 상태 관리 로직 추출
                state_fragments = self.extractors['state_logic'].extract(component_code, file_info, component_id)
                fragments.extend(state_fragments)
                
                # 라우팅 로직 추출
                routing_fragments = self.extractors['routing'].extract(component_code, file_info, component_id)
                fragments.extend(routing_fragments)
        
        # 4. 컴포넌트 외부의 JSX 요소 추출 (주로 App.js 또는 index.js)
        for jsx_element in parsed_file.get('jsx_elements', []):
            # 이미 컴포넌트의 일부로 파편화된 것 건너뛰기
            is_already_fragmented = False
            for component in parsed_file.get('components', []):
                if jsx_element['start_pos'] >= component['start_pos'] and \
                   jsx_element['start_pos'] < component['start_pos'] + len(component['code']):
                    is_already_fragmented = True
                    break
                    
            if not is_already_fragmented:
                jsx_fragments = self.extractors['jsx_element'].extract(
                    jsx_element['code'], 
                    file_info
                )
                fragments.extend(jsx_fragments)
        
        # 5. 커스텀 훅 추출 (특별 처리)
        # 커스텀 훅은 기본 컴포넌트 추출기에서는 잡히지 않을 수 있음
        for hook in parsed_file.get('hooks', []):
            if hook['type'] == 'custom':  # 커스텀 훅만 독립 파편으로
                # 훅은 함수형 컴포넌트와 유사하므로 컴포넌트 추출기 재사용
                hook_fragments = self.extractors['component'].extract(
                    hook['code'], 
                    file_info
                )
                
                # 타입을 'hook'으로 변경
                for fragment in hook_fragments:
                    fragment['type'] = 'hook'
                    
                fragments.extend(hook_fragments)
        
        # 6. 글로벌 API 호출 추출
        api_fragments = self.extractors['api_call'].extract(raw_code, file_info)
        fragments.extend(api_fragments)
        
        # 7. 글로벌 라우팅 코드 추출
        routing_fragments = self.extractors['routing'].extract(raw_code, file_info)
        fragments.extend(routing_fragments)
        
        # 중복 제거 (동일 content와 type의 파편들)
        deduplicated_fragments = self._remove_duplicates(fragments)
        
        return deduplicated_fragments
    
    def _fallback_fragmentation(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        파싱 실패 시 fallback 파편화 로직
        
        Args:
            parsed_file: 파싱 실패한 파일 정보
            
        Returns:
            List[Dict[str, Any]]: 추출된 파편 목록
        """
        # 파싱은 실패했지만 raw_code는 있으므로 간단한 텍스트 기반 파편화 시도
        file_info = parsed_file['file_info']
        code = parsed_file['raw_code']
        fragments = []
        
        # 각 추출기를 사용하여 코드 파편화 시도
        for extractor_name, extractor in self.extractors.items():
            try:
                # 추출 시도
                extracted_fragments = extractor.extract(code, file_info)
                fragments.extend(extracted_fragments)
            except Exception as e:
                print(f"Fallback 추출 오류 ({extractor_name}): {str(e)}")
                continue
        
        # 중복 제거
        return self._remove_duplicates(fragments)
    
    def _remove_duplicates(self, fragments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        중복 파편 제거
        
        Args:
            fragments: 모든 파편 목록
            
        Returns:
            List[Dict[str, Any]]: 중복이 제거된 파편 목록
        """
        unique_fragments = []
        content_type_set = set()  # (content, type) 튜플을 저장하는 집합
        
        for fragment in fragments:
            # content와 type을 기준으로 중복 체크
            content_type = (fragment['content'], fragment['type'])
            
            if content_type not in content_type_set:
                content_type_set.add(content_type)
                unique_fragments.append(fragment)
        
        return unique_fragments
    
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