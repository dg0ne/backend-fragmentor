#!/usr/bin/env python
"""
FastAPI 기반 코드 검색 API 서버
중복 제거 로직이 포함된 검색 엔드포인트 구현
"""

import os
import sys
import time
import json
import httpx
from typing import Dict, List, Any, Optional, Union 
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

# 두 번째 백엔드 URL 환경 변수에서 로드
SECOND_BACKEND_URL = "http://codecooking-backend.20.214.196.128.nip.io/workflow/fragment/save-result"

# Pydantic 모델 정의
class SearchRequest(BaseModel):
    query: str = Field(..., description="검색 쿼리")
    k: int = Field(5, description="반환할 결과 수", ge=1, le=20)
    rerank: bool = Field(True, description="Cross-Encoder 재랭킹 여부")
    filters: Optional[Dict[str, Any]] = Field(None, description="검색 필터")
    ensemble_weight: float = Field(0.5, description="앙상블 가중치", ge=0.0, le=1.0)
    # requirementId를 Optional[Union[int, str]]로 수정하여 정수 또는 문자열 모두 허용
    requirementId: Optional[Union[int, str]] = Field(None, description="요구사항 ID")

class FragmentResult(BaseModel):
    id: str
    score: float
    cross_score: Optional[float] = None
    type: str
    name: str
    relative_path: str
    file_name: str
    content: str  # 전체 내용
    content_preview: str  # 미리보기 내용 (추가)
    component_name: Optional[str] = None
    
class SearchResponse(BaseModel):
    query: str
    total_results: int
    elapsed_time: float
    reranked: bool
    requirementId: Optional[int] = None
    results: List[FragmentResult]

# 두 번째 백엔드를 위한 모델
class SecondBackendFragmentResult(BaseModel):
    id: str
    score: float
    cross_score: Optional[float] = None
    type: str
    name: str
    relative_path: str
    file_name: str
    content_preview: str  # content 대신 content_preview 사용
    component_name: Optional[str] = None
    
class SecondBackendSearchResponse(BaseModel):
    query: str
    total_results: int
    elapsed_time: float
    reranked: bool
    requirementId: Optional[int] = None
    results: List[SecondBackendFragmentResult]

