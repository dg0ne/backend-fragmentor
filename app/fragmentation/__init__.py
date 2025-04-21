"""
코드 파편화(Fragmentation) 패키지
"""

__version__ = "0.2.0"

# 주요 클래스와 함수를 패키지 레벨에서 쉽게 접근할 수 있도록 노출
from app.fragmentation.base import CodeExtractor, FragmenterStrategy
from app.fragmentation.fragmenter import ReactFragmenter
from app.fragmentation.models.fragment import CodeFragment

# 사용 예시:
# from app.fragmentation import ReactFragmenter, CodeFragment