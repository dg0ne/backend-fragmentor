"""
API 호출 코드 추출기
"""

import re
import uuid
from typing import List, Dict, Any, Optional

from app.fragmentation.base import CodeExtractor
from app.fragmentation.utils import normalize_code

class APICallExtractor(CodeExtractor):
    """API 호출 코드 추출을 위한 추출기"""
    
    def __init__(self):
        # lifesub-web 특화 API 호출 패턴
        self.api_call_pattern = re.compile(r'(mySubscriptionApi|authApi|recommendApi)\.(get|post|put|delete).*?\(.*?\)')
    
    def extract(self, code: str, metadata: Dict[str, Any], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        코드에서 API 호출 추출
        
        Args:
            code: 분석할 소스 코드
            metadata: 파일 메타데이터 정보
            parent_id: 부모 파편 ID (있는 경우)
            
        Returns:
            List[Dict[str, Any]]: 추출된 API 호출 파편 목록
        """
        api_calls = []
        
        # API 호출 패턴 매칭
        matches = self.api_call_pattern.finditer(code)
        
        for match in matches:
            api_code = match.group(0)
            api_start = match.start()
            
            # 함수 내부에서 호출되는 경우 문맥 파악
            context_start = max(0, api_start - 100)
            context_end = min(len(code), api_start + len(api_code) + 100)
            context_code = code[context_start:context_end]
            
            # API 이름 및 HTTP 메서드 추출
            api_parts = api_code.split('.')
            api_service = api_parts[0] if len(api_parts) > 0 else ""
            method = api_parts[1].split('(')[0] if len(api_parts) > 1 else ""
            
            # 중복 방지 (이미 추출된 API 호출인 경우 건너뛰기)
            is_duplicate = False
            for existing_api in api_calls:
                if existing_api['content'] == context_code:
                    is_duplicate = True
                    break
            
            if is_duplicate:
                continue
            
            # 파편 메타데이터 생성
            api_metadata = {
                'file_path': metadata.get('file_path', ''),
                'file_name': metadata.get('file_name', ''),
                'api_service': api_service,
                'http_method': method,
                'context': api_code
            }
            
            # 부모 파편 ID가 있으면 추가
            if parent_id:
                api_metadata['parent_id'] = parent_id
            
            # API 서비스별 추가 메타데이터
            if api_service == 'mySubscriptionApi':
                api_metadata['domain'] = '구독'
                if method == 'get':
                    api_metadata['purpose'] = '구독 정보 조회'
                elif method == 'post':
                    api_metadata['purpose'] = '구독 생성/갱신'
                elif method == 'put':
                    api_metadata['purpose'] = '구독 정보 수정'
                elif method == 'delete':
                    api_metadata['purpose'] = '구독 취소'
            elif api_service == 'authApi':
                api_metadata['domain'] = '인증'
                if 'login' in api_code.lower():
                    api_metadata['purpose'] = '로그인'
                elif 'logout' in api_code.lower():
                    api_metadata['purpose'] = '로그아웃'
                elif 'register' in api_code.lower():
                    api_metadata['purpose'] = '회원가입'
            elif api_service == 'recommendApi':
                api_metadata['domain'] = '추천'
                api_metadata['purpose'] = '추천 서비스'
            
            # 파편 생성
            api_calls.append(self._create_fragment(
                str(uuid.uuid4()),
                'api_call',
                f"{api_service}.{method}",
                normalize_code(context_code),
                api_metadata
            ))
        
        return api_calls