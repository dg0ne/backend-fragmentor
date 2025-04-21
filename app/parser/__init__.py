"""
React/JSX 코드 파싱 패키지
"""

__version__ = "0.2.0"

# 주요 클래스 및 함수를 패키지 레벨에서 쉽게 접근할 수 있도록 노출
from app.parser.base import CodeParser, CodeProcessor, MetadataExtractor
from app.parser.jsx_parser import EnhancedJSXParser, parse_react_project

# 사용 예시:
# from app.parser import EnhancedJSXParser, parse_react_project