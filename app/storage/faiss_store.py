"""
Faiss 벡터 저장소 모듈
"""

import os
import json
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any, Optional, Tuple, Set

class FaissVectorStore:
    """
    Faiss를 사용한 코드 임베딩 벡터 저장소
    """
    
    def __init__(self, 
                 dimension: int, 
                 index_type: str = 'Cosine',
                 data_dir: str = './data',
                 index_name: str = 'vue_todo_fragments'):
        """
        Args:
            dimension: 벡터 차원 수
            index_type: 인덱스 타입 ('L2', 'IP', 'Cosine')
            data_dir: 데이터 저장 디렉토리
            index_name: 인덱스 이름
        """
        self.dimension = dimension
        self.index_type = index_type
        self.data_dir = data_dir
        self.index_name = index_name
        
        # 저장 디렉토리 생성
        self.index_dir = os.path.join(data_dir, 'faiss')
        self.meta_dir = os.path.join(data_dir, 'metadata')
        
        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.meta_dir, exist_ok=True)
        
        # 인덱스 파일 경로
        self.index_path = os.path.join(self.index_dir, f"{index_name}.index")
        self.id_map_path = os.path.join(self.meta_dir, f"{index_name}_id_map.pkl")
        self.metadata_path = os.path.join(self.meta_dir, f"{index_name}_metadata.json")
        
        # 내부 상태
        self.index = None
        self.id_to_idx = {}  # fragment_id -> faiss_idx 매핑
        self.idx_to_id = {}  # faiss_idx -> fragment_id 매핑
        self.fragment_metadata = {}  # fragment_id -> metadata 매핑
        
        # 인덱스 초기화 또는 로드
        self._init_index()
    
    def _init_index(self):
        """인덱스 초기화 또는 기존 인덱스 로드"""
        # 기존 인덱스가 있으면 로드
        if os.path.exists(self.index_path) and os.path.exists(self.id_map_path):
            self._load_index()
        else:
            # 새 인덱스 생성
            self._create_index()
    
    def _create_index(self):
        """인덱스 새로 생성"""
        if self.index_type == 'L2':
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == 'IP':
            self.index = faiss.IndexFlatIP(self.dimension)
        elif self.index_type == 'Cosine':
            # 코사인 유사도를 위한 인덱스 (벡터 정규화 필요)
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            # 기본값으로 L2 거리 사용
            self.index = faiss.IndexFlatL2(self.dimension)
            
        print(f"새 Faiss 인덱스 생성 완료 (차원: {self.dimension}, 타입: {self.index_type})")
    
    def _load_index(self):
        """기존 인덱스 및 메타데이터 로드"""
        try:
            # Faiss 인덱스 로드
            self.index = faiss.read_index(self.index_path)
            
            # ID 매핑 로드
            with open(self.id_map_path, 'rb') as f:
                data = pickle.load(f)
                self.id_to_idx = data.get('id_to_idx', {})
                self.idx_to_id = data.get('idx_to_id', {})
            
            # 메타데이터 JSON 파일에서 로드
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.fragment_metadata = json.load(f)
                
            print(f"Faiss 인덱스 로드 완료 (벡터 수: {self.index.ntotal})")
            
        except Exception as e:
            print(f"인덱스 로드 실패: {str(e)}")
            self._create_index()
    
    def _save_index(self):
        """인덱스 및 메타데이터 저장"""
        try:
            # Faiss 인덱스 저장
            faiss.write_index(self.index, self.index_path)
            
            # ID 매핑 저장
            with open(self.id_map_path, 'wb') as f:
                pickle.dump({
                    'id_to_idx': self.id_to_idx,
                    'idx_to_id': self.idx_to_id
                }, f)
            
            # 메타데이터 별도 저장
            self._save_metadata()
                
            print(f"Faiss 인덱스 저장 완료 (벡터 수: {self.index.ntotal})")
            
        except Exception as e:
            print(f"인덱스 저장 실패: {str(e)}")
    
    def _save_metadata(self):
        """메타데이터만 별도 저장 (JSON 형식)"""
        try:
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.fragment_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"메타데이터 저장 실패: {str(e)}")
    
    def add_fragments(self, fragments: List[Dict[str, Any]], embeddings: Dict[str, np.ndarray]):
        """
        코드 파편 및 임베딩을 인덱스에 추가
        
        Args:
            fragments: 코드 파편 목록
            embeddings: fragment_id를 키로 하는 임베딩 딕셔너리
        """
        # 추가할 벡터와 ID 준비
        vectors = []
        fragment_ids = []
        
        for fragment in fragments:
            fragment_id = fragment['id']
            
            # 이미 있는 fragment_id는 건너뛰기
            if fragment_id in self.id_to_idx:
                continue
                
            # 임베딩이 없는 경우 건너뛰기
            if fragment_id not in embeddings:
                print(f"경고: ID {fragment_id}의 임베딩이 없습니다.")
                continue
                
            # 벡터 추가
            vector = embeddings[fragment_id]
            
            # 코사인 유사도를 위한 정규화 (필요 시)
            if self.index_type == 'Cosine':
                vector = vector / np.linalg.norm(vector)
                
            vectors.append(vector)
            fragment_ids.append(fragment_id)
            
            # 메타데이터 저장
            self.fragment_metadata[fragment_id] = self._extract_metadata(fragment)
        
        if not vectors:
            print("추가할 새 벡터가 없습니다.")
            return
            
        # Faiss 인덱스에 벡터 추가
        vectors_array = np.array(vectors).astype('float32')
        start_idx = self.index.ntotal
        
        self.index.add(vectors_array)
        
        # ID 매핑 업데이트
        for i, fragment_id in enumerate(fragment_ids):
            idx = start_idx + i
            self.id_to_idx[fragment_id] = idx
            self.idx_to_id[idx] = fragment_id
            
        print(f"{len(vectors)}개 벡터 추가 완료 (현재 총 {self.index.ntotal}개)")
        
        # 인덱스 저장
        self._save_index()
    
    def _extract_metadata(self, fragment: Dict[str, Any]) -> Dict[str, Any]:
        """
        검색에 필요한 메타데이터 추출 (저장 크기 최적화)
        
        Args:
            fragment: 코드 파편
            
        Returns:
            Dict[str, Any]: 추출된 메타데이터
        """
        metadata = {
            'type': fragment['type'],
            'name': fragment['name'],
            'file_path': fragment['metadata'].get('file_path', ''),
            'file_name': fragment['metadata'].get('file_name', ''),
            'content_preview': fragment['content'][:150] + '...' if len(fragment['content']) > 150 else fragment['content']
        }
        
        # 타입별 추가 메타데이터
        if fragment['type'] == 'component':
            metadata.update({
                'component_name': fragment['metadata'].get('component_name', ''),
                'props': fragment['metadata'].get('props', [])[:5],
                'components': fragment['metadata'].get('components', [])[:5]
            })
        
        return metadata
    
    def search(self, query_vector: np.ndarray, k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        쿼리 벡터와 유사한 코드 파편 검색 (필터링 지원)
        
        Args:
            query_vector: 쿼리 벡터
            k: 반환할 결과 수
            filters: 필터링 조건 (예: {'type': 'component'})
            
        Returns:
            List[Dict]: 검색 결과 목록
        """
        if self.index.ntotal == 0:
            return []
            
        # 코사인 유사도를 위한 정규화 (필요 시)
        if self.index_type == 'Cosine':
            query_vector = query_vector / np.linalg.norm(query_vector)
            
        # 벡터 형식 변환
        query_vector = np.array([query_vector]).astype('float32')
        
        # 필터링이 필요한 경우 더 많은 결과를 가져와서 후처리
        search_k = k
        if filters:
            search_k = min(k * 5, self.index.ntotal)  # 필터링을 위해 더 많은 후보 검색
            
        # 검색 실행
        distances, indices = self.index.search(query_vector, search_k)
        
        # 결과 변환 및 필터링
        results = []
        for i, idx in enumerate(indices[0]):
            # 유효한 인덱스가 아닌 경우 건너뛰기
            if idx == -1 or idx not in self.idx_to_id:
                continue
                
            fragment_id = self.idx_to_id[idx]
            metadata = self.fragment_metadata.get(fragment_id, {})
            
            # 필터 적용
            if filters and not self._apply_filters(metadata, filters):
                continue
                
            # IP 유사도는 높을수록 좋고, L2 거리는 낮을수록 좋음
            # 따라서 거리를 점수로 변환 (L2 거리인 경우 음수로 변환)
            score = distances[0][i]
            if self.index_type == 'L2':
                score = -score
                
            results.append({
                'id': fragment_id,
                'score': float(score),
                'type': metadata.get('type', ''),
                'name': metadata.get('name', ''),
                'file_path': metadata.get('file_path', ''),
                'file_name': metadata.get('file_name', ''),
                'content_preview': metadata.get('content_preview', '')
            })
            
            # 충분한 결과를 얻었으면 종료
            if len(results) >= k:
                break
                
        return results
    
    def _apply_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        메타데이터에 필터 적용
        
        Args:
            metadata: 메타데이터
            filters: 필터 조건
            
        Returns:
            bool: 필터 통과 여부
        """
        for key, value in filters.items():
            if key not in metadata:
                return False
                
            if isinstance(value, list):
                # 리스트인 경우 하나라도 일치하면 통과
                if metadata[key] not in value:
                    return False
            elif isinstance(metadata[key], list):
                # 메타데이터가 리스트인 경우 (props 등)
                if value not in metadata[key]:
                    return False
            elif metadata[key] != value:
                return False
                
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        벡터 저장소 통계 정보
        
        Returns:
            Dict: 통계 정보
        """
        type_counts = {}
        file_counts = set()  # 중복 없이 파일 경로 저장하기 위해 set 사용
        component_names = set()
        
        for fragment_id, metadata in self.fragment_metadata.items():
            # 타입별 카운트
            frag_type = metadata.get('type', 'unknown')
            if frag_type in type_counts:
                type_counts[frag_type] += 1
            else:
                type_counts[frag_type] = 1
                
            # 파일별 카운트
            file_path = metadata.get('file_path', '')
            if file_path:
                file_counts.add(file_path)
                
            # 컴포넌트별 카운트
            if frag_type == 'component':
                component_name = metadata.get('component_name', '')
                if component_name:
                    component_names.add(component_name)
        
        return {
            'vector_count': self.index.ntotal,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'fragment_types': type_counts,
            'file_counts': len(file_counts),
            'component_count': len(component_names)
        }
    
    def get_fragments_by_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        특정 파일의 모든 파편 검색
        
        Args:
            file_path: 파일 경로
            
        Returns:
            List[Dict]: 파편 목록
        """
        results = []
        
        for fragment_id, metadata in self.fragment_metadata.items():
            if metadata.get('file_path') == file_path:
                idx = self.id_to_idx.get(fragment_id)
                if idx is not None:
                    results.append({
                        'id': fragment_id,
                        'type': metadata.get('type', ''),
                        'name': metadata.get('name', ''),
                        'file_path': metadata.get('file_path', ''),
                        'file_name': metadata.get('file_name', ''),
                        'content_preview': metadata.get('content_preview', '')
                    })
                    
        return results
    
    def get_similar_fragments(self, fragment_id: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        특정 파편과 유사한 다른 파편 검색
        
        Args:
            fragment_id: 기준 파편 ID
            k: 반환할 결과 수
            
        Returns:
            List[Dict]: 유사한 파편 목록
        """
        # 파편 ID가 인덱스에 없는 경우
        if fragment_id not in self.id_to_idx:
            return []
            
        # 기준 파편의 인덱스와 벡터 가져오기
        idx = self.id_to_idx[fragment_id]
        vector = self.index.reconstruct(idx)
        
        # 자기 자신을 제외한 유사 파편 검색
        results = self.search(vector, k=k+1)
        
        # 자기 자신 제거
        return [r for r in results if r['id'] != fragment_id]
    
    def save(self):
        """인덱스 명시적 저장"""
        self._save_index()
    
    def clear(self):
        """인덱스 초기화"""
        self._create_index()
        self.id_to_idx = {}
        self.idx_to_id = {}
        self.fragment_metadata = {}
        self._save_index()
        print("인덱스가 초기화되었습니다.")