def remove_unnecessary_fragments(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    검색 결과에서 불필요한 파편을 제거하는 함수
    - 각 파일당 component 타입이 있으면 그것만 유지
    - component가 없는 파일은 모든 파편 유지
    
    Args:
        results: 원본 검색 결과 리스트
        
    Returns:
        불필요한 파편이 제거된 결과 리스트
    """
    # 파일별로 파편 그룹화
    file_fragments = {}
    
    for result in results:
        file_path = result['file_path']
        if file_path not in file_fragments:
            file_fragments[file_path] = []
        file_fragments[file_path].append(result)
    
    # 각 파일에서 대표 파편 선택
    final_results = []
    
    for file_path, fragments in file_fragments.items():
        # component 타입이 있는지 확인
        component_fragments = [f for f in fragments if f['type'] == 'component']
        
        if component_fragments:
            # component 파편이 있으면 그것만 추가
            best_component = max(
                component_fragments, 
                key=lambda x: x.get('cross_score', x['score'])
            )
            final_results.append(best_component)
        else:
            # component가 없으면 모든 파편 추가
            final_results.extend(fragments)
    
    return final_results

async def send_to_second_backend(query: str, results: List[Dict[str, Any]], elapsed_time: float, reranked: bool, requirement_id: Optional[Union[int, str]] = None):
    """
    두 번째 백엔드로 검색 결과 전송
    
    Args:
        query: 검색 쿼리
        results: 원본 검색 결과 (필터링되지 않은)
        elapsed_time: 검색 소요 시간
        reranked: 재랭킹 적용 여부
        requirement_id: 요구사항 ID (정수 또는 문자열)
    """
    try:
        # 결과 가공
        fragment_results = []
        for idx, result in enumerate(results):
            # 상대 경로 추가
            full_path = result['file_path']
            try:
                todo_web_index = full_path.index('todo-web')
                relative_path = full_path[todo_web_index:]
            except ValueError:
                relative_path = full_path
            
            # 메타데이터에서 정보 가져오기
            metadata = vector_store.fragment_metadata.get(result['id'], {})
            
            # content_preview 처리
            content_preview = result.get('content_preview', '')
            if not content_preview or isinstance(content_preview, int):
                content_preview = metadata.get('content_preview', '')
                if not content_preview:
                    full_content = metadata.get('full_content', '')
                    content_preview = (full_content[:150] + "...") if len(full_content) > 150 else full_content
            
            # 결과 항목 생성
            fragment_result = {
                'id': result['id'],
                'score': result['score'],
                'cross_score': result.get('cross_score'),
                'type': result['type'],
                'name': result['name'],
                'relative_path': relative_path,
                'file_name': result['file_name'],
                'content_preview': content_preview,
                'component_name': metadata.get('component_name', '')
            }
            
            # 첫 번째 결과 항목에 대한 상세 로그 (디버깅용)
            if idx == 0:
                print(f"첫 번째 결과 항목 상세: {json.dumps(fragment_result, ensure_ascii=False)}")
            
            fragment_results.append(fragment_result)
        
        # 두 번째 백엔드에 전송할 응답 구성
        response_data = {
            'query': query,
            'total_results': len(fragment_results),
            'elapsed_time': elapsed_time,
            'reranked': reranked,
            'requirementId': requirement_id,  # null 또는 실제 값 그대로 전달
            'results': fragment_results
        }
        
        # 디버깅을 위한 JSON 로그 (결과 배열은 length만 표시)
        log_data = response_data.copy()
        log_data['results'] = f"[{len(fragment_results)} items]"
        print(f"두 번째 백엔드 전송 데이터: {json.dumps(log_data, ensure_ascii=False)}")
        
        # 첫 번째 결과 항목의 content_preview 길이 확인 (디버깅용)
        if fragment_results:
            preview = fragment_results[0].get('content_preview', '')
            print(f"첫 번째 결과의 content_preview 길이: {len(preview)}, 타입: {type(preview)}")
        
        # 비동기 HTTP 클라이언트로 두 번째 백엔드에 전송
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SECOND_BACKEND_URL,
                json=response_data,
                timeout=5.0  # 타임아웃 5초로 설정
            )
            print(f"두 번째 백엔드 응답 코드: {response.status_code}")
            print(f"두 번째 백엔드 응답 헤더: {response.headers}")
            
            # 응답 내용이 있는 경우 로깅
            if response.text:
                # 너무 길지 않게 처음 200자만 로깅
                print(f"두 번째 백엔드 응답 내용: {response.text[:200]}...")
            
    except Exception as e:
        print(f"두 번째 백엔드 전송 오류 (무시됨): {str(e)}")
        import traceback
        print(traceback.format_exc())

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 자원 초기화"""
    global vector_store, embedder, cross_encoder
    
    data_dir = os.getenv("DATA_DIR", "./data")
    
    # 임베더 초기화
    embedder = CodeEmbedder(model_name='dragonkue/BGE-m3-ko')
    
    # Cross-Encoder 초기화
    cross_encoder_model = "SeoJHeasdw/ktds-vue-code-search-reranker-ko"
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
    """
    if not vector_store or not embedder:
        raise HTTPException(status_code=503, detail="서비스 초기화되지 않음")
    
    # 디버깅을 위한 로그 추가
    print(f"검색 요청 데이터: {request.dict()}")
    
    start_time = time.time()
    
    # 검색 쿼리 임베딩 생성
    query_embedding = embedder.model.encode(request.query)
    
    # 필터 설정
    filters = request.filters or {}
    filters['query_text'] = request.query
    filters['ensemble_weight'] = request.ensemble_weight
    filters['rerank'] = request.rerank and cross_encoder is not None
    
    # 검색 실행
    results = vector_store.search(
        query_vector=query_embedding,
        k=request.k,
        filters=filters,
        rerank=request.rerank and cross_encoder is not None
    )
    
    elapsed_time = time.time() - start_time
    
    # 두 번째 백엔드로 원본 결과 전송 (비동기)
    if SECOND_BACKEND_URL:
        try:
            await send_to_second_backend(
                query=request.query,
                results=results,
                elapsed_time=elapsed_time,
                requirement_id=request.requirementId,
                reranked=request.rerank and cross_encoder is not None
            )
        except Exception as e:
            print(f"두 번째 백엔드 전송 오류 (무시됨): {str(e)}")
            # 오류가 발생해도 계속 진행
    
    # 불필요한 파편 제거 (component 우선)
    filtered_results = remove_unnecessary_fragments(results)
    
    # 결과 가공
    fragment_results = []
    for result in filtered_results:
        # 상대 경로 추가
        full_path = result['file_path']
        try:
            todo_web_index = full_path.index('todo-web')
            relative_path = full_path[todo_web_index:]
        except ValueError:
            relative_path = full_path
        
        # 메타데이터에서 전체 컨텐츠 가져오기
        metadata = vector_store.fragment_metadata.get(result['id'], {})
        full_content = metadata.get('full_content', '')
        
        # content_preview 필드 확인 및 수정
        content_preview = result.get('content_preview', '')
        if not content_preview or isinstance(content_preview, int):
            # 메타데이터에서 content_preview를 다시 가져오거나 생성
            content_preview = metadata.get('content_preview', '')
            if not content_preview:
                # 전체 내용이 있으면 처음 150자를 미리보기로 사용
                content_preview = (full_content[:150] + "...") if len(full_content) > 150 else full_content
        
        # 컴포넌트 이름 추가
        component_name = metadata.get('component_name', '')
        
        # 최종 결과 생성
        fragment_results.append(FragmentResult(
            id=result['id'],
            score=result['score'],
            cross_score=result.get('cross_score'),
            type=result['type'],
            name=result['name'],
            relative_path=relative_path,
            file_name=result['file_name'],
            content=full_content,
            content_preview=content_preview,
            component_name=component_name
        ))
    
    return SearchResponse(
        query=request.query,
        total_results=len(fragment_results),
        elapsed_time=elapsed_time,
        reranked=request.rerank and cross_encoder is not None,
        requirementId=request.requirementId,
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