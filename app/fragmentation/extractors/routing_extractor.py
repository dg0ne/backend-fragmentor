"""
라우팅 관련 코드 추출기
"""

import re
import uuid
from typing import List, Dict, Any, Optional

from app.fragmentation.base import CodeExtractor
from app.fragmentation.utils import normalize_code

class RoutingExtractor(CodeExtractor):
    """라우팅 관련 코드 추출을 위한 추출기"""
    
    def __init__(self):
        # 라우팅 패턴
        self.router_pattern = re.compile(r'(useNavigate|useParams|useLocation|Navigate|Routes|Route)')
    
    def extract(self, code: str, metadata: Dict[str, Any], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        코드에서 라우팅 관련 로직 추출
        
        Args:
            code: 분석할 소스 코드
            metadata: 파일 메타데이터 정보
            parent_id: 부모 파편 ID (있는 경우)
            
        Returns:
            List[Dict[str, Any]]: 추출된 라우팅 관련 파편 목록
        """
        routing_fragments = []
        
        # 라우팅 패턴 매칭
        matches = self.router_pattern.finditer(code)
        
        for match in matches:
            router_code = match.group(0)
            router_start = match.start()
            
            # 라우팅 컨텍스트 파악 (주변 코드 함께 추출)
            context_start = max(0, router_start - 50)
            context_end = min(len(code), router_start + len(router_code) + 150)
            context_code = code[context_start:context_end]
            
            # 중복 방지 (이미 추출된 컨텍스트인 경우 건너뛰기)
            is_duplicate = False
            for fragment in routing_fragments:
                if fragment['content'] == normalize_code(context_code):
                    is_duplicate = True
                    break
                    
            if is_duplicate:
                continue
            
            # 파편 메타데이터 생성
            routing_metadata = {
                'file_path': metadata.get('file_path', ''),
                'file_name': metadata.get('file_name', ''),
                'router_api': match.group(1)
            }
            
            # 부모 파편 ID가 있으면 추가
            if parent_id:
                routing_metadata['parent_id'] = parent_id
            
            # 라우팅 역할 추론
            routing_metadata['routing_role'] = self._infer_routing_role(match.group(1), context_code)
            
            # 라우트 경로 추출 시도
            route_path = self._extract_route_path(context_code)
            if route_path:
                routing_metadata['route_path'] = route_path
            
            # 파편 생성
            routing_fragments.append(self._create_fragment(
                str(uuid.uuid4()),
                'routing',
                match.group(1),
                normalize_code(context_code),
                routing_metadata
            ))
        
        return routing_fragments
    
    def _infer_routing_role(self, router_api: str, context_code: str) -> str:
        """
        라우팅 역할 추론
        
        Args:
            router_api: 라우팅 API 이름
            context_code: 컨텍스트 코드
            
        Returns:
            str: 추론된 라우팅 역할
        """
        if router_api == 'useNavigate':
            if 'navigate(' in context_code:
                return '페이지 이동'
            return '내비게이션 준비'
        elif router_api == 'useParams':
            return 'URL 파라미터 추출'
        elif router_api == 'useLocation':
            return '현재 위치 정보 접근'
        elif router_api == 'Navigate':
            return '선언적 내비게이션'
        elif router_api == 'Routes':
            return '라우트 컨테이너'
        elif router_api == 'Route':
            return '라우트 정의'
        else:
            return '라우팅 관련'
    
    def _extract_route_path(self, context_code: str) -> Optional[str]:
        """
        라우트 경로 추출
        
        Args:
            context_code: 컨텍스트 코드
            
        Returns:
            Optional[str]: 추출된 라우트 경로 또는 None
        """
        # Route 컴포넌트의 path 속성 추출
        route_path_match = re.search(r'<Route\s+path=[\'"]([^\'"]*)[\'"]', context_code)
        if route_path_match:
            return route_path_match.group(1)
        
        # navigate 함수의 경로 인자 추출
        navigate_path_match = re.search(r'navigate\([\'"]([^\'"]*)[\'"]', context_code)
        if navigate_path_match:
            return navigate_path_match.group(1)
        
        return None