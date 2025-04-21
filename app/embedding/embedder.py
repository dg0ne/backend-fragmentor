"""
향상된 코드 임베딩(Embedding) 생성 모듈 - lifesub-web 프로젝트용
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Union, Optional
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

class CodeEmbedder:
    """
    lifesub-web 코드 조각을 SentenceTransformer를 이용해 벡터로 변환
    """
    
    def __init__(self, model_name: str = 'microsoft/codebert-base', cache_dir: Optional[str] = None):
        """
        Args:
            model_name: SentenceTransformer 모델 이름
            cache_dir: 임베딩 캐싱 디렉토리 (None인 경우 캐싱 비활성화)
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.vector_dim = self.model.get_sentence_embedding_dimension()
        self.cache_dir = cache_dir
        
        # 캐시 디렉토리 생성
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            
        # 파편 타입별 가중치 설정 추가
        self.type_weights = {
            'component': 2.0,     # 컴포넌트는 가장 중요
            'function': 1.8,      # 함수도 중요
            'api_call': 1.7,      # API 호출도 중요
            'state_logic': 1.6,   # 상태 로직도 중요
            'routing': 1.5,       # 라우팅도 중요
            'jsx_element': 1.3,   # JSX 요소는 중간 중요도
            'mui_component': 1.2, # MUI 컴포넌트는 중간 중요도
            'import_block': 0.8,  # import 블록은 덜 중요
            'style_block': 0.5    # style 블록은 가장 덜 중요
        }
            
        # lifesub-web 프로젝트 특화 문맥 키워드
        self.context_keywords = {
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
    
    def embed_fragment(self, fragment: Dict[str, Any]) -> np.ndarray:
        """
        단일 코드 파편 임베딩 (가중치 적용)
        
        Args:
            fragment: 코드 파편 객체
            
        Returns:
            np.ndarray: 임베딩 벡터
        """
        # 캐시 확인
        if self.cache_dir:
            cache_path = os.path.join(self.cache_dir, f"{fragment['id']}.pkl")
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    # 캐시에서 가져온 임베딩도 가중치 적용
                    base_embedding = pickle.load(f)
                    return self._apply_weights(base_embedding, fragment)
        
        # 임베딩 생성을 위한 텍스트 구성
        embedding_text = self._prepare_embedding_text(fragment)
        
        # 임베딩 생성
        base_embedding = self.model.encode(embedding_text)
        
        # 가중치 적용된 임베딩
        weighted_embedding = self._apply_weights(base_embedding, fragment)
        
        # 캐시 저장 (원본 임베딩만 저장, 가중치는 실시간 적용)
        if self.cache_dir:
            with open(cache_path, 'wb') as f:
                pickle.dump(base_embedding, f)
        
        return weighted_embedding
    
    def _apply_weights(self, embedding: np.ndarray, fragment: Dict[str, Any]) -> np.ndarray:
        """
        임베딩에 파편 타입 가중치 적용
        
        Args:
            embedding: 원본 임베딩 벡터
            fragment: 코드 파편 정보
            
        Returns:
            np.ndarray: 가중치 적용된 임베딩
        """
        # 파편 타입에 따른 가중치 적용
        fragment_type = fragment['type']
        weight = self.type_weights.get(fragment_type, 1.0)
        
        # 코드 길이에 따른 추가 가중치 (최대 50% 추가)
        content_length = len(fragment.get('content', ''))
        length_factor = min(1.0 + (content_length / 1000), 1.5)
        
        # 특정 키워드 검색 관련성 강화
        content = fragment.get('content', '').lower()
        name = fragment.get('name', '').lower()
        file_name = fragment.get('metadata', {}).get('file_name', '').lower()
        keyword_bonus = 1.0
        
        # 로그인/인증 관련 코드에 보너스
        if ('login' in content or 'auth' in content or 
            'login' in name or 'auth' in name or 
            'login' in file_name or 'auth' in file_name or
            'password' in content or 'user' in content):
            keyword_bonus += 0.3
            
        # 구독 관련 코드에 보너스
        if ('subscription' in content or 'subscribe' in content or 
            '구독' in content or 'subscription' in name or
            'subscription' in file_name):
            keyword_bonus += 0.3
            
        # 최종 가중치 적용
        final_weight = weight * length_factor * keyword_bonus
        weighted_embedding = embedding * final_weight
        
        # 정규화 (코사인 유사도를 위해)
        norm = np.linalg.norm(weighted_embedding)
        if norm > 0:
            return weighted_embedding / norm
        return weighted_embedding
    
    def embed_fragments(self, fragments: List[Dict[str, Any]], batch_size: int = 32) -> Dict[str, np.ndarray]:
        """
        다수의 코드 파편 임베딩 (배치 처리)
        
        Args:
            fragments: 코드 파편 목록
            batch_size: 배치 크기
            
        Returns:
            Dict[str, np.ndarray]: fragment_id를 키로, 임베딩 벡터를 값으로 하는 딕셔너리
        """
        embeddings = {}
        texts_to_embed = []
        ids_to_embed = []
        fragments_to_embed = []  # 가중치 적용을 위해 전체 fragment 객체 저장
        
        print(f"총 {len(fragments)}개 파편 임베딩 생성 중...")
        
        # 캐시 확인 및 임베딩 필요한 파편 확인
        for fragment in fragments:
            fragment_id = fragment['id']
            
            # 캐시 확인
            if self.cache_dir:
                cache_path = os.path.join(self.cache_dir, f"{fragment_id}.pkl")
                if os.path.exists(cache_path):
                    with open(cache_path, 'rb') as f:
                        base_embedding = pickle.load(f)
                        # 가중치 적용
                        embeddings[fragment_id] = self._apply_weights(base_embedding, fragment)
                        continue
            
            # 임베딩 필요한 파편 추가
            embedding_text = self._prepare_embedding_text(fragment)
            texts_to_embed.append(embedding_text)
            ids_to_embed.append(fragment_id)
            fragments_to_embed.append(fragment)  # 가중치 적용을 위해 저장
        
        # 임베딩이 필요한 것이 있을 경우만 처리
        if texts_to_embed:
            # 배치 처리
            for i in tqdm(range(0, len(texts_to_embed), batch_size)):
                batch_texts = texts_to_embed[i:i+batch_size]
                batch_ids = ids_to_embed[i:i+batch_size]
                batch_fragments = fragments_to_embed[i:i+batch_size]
                
                # 배치 임베딩 생성
                batch_embeddings = self.model.encode(batch_texts)
                
                # 결과 저장 및 캐싱
                for j, fragment_id in enumerate(batch_ids):
                    # 원본 임베딩
                    base_embedding = batch_embeddings[j]
                    
                    # 가중치 적용
                    weighted_embedding = self._apply_weights(base_embedding, batch_fragments[j])
                    embeddings[fragment_id] = weighted_embedding
                    
                    # 캐시 저장 (원본 임베딩만 저장)
                    if self.cache_dir:
                        cache_path = os.path.join(self.cache_dir, f"{fragment_id}.pkl")
                        with open(cache_path, 'wb') as f:
                            pickle.dump(base_embedding, f)
        
        return embeddings
    
    def _prepare_embedding_text(self, fragment: Dict[str, Any]) -> str:
        """
        임베딩을 위한 텍스트 준비
        lifesub-web 특화 컨텍스트 포함
        
        Args:
            fragment: 코드 파편
            
        Returns:
            str: 임베딩을 위한 텍스트
        """
        content = fragment['content']
        frag_type = fragment['type']
        name = fragment['name']
        metadata = fragment['metadata']
        
        # 코드 구조 및 목적 설명 생성
        code_description = f"이것은 {frag_type} 타입이며 이름은 {name}입니다. "
        
        # 파일 경로 분석하여 추가 컨텍스트 추출
        file_path = metadata.get('file_path', '')
        file_name = metadata.get('file_name', '')
        
        # 파일 경로에서 모듈/카테고리 추출
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
        
        code_description += module_info
        
        # 타입별 설명 추가
        if frag_type == 'component':
            comp_type = metadata.get('component_type', 'unknown')
            purpose = metadata.get('purpose', '')
            props = metadata.get('props', [])
            
            code_description += f"이것은 {comp_type} 방식의 React 컴포넌트입니다. "
            
            # lifesub-web 특화 목적 추가
            if 'Login' in name or 'Auth' in name:
                code_description += "이 컴포넌트는 사용자 인증 및, 로그인 기능을 담당합니다. "
            elif 'Subscription' in name:
                code_description += "이 컴포넌트는 구독 서비스 관리 기능을 담당합니다. "
            elif 'List' in name:
                code_description += "이 컴포넌트는 목록 형태의 데이터를 표시합니다. "
            elif 'Detail' in name:
                code_description += "이 컴포넌트는 상세 정보를 표시합니다. "
            elif 'Card' in name:
                code_description += "이 컴포넌트는 카드 형태의 UI를 표시합니다. "
            elif 'Loading' in name:
                code_description += "이 컴포넌트는 로딩 상태를 표시합니다. "
            elif 'Error' in name:
                code_description += "이 컴포넌트는 오류 메시지를 표시합니다. "
            
            if purpose:
                code_description += f"주요 목적은 {purpose}입니다. "
            
            if props:
                code_description += f"이 컴포넌트는 다음 props를 사용합니다: {', '.join(props[:5])}. "
        
        elif frag_type == 'function':
            if 'handle' in name.lower():
                code_description += "이 함수는 이벤트 핸들러입니다. "
            elif 'fetch' in name.lower() or 'get' in name.lower():
                code_description += "이 함수는 데이터를 가져오는 역할을 합니다. "
            elif 'format' in name.lower():
                code_description += "이 함수는 데이터 포맷팅을 담당합니다. "
            
            parent = metadata.get('parent_id', None)
            if parent:
                code_description += "이 함수는 상위 컴포넌트의 내부 함수입니다. "
        
        elif frag_type == 'api_call':
            api_service = metadata.get('api_service', '')
            http_method = metadata.get('http_method', '')
            
            # lifesub-web API 서비스 특화 설명
            if api_service == 'mySubscriptionApi':
                code_description += "이 코드는 구독 관리 API를 호출합니다. "
                if http_method == 'get':
                    code_description += "구독 정보를 조회합니다. "
                elif http_method == 'post':
                    code_description += "새로운 구독을 등록합니다. "
                elif http_method == 'delete':
                    code_description += "구독을 취소합니다. "
            elif api_service == 'authApi':
                code_description += "이 코드는 인증 관련 API를 호출합니다. "
                if http_method == 'post' and 'login' in content.lower():
                    code_description += "사용자 로그인을 처리합니다. "
                elif http_method == 'post' and 'logout' in content.lower():
                    code_description += "사용자 로그아웃을 처리합니다. "
            elif api_service == 'recommendApi':
                code_description += "이 코드는 구독 추천 API를 호출합니다. "
        
        elif frag_type == 'jsx_element':
            if 'Card' in name or 'Paper' in name:
                code_description += "이 JSX 요소는 카드 형태의 UI 컴포넌트를 렌더링합니다. "
            elif 'List' in name:
                code_description += "이 JSX 요소는 목록 형태의 UI를 렌더링합니다. "
            elif 'Button' in name:
                code_description += "이 JSX 요소는 버튼을 렌더링합니다. "
            elif 'Box' in name or 'Container' in name:
                code_description += "이 JSX 요소는 레이아웃 컨테이너입니다. "
        
        elif frag_type == 'mui_component':
            code_description += "이 코드는 Material UI 라이브러리의 컴포넌트를 사용합니다. "
            if 'Card' in content or 'Paper' in content:
                code_description += "Card 또는 Paper 컴포넌트로 콘텐츠를 그룹화합니다. "
            if 'Grid' in content:
                code_description += "Grid 시스템으로 레이아웃을 구성합니다. "
            if 'Typography' in content:
                code_description += "Typography 컴포넌트로 텍스트 스타일을 적용합니다. "
            if 'CircularProgress' in content:
                code_description += "로딩 상태를 표시하는 CircularProgress를 사용합니다. "
        
        elif frag_type == 'state_logic':
            if 'useState' in content:
                code_description += "이 코드는 React useState 훅을 사용하여 상태를 관리합니다. "
            if 'useEffect' in content:
                code_description += "이 코드는 React useEffect 훅을 사용하여 사이드 이펙트를 처리합니다. "
                
                # lifesub-web 특화 API 호출 패턴 감지
                if 'mySubscriptionApi' in content:
                    code_description += "구독 서비스 API를 호출합니다. "
                elif 'authApi' in content:
                    code_description += "인증 관련 API를 호출합니다. "
                elif 'recommendApi' in content:
                    code_description += "추천 서비스 API를 호출합니다. "
                
                dependencies = metadata.get('dependencies', [])
                if dependencies:
                    code_description += f"이 effect는 다음 의존성이 변경될 때 실행됩니다: {', '.join(dependencies[:3])}. "
        
        elif frag_type == 'routing':
            code_description += "이 코드는 React Router를 사용한 라우팅 관련 로직입니다. "
            router_api = metadata.get('router_api', '')
            if router_api == 'useNavigate':
                code_description += "페이지 이동 함수를 사용합니다. "
            elif router_api == 'useParams':
                code_description += "URL 파라미터를 추출합니다. "
            elif router_api == 'Route':
                code_description += "라우트 정의를 포함합니다. "
        
        elif frag_type == 'import_block':
            code_description += "이 코드는 import 문을 포함합니다. "
            libraries = metadata.get('libraries', {})
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
                
            if imported_libs:
                code_description += f"주요 라이브러리: {', '.join(imported_libs)}. "
        
        # 문맥 정보 구성 (기존 로직 확장)
        context_parts = []
        
        # 1. 기본 타입별 접두사
        if frag_type in self.context_keywords:
            context_parts.append(f"{' '.join(self.context_keywords[frag_type][:3])}")
        
        # 2. 이름과 메타데이터
        context_parts.append(f"{name}")
        
        # 3. 파일 경로 정보
        if file_name:
            context_parts.append(f"파일: {file_name}")
        
        # 4. 목적 정보
        purpose = metadata.get('purpose', '')
        if purpose and purpose in self.purpose_keywords:
            context_parts.append(f"목적: {purpose} {' '.join(self.purpose_keywords[purpose][:3])}")
        
        # 5. 타입별 추가 컨텍스트
        if frag_type == 'component':
            component_type = metadata.get('component_type', '')
            if component_type:
                context_parts.append(f"컴포넌트 타입: {component_type}")
            props = metadata.get('props', [])
            if props:
                context_parts.append(f"Props: {', '.join(props[:5])}")
                    
        elif frag_type == 'api_call':
            api_service = metadata.get('api_service', '')
            http_method = metadata.get('http_method', '')
            if api_service and http_method:
                context_parts.append(f"API: {api_service}.{http_method}")
                    
        elif frag_type == 'state_logic':
            dependencies = metadata.get('dependencies', [])
            if dependencies:
                context_parts.append(f"의존성: {', '.join(dependencies[:5])}")
                    
        elif frag_type == 'mui_component':
            context_parts.append("Material UI 컴포넌트")
        
        # 컨텍스트 결합
        context = ' | '.join(context_parts)
        
        # 최대 텍스트 길이 제한 (모델 한계 고려)
        max_description_length = 200  # 설명 최대 길이
        max_context_length = 150      # 컨텍스트 최대 길이
        max_content_length = 512 - max_description_length - max_context_length  # 컨텐츠 최대 길이
        
        if len(code_description) > max_description_length:
            code_description = code_description[:max_description_length]
            
        if len(context) > max_context_length:
            context = context[:max_context_length]
                
        if len(content) > max_content_length:
            content = content[:max_content_length]
        
        # 최종 임베딩 텍스트 생성
        embedding_text = f"{code_description}\n\n{context}\n\n{content}"
        
        return embedding_text