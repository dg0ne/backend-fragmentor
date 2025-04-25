#!/usr/bin/env python
"""
FastAPI 기반 코드 검색 API 서버
중복 제거 로직이 포함된 검색 엔드포인트 구현
"""

import os
import sys
import time
import json
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 상대 경로 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parser.vue_parser import parse_vue_project
from app.fragmenter.fragmenter import VueFragmenter
from app.embedding.embedder import CodeEmbedder
from app.embedding.cross_encoder import CrossEncoder
from app.storage.faiss_store import FaissVectorStore

# FastAPI 앱 생성
app = FastAPI(
    title="Code Search API",
    description="코드 검색 API with 중복 제거 기능",
    version="1.0.0"
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수로 서비스 인스턴스 관리
vector_store = None
embedder = None
cross_encoder = None

# Pydantic 모델 정의
class SearchRequest(BaseModel):
    query: str = Field(..., description="검색 쿼리")
    k: int = Field(5, description="반환할 결과 수", ge=1, le=20)
    rerank: bool = Field(True, description="Cross-Encoder 재랭킹 여부")
    filters: Optional[Dict[str, Any]] = Field(None, description="검색 필터")
    ensemble_weight: float = Field(0.5, description="앙상블 가중치", ge=0.0, le=1.0)

class FragmentResult(BaseModel):
    id: str
    score: float
    cross_score: Optional[float] = None
    type: str
    name: str
    file_path: str
    relative_path: str  # 상대 경로 추가
    file_name: str
    content_preview: str
    component_name: Optional[str] = None
    
class SearchResponse(BaseModel):
    query: str
    total_results: int
    elapsed_time: float
    reranked: bool
    results: List[FragmentResult]

def deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    검색 결과에서 중복을 제거하는 함수
    Vue 파일의 component가 있으면 해당 파일의 template, script, style 파편 제거
    
    Args:
        results: 원본 검색 결과 리스트
        
    Returns:
        중복이 제거된 결과 리스트
    """
    # 파일별로 결과를 그룹화
    file_fragments = {}
    
    # 결과를 파일 경로별로 그룹화
    for result in results:
        file_path = result['file_path']
        if file_path not in file_fragments:
            file_fragments[file_path] = []
        file_fragments[file_path].append(result)
    
    # 중복 제거된 결과
    deduplicated_results = []
    
    # 각 파일에 대해 처리
    for file_path, fragments in file_fragments.items():
        # Vue 파일인 경우 특별 처리
        if file_path.endswith('.vue'):
            # 해당 파일의 component 파편이 있는지 확인
            component_fragment = None
            other_fragments = []
            
            for fragment in fragments:
                if fragment['type'] == 'component':
                    # component 파편이 있으면 가장 높은 점수의 것을 선택
                    if component_fragment is None or fragment['score'] > component_fragment['score']:
                        component_fragment = fragment
                else:
                    other_fragments.append(fragment)
            
            # component 파편이 있으면 그것만 추가
            if component_fragment:
                deduplicated_results.append(component_fragment)
            else:
                # component 파편이 없으면 모든 파편 추가
                deduplicated_results.extend(other_fragments)
        else:
            # Vue 파일이 아닌 경우 모든 파편 추가
            deduplicated_results.extend(fragments)
    
    # 최종 점수로 정렬 (cross_score가 있으면 우선, 없으면 score 사용)
    deduplicated_results.sort(
        key=lambda x: x.get('cross_score', x['score']), 
        reverse=True
    )
    
    return deduplicated_results

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 자원 초기화"""
    global vector_store, embedder, cross_encoder
    
    data_dir = os.getenv("DATA_DIR", "./data")
    
    # 임베더 초기화
    embedder = CodeEmbedder(model_name='dragonkue/BGE-m3-ko')
    cross_encoder_model = os.getenv("SeoJHeasdw/ktds-vue-code-search-reranker-ko")
    # Cross-Encoder 초기화
    try:
        cross_encoder = CrossEncoder(model_name=cross_encoder_model)
        print(f"Cross-Encoder 모델 로드 성공: {cross_encoder_model}")
    except Exception as e:
        print(f"Cross-Encoder 모델 로드 실패: {str(e)}")
        cross_encoder = None
    
    # Faiss 벡터 저장소 초기화
    vector_store = FaissVectorStore(
        dimension=embedder.vector_dim,
        index_type='Cosine',
        data_dir=data_dir,
        index_name='vue_todo_fragments',
        cross_encoder=cross_encoder
    )
    
    print(f"서버 초기화 완료 - 벡터 수: {vector_store.index.ntotal}")

@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "status": "ok",
        "service": "Code Search API",
        "version": "1.0.0",
        "vector_count": vector_store.index.ntotal if vector_store else 0,
        "cross_encoder_enabled": cross_encoder is not None
    }

