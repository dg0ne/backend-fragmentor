"""
Vue 코드 파편화 모듈
"""

import uuid
from typing import Dict, List, Any, Optional

class VueFragmenter:
    """Vue 코드를 의미 단위로 파편화하는 클래스"""
    
    def __init__(self):
        # 파편화 타입
        self.fragment_types = [
            'component',    # Vue 컴포넌트 전체
            'template',     # 템플릿 섹션
            'script',       # Vue 파일의 스크립트 섹션
            'style',        # Vue 파일의 스타일 섹션
            'javascript',   # 독립 JS 파일
            'css',          # 독립 CSS 파일
            'html',         # HTML 파일
            'config',       # 설정 파일 (json, yaml 등)
            'generic'       # 기타 파일
        ]
    
    def fragment_file(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        파싱된 파일에서 의미 있는 코드 파편들을 추출
        
        Args:
            parsed_file: VueParser로 파싱된 파일 정보
            
        Returns:
            List[Dict]: 추출된 코드 파편 목록
        """
        fragments = []
        
        # 무시된 파일이거나 파싱 오류가 있는 경우 처리
        if parsed_file.get('ignored', False) or 'error' in parsed_file:
            return fragments
            
        file_info = parsed_file['file_info']
        file_extension = file_info['extension'].lower()
        
        # 파일 확장자에 따라 다른 파편화 전략 적용
        if file_extension == '.vue':
            return self._fragment_vue_file(parsed_file)
        elif file_extension in ['.js', '.ts']:
            return self._fragment_js_file(parsed_file)
        elif file_extension == '.css':
            return self._fragment_css_file(parsed_file)
        elif file_extension == '.html':
            return self._fragment_html_file(parsed_file)
        else:
            # 기타 파일은 전체를 하나의 파편으로 처리
            return self._fragment_generic_file(parsed_file)
    
    def _fragment_vue_file(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Vue SFC 파일 파편화"""
        fragments = []
        file_info = parsed_file['file_info']
        component_name = parsed_file.get('component_name', 
                                    file_info['file_name'].replace('.vue', ''))
        
        # 1. 컴포넌트 전체 파편
        component_fragment = self._create_fragment(
            fragment_id=str(uuid.uuid4()),
            fragment_type='component',
            name=component_name,
            content=parsed_file['raw_content'],
            metadata={
                'file_path': file_info['file_path'],
                'file_name': file_info['file_name'],
                'component_name': component_name,
                'props': parsed_file.get('props', []),
                'components': parsed_file.get('components', [])
            }
        )
        fragments.append(component_fragment)
        
        # 2. 템플릿 섹션 파편화 - 태그 포함
        if parsed_file.get('template'):
            template_content = f"<template>\n{parsed_file['template']}\n</template>"
            template_fragment = self._create_fragment(
                fragment_id=str(uuid.uuid4()),
                fragment_type='template',
                name=f"{component_name}_template",
                content=template_content,
                metadata={
                    'component_name': component_name,
                    'file_path': file_info['file_path'],
                    'file_name': file_info['file_name']
                }
            )
            fragments.append(template_fragment)
        
        # 3. 스크립트 섹션 파편화 - 태그 포함
        if parsed_file.get('script'):
            script_content = f"<script>\n{parsed_file['script']}\n</script>"
            script_fragment = self._create_fragment(
                fragment_id=str(uuid.uuid4()),
                fragment_type='script',
                name=f"{component_name}_script",
                content=script_content,
                metadata={
                    'component_name': component_name,
                    'file_path': file_info['file_path'],
                    'file_name': file_info['file_name'],
                    'props': parsed_file.get('props', []),
                    'components': parsed_file.get('components', [])
                }
            )
            fragments.append(script_fragment)
        
        # 4. 스타일 섹션 파편화 - 태그 포함
        if parsed_file.get('style'):
            style_content = f"<style scoped>\n{parsed_file['style']}\n</style>"
            style_fragment = self._create_fragment(
                fragment_id=str(uuid.uuid4()),
                fragment_type='style',
                name=f"{component_name}_style",
                content=style_content,
                metadata={
                    'component_name': component_name,
                    'file_path': file_info['file_path'],
                    'file_name': file_info['file_name']
                }
            )
            fragments.append(style_fragment)
        
        return fragments

    def _fragment_js_file(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """JS 파일을 javascript 타입으로 파편화 - 태그 없음"""
        fragments = []
        file_info = parsed_file['file_info']
        
        # 독립 JS 파일은 태그 없이 원본 내용 그대로 사용
        js_fragment = self._create_fragment(
            fragment_id=str(uuid.uuid4()),
            fragment_type='javascript',
            name=file_info['file_name'],
            content=parsed_file['raw_content'],
            metadata={
                'file_path': file_info['file_path'],
                'file_name': file_info['file_name'],
                'extension': file_info['extension']
            }
        )
        fragments.append(js_fragment)
        return fragments

    def _fragment_css_file(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """CSS 파일을 css 타입으로 파편화 - 태그 없음"""
        fragments = []
        file_info = parsed_file['file_info']
        
        # 독립 CSS 파일은 태그 없이 원본 내용 그대로 사용
        css_fragment = self._create_fragment(
            fragment_id=str(uuid.uuid4()),
            fragment_type='css',
            name=file_info['file_name'],
            content=parsed_file['raw_content'],
            metadata={
                'file_path': file_info['file_path'],
                'file_name': file_info['file_name'],
                'extension': file_info['extension']
            }
        )
        fragments.append(css_fragment)
        return fragments

    def _fragment_html_file(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """HTML 파일을 html 타입으로 파편화 - 태그 없음"""
        fragments = []
        file_info = parsed_file['file_info']
        
        # HTML 파일은 이미 태그를 포함하고 있으므로 원본 사용
        html_fragment = self._create_fragment(
            fragment_id=str(uuid.uuid4()),
            fragment_type='html',  # 'template' 대신 'html' 타입으로 명확히 구분
            name=file_info['file_name'],
            content=parsed_file['raw_content'],
            metadata={
                'file_path': file_info['file_path'],
                'file_name': file_info['file_name'],
                'file_type': 'html',
                'extension': file_info['extension']
            }
        )
        fragments.append(html_fragment)
        return fragments

    def _fragment_generic_file(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """기타 파일 전체를 하나의 파편으로 처리"""
        fragments = []
        file_info = parsed_file['file_info']
        
        generic_fragment = self._create_fragment(
            fragment_id=str(uuid.uuid4()),
            fragment_type='generic',
            name=file_info['file_name'],
            content=parsed_file['raw_content'],
            metadata={
                'file_path': file_info['file_path'],
                'file_name': file_info['file_name'],
                'extension': file_info['extension']
            }
        )
        fragments.append(generic_fragment)
        return fragments

    def fragment_file(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        파싱된 파일에서 의미 있는 코드 파편들을 추출
        
        Args:
            parsed_file: VueParser로 파싱된 파일 정보
            
        Returns:
            List[Dict]: 추출된 코드 파편 목록
        """
        fragments = []
        
        # 무시된 파일이거나 파싱 오류가 있는 경우 처리
        if parsed_file.get('ignored', False) or 'error' in parsed_file:
            return fragments
            
        file_info = parsed_file['file_info']
        file_extension = file_info['extension'].lower()
        
        # 파일 확장자에 따라 다른 파편화 전략 적용
        if file_extension == '.vue':
            return self._fragment_vue_file(parsed_file)
        elif file_extension in ['.js', '.ts']:
            return self._fragment_js_file(parsed_file)
        elif file_extension == '.css':
            return self._fragment_css_file(parsed_file)
        elif file_extension == '.html':
            return self._fragment_html_file(parsed_file)
        else:
            # 기타 파일은 전체를 하나의 파편으로 처리
            return self._fragment_generic_file(parsed_file)
    
    def fragment_project(self, parsed_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        프로젝트 전체의 코드를 파편화
        
        Args:
            parsed_project: VueParser로 파싱된 프로젝트 정보
            
        Returns:
            Dict: 파편화 결과 및 통계
        """
        all_fragments = []
        file_fragment_counts = {}
        
        # 파싱된 파일별로 파편화 수행
        for file_path, parsed_file in parsed_project['parsed_files'].items():
            fragments = self.fragment_file(parsed_file)
            all_fragments.extend(fragments)
            file_fragment_counts[file_path] = len(fragments)
        
        # 통계 계산
        fragment_stats = self._calculate_fragment_stats(all_fragments)
        fragment_stats['by_file'] = file_fragment_counts
        
        return {
            'fragments': all_fragments,
            'fragment_stats': fragment_stats
        }

    def _create_fragment(self, 
                        fragment_id: str,
                        fragment_type: str,
                        name: str,
                        content: str,
                        metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        표준화된 파편 객체 생성
        
        Args:
            fragment_id: 파편 ID
            fragment_type: 파편 유형 (component, template 등)
            name: 파편 이름
            content: 파편 코드 내용
            metadata: 파편 메타데이터
            
        Returns:
            Dict: 생성된 파편 객체
        """
        return {
            'id': fragment_id,
            'type': fragment_type,
            'name': name,
            'content': content,
            'metadata': metadata
        }
    
    def _count_fragment_types(self, fragments: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        파편 타입별 개수 계산
        
        Args:
            fragments: 파편 목록
            
        Returns:
            Dict[str, int]: 타입별 개수
        """
        type_counts = {}
        for fragment in fragments:
            frag_type = fragment['type']
            if frag_type in type_counts:
                type_counts[frag_type] += 1
            else:
                type_counts[frag_type] = 1
        return type_counts
    
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
            'by_type': self._count_fragment_types(fragments),
            'by_component_type': {},
            'has_props': 0,
            'has_components': 0
        }
        
        # 추가 통계
        for fragment in fragments:
            # 프로퍼티가 있는 컴포넌트 수
            if fragment['type'] == 'component' and fragment['metadata'].get('props', []):
                stats['has_props'] += 1
                
            # 하위 컴포넌트를 사용하는 컴포넌트 수
            if fragment['type'] == 'component' and fragment['metadata'].get('components', []):
                stats['has_components'] += 1
                
        return stats