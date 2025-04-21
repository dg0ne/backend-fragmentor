"""
lifesub-web 프로젝트 특화 키워드 컨텍스트 모델
"""

from typing import Dict, List, Any

class KeywordContextModel:
    """
    lifesub-web 프로젝트에 특화된 키워드 컨텍스트 모델
    파편 유형 및 목적에 따른 관련 키워드 제공
    """
    
    def __init__(self):
        # lifesub-web 프로젝트 특화 문맥 키워드
        self.fragment_type_keywords = {
            'component': ['리액트', '컴포넌트', 'React', 'component', 'UI', '사용자 인터페이스'],
            'hook': ['훅', 'hook', '상태 관리', 'state management', '사이드 이펙트'],
            'function': ['함수', 'function', '유틸리티', 'utility', '헬퍼'],
            'jsx_element': ['JSX', 'element', '요소', 'UI 요소', '마크업'],
            'style_block': ['스타일', 'style', 'CSS', '디자인', '레이아웃'],
            'import_block': ['import', '가져오기', '모듈', 'module', '의존성', 'dependency'],
            'api_call': ['API', '호출', 'call', '요청', 'request', 'HTTP', '데이터 가져오기'],
            'mui_component': ['Material UI', 'MUI', '컴포넌트 라이브러리', 'component library'],
            'state_logic': ['상태', 'state', '로직', 'logic', '데이터 관리', 'data management'],
            'routing': ['라우팅', 'routing', '페이지 이동', 'navigation', 'SPA', '싱글 페이지 애플리케이션']
        }
        
        # lifesub-web 프로젝트 특화 목적 키워드
        self.purpose_keywords = {
            '인증': ['로그인', '인증', '사용자', '계정', 'login', 'auth', 'user', 'account'],
            '구독': ['구독', '서비스', '결제', 'subscription', 'service', 'payment'],
            '목록': ['목록', '리스트', '카드', 'list', 'cards', 'items'],
            '상세': ['상세', '정보', '조회', 'detail', 'info', 'view'],
            '양식': ['양식', '폼', '입력', 'form', 'input', 'submit']
        }
        
        # 컴포넌트 타입별 키워드
        self.component_type_keywords = {
            'functional': ['함수형', '함수', 'functional', '컴포넌트'],
            'class': ['클래스', '컴포넌트', 'class', 'extends'],
            'memo': ['메모이제이션', '최적화', 'memoization', 'optimization'],
            'hook': ['훅', '상태', 'hook', 'state'],
            'arrow_function': ['화살표 함수', '화살표', 'arrow function']
        }
        
        # API 서비스별 키워드
        self.api_service_keywords = {
            'mySubscriptionApi': ['구독', '서비스', '관리', 'subscription'],
            'authApi': ['인증', '로그인', '사용자', 'authentication'],
            'recommendApi': ['추천', '제안', 'recommendation']
        }
    
    def get_fragment_type_keywords(self, fragment_type: str) -> List[str]:
        """
        파편 유형에 따른 키워드 가져오기
        
        Args:
            fragment_type: 파편 유형
            
        Returns:
            List[str]: 키워드 목록
        """
        return self.fragment_type_keywords.get(fragment_type, [])[:3]
    
    def get_purpose_keywords(self, purpose: str) -> List[str]:
        """
        목적에 따른 키워드 가져오기
        
        Args:
            purpose: 목적
            
        Returns:
            List[str]: 키워드 목록
        """
        return self.purpose_keywords.get(purpose, [])[:3]
    
    def get_component_type_keywords(self, component_type: str) -> List[str]:
        """
        컴포넌트 유형에 따른 키워드 가져오기
        
        Args:
            component_type: 컴포넌트 유형
            
        Returns:
            List[str]: 키워드 목록
        """
        return self.component_type_keywords.get(component_type, [])[:3]
    
    def get_api_service_keywords(self, api_service: str) -> List[str]:
        """
        API 서비스에 따른 키워드 가져오기
        
        Args:
            api_service: API 서비스 이름
            
        Returns:
            List[str]: 키워드 목록
        """
        return self.api_service_keywords.get(api_service, [])[:3]
    
    def enhance_fragment_metadata(self, fragment: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        파편 메타데이터를 바탕으로 관련 키워드 컨텍스트 생성
        
        Args:
            fragment: 코드 파편
            
        Returns:
            Dict[str, List[str]]: 키워드 컨텍스트
        """
        context = {}
        
        # 1. 파편 유형 키워드
        context['type_keywords'] = self.get_fragment_type_keywords(fragment['type'])
        
        # 2. 메타데이터에서 추가 컨텍스트 추출
        metadata = fragment.get('metadata', {})
        
        # 목적 키워드
        if 'purpose' in metadata:
            context['purpose_keywords'] = self.get_purpose_keywords(metadata['purpose'])
        
        # 컴포넌트 유형 키워드
        if 'component_type' in metadata:
            context['component_type_keywords'] = self.get_component_type_keywords(metadata['component_type'])
        
        # API 서비스 키워드
        if 'api_service' in metadata:
            context['api_service_keywords'] = self.get_api_service_keywords(metadata['api_service'])
        
        return context