@app.post("/search", response_model=SearchResponse)
async def search_code(request: SearchRequest):
    """
    코드 검색 API 엔드포인트
    
    Args:
        request: 검색 요청 정보
        
    Returns:
        검색 결과 (중복 제거됨)
    """
    if not vector_store or not embedder:
        raise HTTPException(status_code=503, detail="서비스 초기화되지 않음")
    
    start_time = time.time()
    
    # 검색 쿼리 임베딩 생성
    query_embedding = embedder.model.encode(request.query)
    
    # 필터 설정
    filters = request.filters or {}
    filters['query_text'] = request.query
    filters['ensemble_weight'] = request.ensemble_weight
    filters['rerank'] = request.rerank and cross_encoder is not None
    
    # 검색 실행 (k를 2배로 늘려서 중복 제거 후에도 충분한 결과가 남도록 함)
    search_k = request.k * 2
    results = vector_store.search(
        query_vector=query_embedding,
        k=search_k,
        filters=filters,
        rerank=request.rerank and cross_encoder is not None
    )
    
    # 중복 제거
    deduplicated_results = deduplicate_results(results)
    
    # 요청한 k개로 제한
    final_results = deduplicated_results[:request.k]
    
    elapsed_time = time.time() - start_time
    
    # 상대 경로 추가
    for result in final_results:
        # file_path에서 todo-web 이후의 경로만 추출
        full_path = result['file_path']
        try:
            todo_web_index = full_path.index('todo-web')
            relative_path = full_path[todo_web_index:]
        except ValueError:
            # todo-web이 없는 경우 전체 경로 사용
            relative_path = full_path
        result['relative_path'] = relative_path
    
    # 응답 형식으로 변환
    fragment_results = [
        FragmentResult(**result) for result in final_results
    ]
    
    return SearchResponse(
        query=request.query,
        total_results=len(final_results),
        elapsed_time=elapsed_time,
        reranked=request.rerank and cross_encoder is not None,
        results=fragment_results
    )

@app.get("/stats")
async def get_stats():
    """벡터 저장소 통계 정보"""
    if not vector_store:
        raise HTTPException(status_code=503, detail="서비스 초기화되지 않음")
    
    return vector_store.get_stats()

@app.get("/fragment/{fragment_id}")
async def get_fragment(fragment_id: str):
    """특정 파편 상세 정보 조회"""
    if not vector_store:
        raise HTTPException(status_code=503, detail="서비스 초기화되지 않음")
    
    metadata = vector_store.fragment_metadata.get(fragment_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="파편을 찾을 수 없음")
    
    return {
        "id": fragment_id,
        "metadata": metadata
    }

@app.get("/similar/{fragment_id}")
async def get_similar_fragments(
    fragment_id: str, 
    k: int = Query(5, ge=1, le=20),
    rerank: bool = Query(False)
):
    """특정 파편과 유사한 파편 검색"""
    if not vector_store:
        raise HTTPException(status_code=503, detail="서비스 초기화되지 않음")
    
    # 기본 유사 파편 검색
    similar_results = vector_store.get_similar_fragments(fragment_id, k=k*2)
    
    if not similar_results:
        raise HTTPException(status_code=404, detail="유사한 파편을 찾을 수 없음")
    
    # 재랭킹 적용
    if rerank and cross_encoder:
        current_metadata = vector_store.fragment_metadata.get(fragment_id, {})
        current_content = current_metadata.get('content_preview', '')
        
        similar_results = cross_encoder.rerank(
            query=current_content,
            passages=similar_results,
            top_k=k*2
        )
    
    # 중복 제거
    deduplicated_results = deduplicate_results(similar_results)
    
    # 요청한 k개로 제한
    final_results = deduplicated_results[:k]
    
    return {
        "fragment_id": fragment_id,
        "similar_fragments": final_results,
        "reranked": rerank and cross_encoder is not None
    }

@app.get("/file-fragments")
async def get_fragments_by_file(file_path: str):
    """특정 파일의 모든 파편 조회"""
    if not vector_store:
        raise HTTPException(status_code=503, detail="서비스 초기화되지 않음")
    
    results = vector_store.get_fragments_by_file(file_path)
    
    if not results:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없음")
    
    return {
        "file_path": file_path,
        "fragments": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)