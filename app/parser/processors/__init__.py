"""
코드 프로세서 모듈
"""

from app.parser.processors.component_processor import ComponentProcessor
from app.parser.processors.hook_processor import HookProcessor
from app.parser.processors.jsx_processor import JSXProcessor
from app.parser.processors.import_processor import ImportProcessor
from app.parser.processors.metadata_processor import LifesubMetadataExtractor

# 사용 예시:
# from app.parser.processors import ComponentProcessor, JSXProcessor