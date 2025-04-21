"""
파싱된 React 컴포넌트 모델
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class ParsedProps:
    """파싱된 Props 정보"""
    names: List[str] = field(default_factory=list)
    types: Dict[str, str] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'names': self.names,
            'types': self.types,
            'defaults': self.defaults
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParsedProps':
        """딕셔너리에서 생성"""
        return cls(
            names=data.get('names', []),
            types=data.get('types', {}),
            defaults=data.get('defaults', {})
        )

@dataclass
class ParsedState:
    """파싱된 상태(useState) 정보"""
    name: str
    setter: str
    initial_value: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'name': self.name,
            'setter': self.setter,
            'initial_value': self.initial_value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParsedState':
        """딕셔너리에서 생성"""
        return cls(
            name=data['name'],
            setter=data['setter'],
            initial_value=data.get('initial_value')
        )

@dataclass
class ParsedComponent:
    """파싱된 React 컴포넌트"""
    name: str
    code: str
    start_pos: int
    component_type: str
    props: ParsedProps = field(default_factory=ParsedProps)
    states: List[ParsedState] = field(default_factory=list)
    children: List[Dict[str, Any]] = field(default_factory=list)
    category: Optional[str] = None
    purpose: Optional[str] = None
    pattern_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'name': self.name,
            'code': self.code,
            'start_pos': self.start_pos,
            'component_type': self.component_type,
            'props': self.props.to_dict(),
            'states': [state.to_dict() for state in self.states],
            'children': self.children,
            'category': self.category,
            'purpose': self.purpose,
            'pattern_type': self.pattern_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParsedComponent':
        """딕셔너리에서 생성"""
        props_data = data.get('props', {})
        states_data = data.get('states', [])
        
        return cls(
            name=data['name'],
            code=data['code'],
            start_pos=data['start_pos'],
            component_type=data['component_type'],
            props=ParsedProps.from_dict(props_data if isinstance(props_data, dict) else {}),
            states=[ParsedState.from_dict(s) for s in states_data if isinstance(s, dict)],
            children=data.get('children', []),
            category=data.get('category'),
            purpose=data.get('purpose'),
            pattern_type=data.get('pattern_type')
        )

@dataclass
class ParsedHook:
    """파싱된 React 커스텀 훅"""
    name: str
    code: str
    start_pos: int
    type: str = 'custom'
    used_hooks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'name': self.name,
            'code': self.code,
            'start_pos': self.start_pos,
            'type': self.type,
            'used_hooks': self.used_hooks
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParsedHook':
        """딕셔너리에서 생성"""
        return cls(
            name=data['name'],
            code=data['code'],
            start_pos=data['start_pos'],
            type=data.get('type', 'custom'),
            used_hooks=data.get('used_hooks', [])
        )

@dataclass
class ParsedJSXElement:
    """파싱된 JSX 요소"""
    name: str
    code: str
    start_pos: int
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'name': self.name,
            'code': self.code,
            'start_pos': self.start_pos
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParsedJSXElement':
        """딕셔너리에서 생성"""
        return cls(
            name=data['name'],
            code=data['code'],
            start_pos=data['start_pos']
        )