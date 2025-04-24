"""
Vue SFC(Single File Component) 파싱 모듈
"""

import os
import re
import json
from typing import Dict, List, Any, Optional

class VueParser:
    """Vue 파일 파싱을 위한 클래스"""
    
    def __init__(self):
        # 무시할 디렉토리 패턴
        self.ignore_patterns = [
            r'\.git',
            r'node_modules',
            r'\.idea',
            r'build',
            r'dist',
            r'\.env'
        ]
        
        # Vue 컴포넌트의 섹션 추출을 위한 정규 표현식
        self.template_pattern = re.compile(r'<template>(.*?)</template>', re.DOTALL)
        self.script_pattern = re.compile(r'<script>(.*?)</script>', re.DOTALL)
        self.style_pattern = re.compile(r'<style.*?>(.*?)</style>', re.DOTALL)
        
        # 컴포넌트 이름 추출 패턴 
        self.component_name_pattern = re.compile(r'name:\s*[\'"]([^\'"]+)[\'"]')
        
        # props 추출 패턴
        self.props_pattern = re.compile(r'props:\s*{([^}]+)}', re.DOTALL)
        self.props_array_pattern = re.compile(r'props:\s*\[(.*?)\]', re.DOTALL)
        
        # 컴포넌트 추출 패턴
        self.components_pattern = re.compile(r'components:\s*{([^}]+)}', re.DOTALL)
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        파일을 파싱하여 구조화된 정보 추출
        """
        if not os.path.exists(file_path):
            return {
                'error': f"파일을 찾을 수 없습니다: {file_path}",
                'file_info': self._extract_file_info(file_path)
            }
        
        # 무시해야 할 파일인지 확인
        if self._should_ignore_file(file_path):
            return {
                'ignored': True,
                'file_info': self._extract_file_info(file_path)
            }
        
        try:
            # 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 파일 정보 추출
            file_info = self._extract_file_info(file_path)
            
            # Vue 컴포넌트 섹션별 추출
            if file_path.endswith('.vue'):
                template = self._extract_template(content)
                script = self._extract_script(content)
                style = self._extract_style(content)

                # 컴포넌트 이름 추출
                component_name = self._extract_component_name(script, file_info['file_name'])
                
                # Props 추출
                props = self._extract_props(script)
                
                # Components 추출
                components = self._extract_components(script)
                
                # 결과 조합
                result = {
                    'file_info': file_info,
                    'component_name': component_name,
                    'template': template,
                    'script': script,
                    'style': style,
                    'props': props,
                    'components': components,
                    'raw_content': content
                }
                
                return result
            else:
                # JS/TS/기타 파일은 전체 내용을 저장
                return {
                    'file_info': file_info,
                    'raw_content': content  
                }
            
        except Exception as e:
            return {
                'error': f"파싱 오류: {str(e)}",
                'file_info': self._extract_file_info(file_path)
            }
    
    def parse_project(self, project_path: str) -> Dict[str, Any]:
        """
        프로젝트 전체 파싱
        
        Args:
            project_path: 프로젝트 경로
            
        Returns:
            Dict: 프로젝트 파싱 결과
        """
        if not os.path.exists(project_path):
            return {
                'error': f"프로젝트 경로를 찾을 수 없습니다: {project_path}",
                'path': project_path
            }
        
        parsed_files = {}
        file_extensions = {}
        components_count = 0
        
        try:
            for root, _, files in os.walk(project_path):
                for file in files:
                    if file.endswith(('.vue', '.js', '.ts', '.css')):
                        file_path = os.path.join(root, file)
                        
                        # 무시해야 할 파일 건너뛰기
                        if self._should_ignore_file(file_path):
                            continue
                            
                        # 확장자 통계
                        ext = os.path.splitext(file)[1]
                        file_extensions[ext] = file_extensions.get(ext, 0) + 1
                        
                        # 파일 파싱
                        parsed_file = self.parse_file(file_path)
                        parsed_files[file_path] = parsed_file
                        
                        # 컴포넌트 카운트
                        if 'error' not in parsed_file and 'ignored' not in parsed_file:
                            components_count += 1
            
            # 요약 정보
            summary = {
                'total_files': len(parsed_files),
                'components_count': components_count,
                'file_extensions': file_extensions
            }
            
            return {
                'parsed_files': parsed_files,
                'summary': summary,
                'path': project_path
            }
            
        except Exception as e:
            return {
                'error': f"프로젝트 파싱 오류: {str(e)}",
                'path': project_path
            }
    
    def _extract_file_info(self, file_path: str) -> Dict[str, Any]:
        """파일 기본 정보 추출"""
        return {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'extension': os.path.splitext(file_path)[1],
            'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        }
    
    def _should_ignore_file(self, file_path: str) -> bool:
        """무시해야 할 파일인지 확인"""
        for pattern in self.ignore_patterns:
            if re.search(pattern, file_path):
                return True
        return False
    
    def _extract_template(self, content: str) -> Optional[str]:
        """템플릿 섹션 추출"""
        match = self.template_pattern.search(content)
        return match.group(1).strip() if match else None
    
    def _extract_script(self, content: str) -> Optional[str]:
        """스크립트 섹션 추출"""
        match = self.script_pattern.search(content)
        return match.group(1).strip() if match else None
    
    def _extract_style(self, content: str) -> Optional[str]:
        """스타일 섹션 추출"""
        match = self.style_pattern.search(content)
        return match.group(1).strip() if match else None
    
    def _extract_component_name(self, script: Optional[str], file_name: str) -> str:
        """컴포넌트 이름 추출"""
        if not script:
            # 스크립트가 없으면 파일 이름을 기반으로 이름 생성
            return os.path.splitext(file_name)[0]
            
        match = self.component_name_pattern.search(script)
        if match:
            return match.group(1)
        else:
            # 이름을 찾을 수 없으면 파일 이름을 기반으로 이름 생성
            return os.path.splitext(file_name)[0]
    
    def _extract_props(self, script: Optional[str]) -> List[str]:
        """props 목록 추출"""
        if not script:
            return []
            
        # 객체 형식 props
        props_match = self.props_pattern.search(script)
        if props_match:
            props_str = props_match.group(1)
            # 간단한 정규식으로 prop 이름만 추출
            prop_names = re.findall(r'(\w+)\s*:', props_str)
            return prop_names
            
        # 배열 형식 props
        props_array_match = self.props_array_pattern.search(script)
        if props_array_match:
            props_str = props_array_match.group(1)
            # 문자열 리터럴 추출
            prop_names = re.findall(r'[\'"]([^\'"]+)[\'"]', props_str)
            return prop_names
            
        return []
    
    def _extract_components(self, script: Optional[str]) -> List[str]:
        """사용된 컴포넌트 이름 추출"""
        if not script:
            return []
            
        components_match = self.components_pattern.search(script)
        if components_match:
            components_str = components_match.group(1)
            # 컴포넌트 이름 추출
            component_names = re.findall(r'(\w+)\s*:', components_str)
            return component_names
            
        return []


def parse_vue_project(project_path: str) -> Dict[str, Any]:
    """
    Vue 프로젝트 전체 파싱 헬퍼 함수
    
    Args:
        project_path: Vue 프로젝트 디렉토리 경로
        
    Returns:
        Dict: 파싱 결과 및 요약 정보
    """
    parser = VueParser()
    print(f"Vue Todo 프로젝트 파싱 중: {project_path}")
    return parser.parse_project(project_path)