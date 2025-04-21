"""
임베딩을 위한 컨텍스트 향상 모듈
"""

import os
from typing import Dict, List, Any, Optional

from app.embedding.base import ContextEnhancer
from app.embedding.models.keyword_context import KeywordContextModel

class CodeContextEnhancer(ContextEnhancer):
    """
    코드 파편에 추가 컨텍스트를 제공하는 향상기
    임베딩 품질 개선을 위한 의미 정보 추가
    """
    
    def __init__(self):
        self.keyword_model = KeywordContextModel()
        
        # 최대 텍스트 길이 제한 (모델 한계 고려)
        self.max_description_length = 200  # 설명 최대 길이
        self.max_context_length = 150      # 컨텍스트 최대 길이
        self.max_content_length = 512      # 컨텐츠 최대 길이
    
    def enhance(self, fragment: Dict[str, Any]) -> str:
        """
        코드 파편에 컨텍스트 정보를 추가하여 향상된 텍스트 생성
        
        Args:
            fragment: 코드 파편
            
        Returns:
            str: 컨텍스트가 향상된 텍스트
        """
        # 1. 기본 정보 추출
        content = fragment['content']
        frag_type = fragment['type']
        name = fragment['name']
        metadata = fragment.get('metadata', {})
        
        # 2. 코드 구조 및 목적 설명 생성
        code_description = self._generate_description(fragment)
        
        # 3. 문맥 정보 구성
        context = self._generate_context(fragment)
        
        # 4. 최대 텍스트 길이 제한 
        available_content_length = self.max_content_length - len(code_description) - len(context)
        
        if len(code_description) > self.max_description_length:
            code_description = code_description[:self.max_description_length]
            
        if len(context) > self.max_context_length:
            context = context[:self.max_context_length]
                
        if len(content) > available_content_length:
            content = content[:available_content_length]
        
        # 5. 최종 임베딩 텍스트 생성
        embedding_text = f"{code_description}\n\n{context}\n\n{content}"
        
        return embedding_text
    
    def _generate_description(self, fragment: Dict[str, Any]) -> str:
        """
        파편에 대한 설명 생성
        
        Args:
            fragment: 코드 파편
            
        Returns:
            str: 생성된 설명
        """
        frag_type = fragment['type']
        name = fragment['name']
        metadata = fragment.get('metadata', {})
        
        # 기본 설명
        description = f"이것은 {frag_type} 타입이며 이름은 {name}입니다. "
        
        # 파일 경로 분석하여 추가 컨텍스트 추출
        file_path = metadata.get('file_path', '')
        
        # 모듈/카테고리 정보 추가
        module_info = self._extract_module_info(file_path)
        if module_info:
            description += module_info
        
        # 파편 유형별 설명 추가
        if frag_type == 'component':
            description += self._generate_component_description(fragment)
        elif frag_type == 'function':
            description += self._generate_function_description(fragment)
        elif frag_type == 'api_call':
            description += self._generate_api_call_description(fragment)
        elif frag_type == 'jsx_element':
            description += self._generate_jsx_description(fragment)
        elif frag_type == 'mui_component':
            description += self._generate_mui_description(fragment)
        elif frag_type == 'state_logic':
            description += self._generate_state_logic_description(fragment)
        elif frag_type == 'routing':
            description += self._generate_routing_description(fragment)
        elif frag_type == 'import_block':
            description += self._generate_import_description(fragment)
        
        return description
    
    def _extract_module_info(self, file_path: str) -> str:
        """파일 경로에서 모듈 정보 추출"""
        if not file_path:
            return ""
            
        module_info = ""
        if 'src/components/' in file_path:
            module_parts = file_path.split('src/components/')
            if len(module_parts) > 1:
                component_category = module_parts[1].split('/')[0]
                module_info = f"이 코드는 '{component_category}' 컴포넌트 카테고리에 속합니다. "
        elif 'src/pages/' in file_path:
            module_info = "이 코드는 페이지 컴포넌트입니다. "
        elif 'src/contexts/' in file_path:
            module_info = "이 코드는 Context API와 관련된 파일입니다. "
        elif 'src/services/' in file_path:
            module_info = "이 코드는 API 서비스와 관련된 파일입니다. "
        elif 'src/utils/' in file_path:
            module_info = "이 코드는 유틸리티 함수를 포함합니다. "
        elif 'deployment/' in file_path:
            module_info = "이 코드는 배포 설정과 관련된 파일입니다. "
            
        return module_info
    
    def _generate_component_description(self, fragment: Dict[str, Any]) -> str:
        """컴포넌트 파편에 대한 설명 생성"""
        metadata = fragment.get('metadata', {})
        name = fragment['name']
        
        comp_type = metadata.get('component_type', 'unknown')
        purpose = metadata.get('purpose', '')
        props = metadata.get('props', [])
        
        desc = f"이것은 {comp_type} 방식의 React 컴포넌트입니다. "
        
        # lifesub-web 특화 목적 추가
        if 'Login' in name or 'Auth' in name:
            desc += "이 컴포넌트는 사용자 인증 및 로그인 기능을 담당합니다. "
        elif 'Subscription' in name:
            desc += "이 컴포넌트는 구독 서비스 관리 기능을 담당합니다. "
        elif 'List' in name:
            desc += "이 컴포넌트는 목록 형태의 데이터를 표시합니다. "
        elif 'Detail' in name:
            desc += "이 컴포넌트는 상세 정보를 표시합니다. "
        elif 'Card' in name:
            desc += "이 컴포넌트는 카드 형태의 UI를 표시합니다. "
        elif 'Loading' in name:
            desc += "이 컴포넌트는 로딩 상태를 표시합니다. "
        elif 'Error' in name:
            desc += "이 컴포넌트는 오류 메시지를 표시합니다. "
        
        if purpose:
            desc += f"주요 목적은 {purpose}입니다. "
        
        if props:
            desc += f"이 컴포넌트는 다음 props를 사용합니다: {', '.join(props[:5])}. "
            
        return desc
    
    def _generate_function_description(self, fragment: Dict[str, Any]) -> str:
        """함수 파편에 대한 설명 생성"""
        metadata = fragment.get('metadata', {})
        name = fragment['name']
        
        desc = ""
        if 'function_type' in metadata:
            desc += f"이것은 {metadata['function_type']} 함수입니다. "
        
        if 'handle' in name.lower():
            desc += "이 함수는 이벤트 핸들러입니다. "
        elif 'fetch' in name.lower() or 'get' in name.lower():
            desc += "이 함수는 데이터를 가져오는 역할을 합니다. "
        elif 'format' in name.lower():
            desc += "이 함수는 데이터 포맷팅을 담당합니다. "
        
        if 'purpose' in metadata:
            desc += f"이 함수의 목적은 {metadata['purpose']}입니다. "
            
        if metadata.get('is_async', False):
            desc += "이것은 비동기 함수입니다. "
            
        if metadata.get('is_event_handler', False):
            desc += "이 함수는 이벤트를 처리합니다. "
            
        parent_id = metadata.get('parent_id', None)
        if parent_id:
            desc += "이 함수는 상위 컴포넌트의 내부 함수입니다. "
            
        return desc
    
    def _generate_api_call_description(self, fragment: Dict[str, Any]) -> str:
        """API 호출 파편에 대한 설명 생성"""
        metadata = fragment.get('metadata', {})
        
        api_service = metadata.get('api_service', '')
        http_method = metadata.get('http_method', '')
        
        desc = f"이 코드는 API 호출을 수행합니다. "
        
        # lifesub-web API 서비스 특화 설명
        if api_service == 'mySubscriptionApi':
            desc += "이 코드는 구독 관리 API를 호출합니다. "
            if http_method == 'get':
                desc += "구독 정보를 조회합니다. "
            elif http_method == 'post':
                desc += "새로운 구독을 등록합니다. "
            elif http_method == 'delete':
                desc += "구독을 취소합니다. "
        elif api_service == 'authApi':
            desc += "이 코드는 인증 관련 API를 호출합니다. "
            if 'login' in fragment['content'].lower():
                desc += "사용자 로그인을 처리합니다. "
            elif 'logout' in fragment['content'].lower():
                desc += "사용자 로그아웃을 처리합니다. "
        elif api_service == 'recommendApi':
            desc += "이 코드는 구독 추천 API를 호출합니다. "
            
        return desc
    
    def _generate_jsx_description(self, fragment: Dict[str, Any]) -> str:
        """JSX 요소 파편에 대한 설명 생성"""
        metadata = fragment.get('metadata', {})
        name = fragment['name']
        
        desc = "이 코드는 JSX 요소를 정의합니다. "
        
        if 'ui_type' in metadata:
            ui_type = metadata['ui_type']
            if ui_type == 'card':
                desc += "카드 형태의 UI를 표시합니다. "
            elif ui_type == 'list':
                desc += "목록 형태의 UI를 표시합니다. "
            elif ui_type == 'form':
                desc += "양식 입력을 위한 UI를 정의합니다. "
            elif ui_type == 'button':
                desc += "사용자가 클릭할 수 있는 버튼을 표시합니다. "
            elif ui_type == 'container':
                desc += "다른 컴포넌트들을 감싸는 컨테이너 역할을 합니다. "
        else:
            if 'Card' in name or 'Paper' in name:
                desc += "이 JSX 요소는 카드 형태의 UI 컴포넌트를 렌더링합니다. "
            elif 'List' in name:
                desc += "이 JSX 요소는 목록 형태의 UI를 렌더링합니다. "
            elif 'Button' in name:
                desc += "이 JSX 요소는 버튼을 렌더링합니다. "
            elif 'Box' in name or 'Container' in name:
                desc += "이 JSX 요소는 레이아웃 컨테이너입니다. "
                
        return desc
    
    def _generate_mui_description(self, fragment: Dict[str, Any]) -> str:
        """MUI 컴포넌트 파편에 대한 설명 생성"""
        metadata = fragment.get('metadata', {})
        content = fragment['content']
        
        desc = "이 코드는 Material UI 라이브러리의 컴포넌트를 사용합니다. "
        
        mui_component = metadata.get('mui_component', '')
        if mui_component:
            desc += f"{mui_component} 컴포넌트를 사용합니다. "
            
        if 'ui_type' in metadata:
            ui_type = metadata['ui_type']
            if ui_type == 'container':
                desc += "컨텐츠를 그룹화하는 컨테이너 역할을 합니다. "
            elif ui_type == 'layout':
                desc += "레이아웃을 구성하는 역할을 합니다. "
            elif ui_type == 'text':
                desc += "텍스트를 표시하는 역할을 합니다. "
            elif ui_type == 'action':
                desc += "사용자 상호작용을 위한 역할을 합니다. "
            elif ui_type == 'input':
                desc += "사용자 입력을 받는 역할을 합니다. "
            elif ui_type == 'feedback':
                desc += "사용자에게 피드백을 제공하는 역할을 합니다. "
                
        if 'purpose' in metadata:
            desc += f"주요 목적은 {metadata['purpose']}입니다. "
            
        return desc
    
    def _generate_state_logic_description(self, fragment: Dict[str, Any]) -> str:
        """상태 관리 로직 파편에 대한 설명 생성"""
        metadata = fragment.get('metadata', {})
        
        hook_type = metadata.get('hook_type', '')
        desc = f"이 코드는 React {hook_type} 훅을 사용한 상태 관리 로직을 포함합니다. "
        
        if hook_type == 'useEffect':
            dependencies = metadata.get('dependencies', [])
            purpose = metadata.get('purpose', '')
            
            if purpose:
                desc += f"이 useEffect의 목적은 {purpose}입니다. "
                
            if metadata.get('contains_api_call', False):
                desc += "API 호출을 포함하고 있습니다. "
                
            if dependencies:
                desc += f"이 effect는 다음 의존성이 변경될 때 실행됩니다: {', '.join(dependencies[:3])}. "
        
        elif hook_type == 'useState':
            states_count = metadata.get('states_count', 0)
            state_names = metadata.get('state_names', [])
            
            if states_count > 1:
                desc += f"총 {states_count}개의 상태 변수를 정의합니다. "
                
            if state_names:
                desc += f"다음 상태 변수들을 포함합니다: {', '.join(state_names[:3])}. "
        
        elif hook_type == 'useReducer':
            state_name = metadata.get('state_name', '')
            
            if state_name:
                desc += f"'{state_name}' 상태 변수와 dispatch 함수를 정의합니다. "
                
        return desc
    
    def _generate_routing_description(self, fragment: Dict[str, Any]) -> str:
        """라우팅 로직 파편에 대한 설명 생성"""
        metadata = fragment.get('metadata', {})
        
        router_api = metadata.get('router_api', '')
        routing_role = metadata.get('routing_role', '')
        route_path = metadata.get('route_path', '')
        
        desc = f"이 코드는 React Router의 {router_api}를 사용한 라우팅 로직을 포함합니다. "
        
        if routing_role:
            desc += f"라우팅 역할은 {routing_role}입니다. "
            
        if route_path:
            desc += f"경로: '{route_path}'. "
            
        return desc
    
    def _generate_import_description(self, fragment: Dict[str, Any]) -> str:
        """import 문 파편에 대한 설명 생성"""
        metadata = fragment.get('metadata', {})
        
        imports_count = metadata.get('imports_count', 0)
        libraries = metadata.get('libraries', {})
        
        desc = f"이 코드는 {imports_count}개의 import 문을 포함합니다. "
        
        imported_libs = []
        if libraries.get('react', False):
            imported_libs.append("React")
        if libraries.get('react-router', False):
            imported_libs.append("React Router")
        if libraries.get('mui', False):
            imported_libs.append("Material UI")
        if libraries.get('api', False):
            imported_libs.append("API 서비스")
        if libraries.get('hooks', False):
            imported_libs.append("커스텀 훅")
        if libraries.get('redux', False):
            imported_libs.append("Redux")
        if libraries.get('formik', False):
            imported_libs.append("Formik")
        if libraries.get('axios', False):
            imported_libs.append("Axios")
            
        if imported_libs:
            desc += f"주요 라이브러리: {', '.join(imported_libs)}. "
            
        return desc
    
    def _generate_context(self, fragment: Dict[str, Any]) -> str:
        """
        파편에 대한 컨텍스트 정보 생성
        
        Args:
            fragment: 코드 파편
            
        Returns:
            str: 생성된 컨텍스트
        """
        # 키워드 컨텍스트 모델에서 관련 키워드 가져오기
        keyword_context = self.keyword_model.enhance_fragment_metadata(fragment)
        
        # 컨텍스트 구성 요소 정의
        context_parts = []
        
        # 1. 기본 타입별 접두사
        frag_type = fragment['type']
        if 'type_keywords' in keyword_context:
            context_parts.append(f"{' '.join(keyword_context['type_keywords'])}")
        
        # 2. 이름
        context_parts.append(f"{fragment['name']}")
        
        # 3. 파일 경로 정보
        metadata = fragment.get('metadata', {})
        if 'file_name' in metadata:
            context_parts.append(f"파일: {metadata['file_name']}")
        
        # 4. 목적 정보
        if 'purpose' in metadata and 'purpose_keywords' in keyword_context:
            context_parts.append(f"목적: {metadata['purpose']} {' '.join(keyword_context['purpose_keywords'])}")
        
        # 5. 컴포넌트 유형 정보
        if 'component_type' in metadata and 'component_type_keywords' in keyword_context:
            context_parts.append(f"컴포넌트 타입: {metadata['component_type']} {' '.join(keyword_context['component_type_keywords'])}")
        
        # 6. Props 정보
        if 'props' in metadata and len(metadata['props']) > 0:
            context_parts.append(f"Props: {', '.join(metadata['props'][:5])}")
        
        # 7. API 서비스 정보
        if 'api_service' in metadata and 'api_service_keywords' in keyword_context:
            context_parts.append(f"API: {metadata['api_service']} {' '.join(keyword_context['api_service_keywords'])}")
            if 'http_method' in metadata:
                context_parts.append(f"Method: {metadata['http_method']}")
        
        # 8. 라우팅 정보
        if 'routing_role' in metadata:
            context_parts.append(f"라우팅: {metadata['routing_role']}")
            if 'route_path' in metadata:
                context_parts.append(f"경로: {metadata['route_path']}")
        
        # 9. 상태 관리 정보
        if 'hook_type' in metadata:
            context_parts.append(f"훅: {metadata['hook_type']}")
            if 'dependencies' in metadata and len(metadata['dependencies']) > 0:
                context_parts.append(f"의존성: {', '.join(metadata['dependencies'][:3])}")
        
        # 컨텍스트 결합
        context = ' | '.join(context_parts)
        
        return context