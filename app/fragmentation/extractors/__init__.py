"""
코드 파편 추출기 모듈
"""

from app.fragmentation.extractors.component_extractor import ComponentExtractor
from app.fragmentation.extractors.function_extractor import FunctionExtractor
from app.fragmentation.extractors.jsx_extractor import JSXExtractor
from app.fragmentation.extractors.api_call_extractor import APICallExtractor
from app.fragmentation.extractors.mui_extractor import MUIExtractor
from app.fragmentation.extractors.import_extractor import ImportExtractor
from app.fragmentation.extractors.state_extractor import StateLogicExtractor
from app.fragmentation.extractors.routing_extractor import RoutingExtractor

# 모든 추출기를 하나의 딕셔너리로 묶어 제공
EXTRACTORS = {
    'component': ComponentExtractor(),
    'function': FunctionExtractor(),
    'jsx_element': JSXExtractor(),
    'api_call': APICallExtractor(),
    'mui_component': MUIExtractor(),
    'import_block': ImportExtractor(),
    'state_logic': StateLogicExtractor(),
    'routing': RoutingExtractor()
}

def get_extractor(extractor_type: str):
    """
    지정된 유형의 파편 추출기 반환
    
    Args:
        extractor_type: 추출기 유형
        
    Returns:
        CodeExtractor: 해당 유형의 추출기
    """
    return EXTRACTORS.get(extractor_type)

def get_all_extractors():
    """
    모든 추출기 반환
    
    Returns:
        Dict: 모든 추출기 딕셔너리
    """
    return EXTRACTORS