"""
향상된 코드 임베딩(Embedding) 생성 모듈 - lifesub-web 프로젝트용
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Union, Optional
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

class LifesubEmbedder:
    """
    lifesub-web 코드 조각을 SentenceTransformer를 이용해 벡터로 변환
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', cache_dir: Optional[str] = None):
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
        단일 코드 파편 임베딩
        
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
                    return pickle.load(f)
        
        # 임베딩 생성을 위한 텍스트 구성
        embedding_text = self._prepare_embedding_text(fragment)
        
        # 임베딩 생성
        embedding = self.model.encode(embedding_text)
        
        # 캐시 저장
        if self.cache_dir:
            with open(cache_path, 'wb') as f:
                pickle.dump(embedding, f)
        
        return embedding
    
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
        
        print(f"총 {len(fragments)}개 파편 임베딩 생성 중...")
        
        # 캐시 확인 및 임베딩 필요한 파편 확인
        for fragment in fragments:
            fragment_id = fragment['id']
            
            # 캐시 확인
            if self.cache_dir:
                cache_path = os.path.join(self.cache_dir, f"{fragment_id}.pkl")
                if os.path.exists(cache_path):
                    with open(cache_path, 'rb') as f:
                        embeddings[fragment_id] = pickle.load(f)
                        continue
            
            # 임베딩 필요한 파편 추가
            embedding_text = self._prepare_embedding_text(fragment)
            texts_to_embed.append(embedding_text)
            ids_to_embed.append(fragment_id)
        
        # 임베딩이 필요한 것이 있을 경우만 처리
        if texts_to_embed:
            # 배치 처리
            for i in tqdm(range(0, len(texts_to_embed), batch_size)):
                batch_texts = texts_to_embed[i:i+batch_size]
                batch_ids = ids_to_embed[i:i+batch_size]
                
                # 배치 임베딩 생성
                batch_embeddings = self.model.encode(batch_texts)
                
                # 결과 저장 및 캐싱
                for j, fragment_id in enumerate(batch_ids):
                    embeddings[fragment_id] = batch_embeddings[j]
                    
                    # 캐시 저장
                    if self.cache_dir:
                        cache_path = os.path.join(self.cache_dir, f"{fragment_id}.pkl")
                        with open(cache_path, 'wb') as f:
                            pickle.dump(batch_embeddings[j], f)
        
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
        
        # 문맥 정보 구성
        context_parts = []
        
        # 1. 기본 타입별 접두사
        if frag_type in self.context_keywords:
            context_parts.append(f"{' '.join(self.context_keywords[frag_type][:2])}")
        
        # 2. 이름과 메타데이터
        context_parts.append(f"{name}")
        
        # 3. 파일 경로 정보
        file_name = metadata.get('file_name', '')
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
        max_context_length = 150  # 컨텍스트 최대 길이
        max_content_length = 512 - max_context_length  # 컨텐츠 최대 길이
        
        if len(context) > max_context_length:
            context = context[:max_context_length]
            
        if len(content) > max_content_length:
            content = content[:max_content_length]
        
        # 최종 임베딩 텍스트 생성
        embedding_text = f"{context}\n\n{content}"
        
        return embedding_text