"""
향상된 React/JSX 코드 파싱 모듈 - lifesub-web 프로젝트용
"""

import os
import re
import json
from typing import Dict, List, Any, Tuple, Optional
import esprima
from esprima import parseModule

from app.parser.base import CodeParser
from app.parser.utils import (
    get_ignore_patterns, 
    should_ignore_file, 
    get_file_content,
    MUI_IMPORT_PATTERN
)
from app.parser.models import ParsedFile, FileInfo, MUIUsage, ParsedProject, ProjectSummary
from app.parser.processors import (
    ComponentProcessor,
    HookProcessor,
    JSXProcessor,
    ImportProcessor,
    LifesubMetadataExtractor
)

class EnhancedJSXParser(CodeParser):
    """lifesub-web 프로젝트의 React JSX 코드를 파싱하는 클래스"""
    
    def __init__(self):
        # 프로세서 초기화
        self.component_processor = ComponentProcessor()
        self.hook_processor = HookProcessor()
        self.jsx_processor = JSXProcessor()
        self.import_processor = ImportProcessor()
        self.metadata_extractor = LifesubMetadataExtractor()
        
        # 파일 필터 패턴
        self.ignore_patterns = get_ignore_patterns()
    
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
        if should_ignore_file(file_path, self.ignore_patterns):
            return ParsedFile.create_ignored(file_path).to_dict()
        
        # 파일 읽기
        try:
            code = get_file_content(file_path)
        except Exception as e:
            return ParsedFile.create_error(
                file_path, 
                f"파일 읽기 오류: {str(e)}"
            ).to_dict()
        
        # 파일 메타데이터 추출
        file_info = self.metadata_extractor.extract_file_metadata(file_path, code)
        
        try:
            # AST 파싱 시도
            ast = parseModule(code, jsx=True, tolerant=True)
            
            # 컴포넌트 식별
            components = self.component_processor.process(code, file_info)
            
            # 훅 식별
            hooks = self.hook_processor.process(code, file_info)
            
            # JSX 요소 식별
            jsx_elements = self.jsx_processor.process(code, file_info)
            
            # MUI 컴포넌트 사용 감지
            mui_usage = self._detect_mui_usage(code)
            
            # 임포트 분석
            imports = self.import_processor.process(code, file_info)
            
            # 각 컴포넌트에 메타데이터 추가
            for component in components:
                component_metadata = self.metadata_extractor.extract_component_metadata(
                    component, file_info
                )
                component.update(component_metadata)
            
            # ParsedFile 객체 생성
            parsed_file = ParsedFile(
                file_info=FileInfo(**file_info),
                ast=ast,
                raw_code=code,
                components=components,
                hooks=hooks,
                jsx_elements=jsx_elements,
                mui_components=MUIUsage(**mui_usage) if isinstance(mui_usage, dict) else mui_usage
            )
            
            return parsed_file.to_dict()
            
        except Exception as e:
            # 파싱 오류 발생 시
            return ParsedFile.create_error(file_path, f"파싱 오류: {str(e)}", code).to_dict()
    
    def parse_code(self, code: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        코드 문자열 파싱
        
        Args:
            code: 파싱할 코드 문자열
            file_info: 파일 메타데이터
            
        Returns:
            Dict[str, Any]: 파싱 결과
        """
        try:
            # AST 파싱 시도
            ast = parseModule(code, jsx=True, tolerant=True)
            
            # 컴포넌트 식별
            components = self.component_processor.process(code, file_info)
            
            # 훅 식별
            hooks = self.hook_processor.process(code, file_info)
            
            # JSX 요소 식별
            jsx_elements = self.jsx_processor.process(code, file_info)
            
            # MUI 컴포넌트 사용 감지
            mui_usage = self._detect_mui_usage(code)
            
            # 각 컴포넌트에 메타데이터 추가
            for component in components:
                component_metadata = self.metadata_extractor.extract_component_metadata(
                    component, file_info
                )
                component.update(component_metadata)
            
            # 결과 반환
            return {
                'file_info': file_info,
                'ast': ast,
                'components': components,
                'hooks': hooks,
                'jsx_elements': jsx_elements,
                'mui_components': mui_usage,
                'raw_code': code
            }
            
        except Exception as e:
            # 파싱 오류 발생 시
            return {
                'file_info': file_info,
                'error': str(e),
                'raw_code': code
            }
    
    def parse_project(self, project_path: str, extensions: List[str] = None) -> Dict[str, Any]:
        """
        프로젝트 전체 파싱
        
        Args:
            project_path: 프로젝트 경로
            extensions: 처리할 파일 확장자 목록
            
        Returns:
            Dict[str, Any]: 프로젝트 파싱 결과
        """
        if extensions is None:
            extensions = ['.jsx', '.js', '.tsx', '.ts']
            
        if not os.path.exists(project_path):
            error_msg = f"프로젝트 경로를 찾을 수 없습니다: {project_path}"
            return ParsedProject.create_error(project_path, error_msg).to_dict()
        
        parsed_files = {}
        files_processed = 0
        
        try:
            for root, _, files in os.walk(project_path):
                for file in files:
                    if any(file.endswith(ext) for ext in extensions):
                        file_path = os.path.join(root, file)
                        
                        # 무시해야 할 파일 건너뛰기
                        if should_ignore_file(file_path, self.ignore_patterns):
                            continue
                            
                        files_processed += 1
                        if files_processed % 10 == 0:
                            print(f"처리 중... {files_processed}개 파일 완료")
                                
                        parsed_files[file_path] = self.parse_file(file_path)
                        
            # 요약 정보 계산
            summary = ProjectSummary.calculate_from_files(parsed_files)
            
            # 프로젝트 객체 생성
            project = ParsedProject(
                parsed_files=parsed_files,
                summary=summary,
                path=project_path
            )
            
            return project.to_dict()
            
        except Exception as e:
            error_msg = f"프로젝트 파싱 오류: {str(e)}"
            return ParsedProject.create_error(project_path, error_msg).to_dict()
    
    def _detect_mui_usage(self, code: str) -> Dict[str, Any]:
        """Material-UI 컴포넌트 사용 감지"""
        mui_data = {
            'used': False,
            'components': []
        }
        
        # MUI import 문 확인
        mui_imports = MUI_IMPORT_PATTERN.finditer(code)
        for match in mui_imports:
            mui_data['used'] = True
            components_str = match.group(1)
            imported_components = [c.strip() for c in components_str.split(',')]
            mui_data['components'].extend(imported_components)
            
        return mui_data

# 편의 함수: 프로젝트 전체 파싱용 헬퍼 함수
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
    return parser.parse_project(project_path)