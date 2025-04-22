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
            'script',       # 스크립트 섹션
            'style'         # 스타일 섹션
        ]
    
    def fragment_file(self, parsed_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        파싱된 Vue 파일에서 의미 있는 코드 파편들을 추출
        
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
        component_name = parsed_file['component_name']
        
        # 1. 컴포넌트 전체 파편화
        component_id = str(uuid.uuid4())
        component_fragment = self._create_fragment(
            fragment_id=component_id,
            fragment_type='component',
            name=component_name,
            content=parsed_file['raw_content'],
            metadata={
                'file_path': file_info['file_path'],
                'file_name': file_info['file_name'],
                'component_name': component_name,
                'has_template': parsed_file['template'] is not None,
                'has_script': parsed_file['script'] is not None,
                'has_style': parsed_file['style'] is not None,
                'props': parsed_file['props'],
                'components': parsed_file['components']
            }
        )
        fragments.append(component_fragment)
        
        # 2. 템플릿 섹션 파편화
        if parsed_file['template']:
            template_fragment = self._create_fragment(
                fragment_id=str(uuid.uuid4()),
                fragment_type='template',
                name=f"{component_name}-template",
                content=f"<template>{parsed_file['template']}</template>",
                metadata={
                    'file_path': file_info['file_path'],
                    'file_name': file_info['file_name'],
                    'component_name': component_name,
                    'parent_id': component_id
                }
            )
            fragments.append(template_fragment)
        
        # 3. 스크립트 섹션 파편화
        if parsed_file['script']:
            script_fragment = self._create_fragment(
                fragment_id=str(uuid.uuid4()),
                fragment_type='script',
                name=f"{component_name}-script",
                content=f"<script>{parsed_file['script']}</script>",
                metadata={
                    'file_path': file_info['file_path'],
                    'file_name': file_info['file_name'],
                    'component_name': component_name,
                    'props': parsed_file['props'],
                    'components': parsed_file['components'],
                    'parent_id': component_id
                }
            )
            fragments.append(script_fragment)
        
        # 4. 스타일 섹션 파편화
        if parsed_file['style']:
            style_fragment = self._create_fragment(
                fragment_id=str(uuid.uuid4()),
                fragment_type='style',
                name=f"{component_name}-style",
                content=f"<style>{parsed_file['style']}</style>",
                metadata={
                    'file_path': file_info['file_path'],
                    'file_name': file_info['file_name'],
                    'component_name': component_name,
                    'parent_id': component_id
                }
            )
            fragments.append(style_fragment)
        
        return fragments
    
    def fragment_project(self, parsed_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        파싱된 프로젝트 전체 파편화
        
        Args:
            parsed_project: parse_vue_project()로 파싱된 프로젝트 정보
            
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
                'types': self._count_fragment_types(file_fragments)
            }
        
        # 전체 파편 통계
        fragment_stats = self._calculate_fragment_stats(all_fragments)
        
        return {
            'fragments': all_fragments,
            'file_stats': file_stats,
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