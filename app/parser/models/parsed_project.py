"""
파싱된 프로젝트 모델
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from app.parser.models.parsed_file import ParsedFile

@dataclass
class ProjectSummary:
    """프로젝트 파싱 결과 요약"""
    total_files: int = 0
    components_count: int = 0
    hooks_usage: Dict[str, int] = field(default_factory=dict)
    mui_components: Dict[str, int] = field(default_factory=dict)
    file_extensions: Dict[str, int] = field(default_factory=dict)
    lifesub_stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'total_files': self.total_files,
            'components_count': self.components_count,
            'hooks_usage': self.hooks_usage,
            'mui_components': self.mui_components,
            'file_extensions': self.file_extensions,
            'lifesub_stats': self.lifesub_stats
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectSummary':
        """딕셔너리에서 생성"""
        return cls(
            total_files=data.get('total_files', 0),
            components_count=data.get('components_count', 0),
            hooks_usage=data.get('hooks_usage', {}),
            mui_components=data.get('mui_components', {}),
            file_extensions=data.get('file_extensions', {}),
            lifesub_stats=data.get('lifesub_stats', {})
        )
    
    @classmethod
    def calculate_from_files(cls, parsed_files: Dict[str, Any]) -> 'ProjectSummary':
        """파싱된 파일들로부터 요약 계산"""
        summary = cls()
        summary.total_files = len(parsed_files)
        
        # 요약 통계 계산
        for _, data in parsed_files.items():
            if 'error' in data or data.get('ignored', False):
                continue
                
            # 파일 확장자 통계
            ext = data['file_info']['extension']
            if ext in summary.file_extensions:
                summary.file_extensions[ext] += 1
            else:
                summary.file_extensions[ext] = 1
            
            # 컴포넌트 카운트
            summary.components_count += len(data.get('components', []))
                
            # 훅 사용 통계
            for hook in data.get('hooks', []):
                hook_name = hook['name']
                if hook_name in summary.hooks_usage:
                    summary.hooks_usage[hook_name] += 1
                else:
                    summary.hooks_usage[hook_name] = 1
                    
            # MUI 컴포넌트 사용 통계
            if data.get('mui_components', {}).get('used', False):
                for comp in data.get('mui_components', {}).get('components', []):
                    if comp in summary.mui_components:
                        summary.mui_components[comp] += 1
                    else:
                        summary.mui_components[comp] = 1
        
        # lifesub-web 특화 통계
        summary.lifesub_stats = cls._extract_lifesub_specific_stats(parsed_files)
        
        return summary
    
    @staticmethod
    def _extract_lifesub_specific_stats(parsed_files: Dict[str, Any]) -> Dict[str, Any]:
        """lifesub-web 특화 통계 추출"""
        stats = {
            'feature_categories': {},
            'components_by_category': {}
        }
        
        for _, data in parsed_files.items():
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

@dataclass
class ParsedProject:
    """파싱된 프로젝트"""
    parsed_files: Dict[str, Dict[str, Any]]
    summary: ProjectSummary
    path: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        result = {
            'parsed_files': self.parsed_files,
            'summary': self.summary.to_dict(),
            'path': self.path
        }
        
        if self.error:
            result['error'] = self.error
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParsedProject':
        """딕셔너리에서 생성"""
        parsed_files = data.get('parsed_files', {})
        summary_data = data.get('summary', {})
        
        return cls(
            parsed_files=parsed_files,
            summary=ProjectSummary.from_dict(summary_data),
            path=data.get('path', ''),
            error=data.get('error')
        )
    
    @classmethod
    def create_error(cls, project_path: str, error_message: str) -> 'ParsedProject':
        """오류 프로젝트 생성"""
        return cls(
            parsed_files={},
            summary=ProjectSummary(),
            path=project_path,
            error=error_message
        )
    
    def get_components_count(self) -> int:
        """총 컴포넌트 수 반환"""
        return self.summary.components_count
    
    def get_file_count(self) -> int:
        """총 파일 수 반환"""
        return self.summary.total_files
    
    def get_files_by_extension(self, extension: str) -> List[str]:
        """특정 확장자를 가진 파일 경로 목록 반환"""
        return [
            file_path for file_path, file_data in self.parsed_files.items()
            if file_data.get('file_info', {}).get('extension') == extension
        ]
    
    def get_components_by_type(self, component_type: str) -> List[Dict[str, Any]]:
        """특정 타입의 컴포넌트 목록 반환"""
        components = []
        
        for file_path, file_data in self.parsed_files.items():
            if 'error' in file_data or file_data.get('ignored', False):
                continue
                
            for component in file_data.get('components', []):
                if component.get('component_type') == component_type:
                    # 파일 정보 추가
                    component_with_file = component.copy()
                    component_with_file['file_path'] = file_path
                    components.append(component_with_file)
        
        return components