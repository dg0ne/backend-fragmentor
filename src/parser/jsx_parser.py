"""
React/JSX 코드 파싱 모듈
"""

import os
import re
import esprima
from esprima import parseModule
from typing import Dict, List, Any, Tuple

class JSXParser:
    """React JSX 코드를 파싱하는 클래스"""
    
    def __init__(self):
        self.component_pattern = re.compile(r'function\s+([A-Z][a-zA-Z0-9]*)|class\s+([A-Z][a-zA-Z0-9]*)|const\s+([A-Z][a-zA-Z0-9]*)\s*=')
        self.hook_pattern = re.compile(r'(use[A-Z][a-zA-Z0-9]*)')
        
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
        
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
            
        # 파일 메타데이터
        file_info = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'extension': os.path.splitext(file_path)[1],
            'size': os.path.getsize(file_path),
        }
        
        try:
            # AST 파싱 시도
            ast = parseModule(code, jsx=True, tolerant=True)
            
            # 컴포넌트 및 훅 식별
            components = self._identify_components(code)
            hooks = self._identify_hooks(code)
            
            return {
                'file_info': file_info,
                'ast': ast,
                'components': components,
                'hooks': hooks,
                'raw_code': code
            }
        except Exception as e:
            # 파싱 오류 발생 시
            return {
                'file_info': file_info,
                'error': str(e),
                'raw_code': code
            }
    
    def _identify_components(self, code: str) -> List[Dict[str, Any]]:
        """코드에서 React 컴포넌트 식별"""
        components = []
        matches = self.component_pattern.finditer(code)
        
        for match in matches:
            # 세 개의 그룹 중 None이 아닌 그룹 찾기
            name = next((g for g in match.groups() if g is not None), None)
            if name:
                # 컴포넌트 시작 위치 찾기
                start_pos = match.start()
                # 컴포넌트 블록 끝 찾기 (간단한 접근법)
                component_code = self._extract_component_code(code, start_pos)
                
                components.append({
                    'name': name,
                    'start_pos': start_pos,
                    'code': component_code
                })
        
        return components
    
    def _identify_hooks(self, code: str) -> List[str]:
        """코드에서 React 훅 사용 식별"""
        hooks = []
        matches = self.hook_pattern.finditer(code)
        
        for match in matches:
            hook_name = match.group(1)
            if hook_name not in hooks:
                hooks.append(hook_name)
                
        return hooks
    
    def _extract_component_code(self, code: str, start_pos: int) -> str:
        """
        주어진 시작 위치에서 컴포넌트 코드 블록 추출
        (간단한 구현으로, 실제 상황에서는 더 정교한 로직 필요)
        """
        # 함수형 컴포넌트 또는 클래스 컴포넌트의 끝을 찾기 위한 간단한 방법
        # 괄호 매칭을 통해 블록 끝 찾기
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
            # 최소 200자 또는 코드 끝까지
            end_pos = min(start_pos + 200, len(code))
            
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
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        results[file_path] = self.parse_file(file_path)
                    except Exception as e:
                        print(f"파일 파싱 오류: {file_path} - {str(e)}")
        
        return results


def parse_react_project(project_path: str) -> Dict[str, Any]:
    """
    React 프로젝트 전체 파싱 헬퍼 함수
    
    Args:
        project_path: React 프로젝트 디렉토리 경로
        
    Returns:
        Dict: 파싱 결과 및 요약 정보
    """
    parser = JSXParser()
    parsed_files = parser.scan_directory(project_path)
    
    # 프로젝트 요약 정보
    summary = {
        'total_files': len(parsed_files),
        'components_count': sum(len(data.get('components', [])) for _, data in parsed_files.items() if 'error' not in data),
        'hooks_usage': {},
        'file_extensions': {}
    }
    
    # 훅 사용 통계 및 파일 확장자 통계
    for _, data in parsed_files.items():
        if 'error' not in data:
            # 훅 사용 통계
            for hook in data.get('hooks', []):
                if hook in summary['hooks_usage']:
                    summary['hooks_usage'][hook] += 1
                else:
                    summary['hooks_usage'][hook] = 1
            
            # 파일 확장자 통계
            ext = data['file_info']['extension']
            if ext in summary['file_extensions']:
                summary['file_extensions'][ext] += 1
            else:
                summary['file_extensions'][ext] = 1
    
    return {
        'parsed_files': parsed_files,
        'summary': summary
    }