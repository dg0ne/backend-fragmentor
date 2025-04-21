"""
파싱된 파일 모델
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from app.parser.models.parsed_component import ParsedComponent, ParsedHook, ParsedJSXElement

@dataclass
class FileInfo:
    """파일 메타데이터"""
    file_path: str
    file_name: str
    extension: str
    size: int
    category: Optional[str] = None
    description: Optional[str] = None
    features: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'file_path': self.file_path,
            'file_name': self.file_name,
            'extension': self.extension,
            'size': self.size,
            'category': self.category,
            'description': self.description,
            'features': self.features
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileInfo':
        """딕셔너리에서 생성"""
        return cls(
            file_path=data['file_path'],
            file_name=data['file_name'],
            extension=data['extension'],
            size=data['size'],
            category=data.get('category'),
            description=data.get('description'),
            features=data.get('features', [])
        )
    
    @classmethod
    def from_path(cls, file_path: str) -> 'FileInfo':
        """파일 경로에서 기본 정보 생성"""
        return cls(
            file_path=file_path,
            file_name=os.path.basename(file_path),
            extension=os.path.splitext(file_path)[1],
            size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        )

@dataclass
class MUIUsage:
    """Material UI 사용 정보"""
    used: bool = False
    components: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'used': self.used,
            'components': self.components
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MUIUsage':
        """딕셔너리에서 생성"""
        return cls(
            used=data.get('used', False),
            components=data.get('components', [])
        )

@dataclass
class ParsedFile:
    """파싱된 파일"""
    file_info: FileInfo
    ast: Any = None
    raw_code: str = ""
    components: List[ParsedComponent] = field(default_factory=list)
    hooks: List[ParsedHook] = field(default_factory=list)
    jsx_elements: List[ParsedJSXElement] = field(default_factory=list)
    mui_components: MUIUsage = field(default_factory=MUIUsage)
    error: Optional[str] = None
    ignored: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        result = {
            'file_info': self.file_info.to_dict(),
            'raw_code': self.raw_code,
            'components': [comp.to_dict() for comp in self.components],
            'hooks': [hook.to_dict() for hook in self.hooks],
            'jsx_elements': [elem.to_dict() for elem in self.jsx_elements],
            'mui_components': self.mui_components.to_dict()
        }
        
        if self.error:
            result['error'] = self.error
            
        if self.ignored:
            result['ignored'] = True
            
        # AST는 직렬화 가능한 형태로만 포함
        if self.ast:
            try:
                # 최소한의 AST 정보만 포함
                if hasattr(self.ast, 'body'):
                    result['ast'] = {'type': 'Program', 'body_count': len(self.ast.body)}
                else:
                    result['ast'] = {'type': str(type(self.ast))}
            except:
                result['ast'] = None
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParsedFile':
        """딕셔너리에서 생성"""
        file_info_data = data.get('file_info', {})
        components_data = data.get('components', [])
        hooks_data = data.get('hooks', [])
        jsx_elements_data = data.get('jsx_elements', [])
        mui_data = data.get('mui_components', {})
        
        return cls(
            file_info=FileInfo.from_dict(file_info_data),
            raw_code=data.get('raw_code', ''),
            components=[ParsedComponent.from_dict(c) for c in components_data],
            hooks=[ParsedHook.from_dict(h) for h in hooks_data],
            jsx_elements=[ParsedJSXElement.from_dict(e) for e in jsx_elements_data],
            mui_components=MUIUsage.from_dict(mui_data),
            error=data.get('error'),
            ignored=data.get('ignored', False)
        )
    
    @classmethod
    def create_ignored(cls, file_path: str) -> 'ParsedFile':
        """무시된 파일 생성"""
        file_info = FileInfo.from_path(file_path)
        return cls(
            file_info=file_info,
            ignored=True
        )
    
    @classmethod
    def create_error(cls, file_path: str, error_message: str, code: str = "") -> 'ParsedFile':
        """오류 파일 생성"""
        file_info = FileInfo.from_path(file_path)
        return cls(
            file_info=file_info,
            raw_code=code,
            error=error_message
        )