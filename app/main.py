"""
Backend-Fragmentor 메인 애플리케이션
React 코드 파편화 및 벡터화 서비스
"""

import os
import argparse
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from app.parser.vue_parser import parse_react_project
from app.fragmentation.fragmenter import ReactFragmenter
from app.embedding.engine import CodeEmbedder
from app.services.analyzer import SourceCodeAnalyzer
from app.services.indexing import IndexingService
from app.core.config import settings

# FastAPI 애플리케이션 초기화
app = FastAPI(
    title="Backend-Fragmentor",
    description="소스 코드 분석 및 분절화 서비스",
    version="0.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 실제 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 인스턴스 초기화
analyzer = SourceCodeAnalyzer()
indexing_service = IndexingService()

# 작업 상태 저장소
jobs_status = {}

# 모델 정의
class ProjectRequest(BaseModel):
    project_path: str
    options: Optional[Dict[str, Any]] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    message: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Backend-Fragmentor API 서비스"}

@app.post("/api/collect", response_model=Dict[str, str])
async def collect_source_code(project: ProjectRequest, background_tasks: BackgroundTasks):
    """소스 코드 수집 및 파싱 요청"""
    job_id = f"job_{os.urandom(4).hex()}"
    
    # 작업 상태 초기화
    jobs_status[job_id] = {
        "status": "pending",
        "progress": 0.0,
        "message": "작업 초기화 중"
    }
    
    # 백그라운드 작업으로 소스 코드 수집 실행
    background_tasks.add_task(
        indexing_service.process_project,
        project.project_path,
        job_id,
        jobs_status,
        project.options
    )
    
    return {"job_id": job_id}

@app.get("/api/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """작업 상태 확인"""
    if job_id not in jobs_status:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
    
    job_status = jobs_status[job_id]
    return {
        "job_id": job_id,
        "status": job_status["status"],
        "progress": job_status["progress"],
        "message": job_status.get("message")
    }

@app.post("/api/fragment")
async def fragment_code(code: str, options: Optional[Dict[str, Any]] = None):
    """코드 조각 파편화 및 임베딩 생성"""
    try:
        result = analyzer.fragment_code(code, options)
        return result
    except Exception as e:
        logger.error(f"코드 파편화 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파편화 처리 중 오류 발생: {str(e)}")

@app.get("/api/fragments/{fragment_id}")
async def get_fragment(fragment_id: str):
    """특정 파편 조회"""
    try:
        fragment = indexing_service.get_fragment(fragment_id)
        if not fragment:
            raise HTTPException(status_code=404, detail="파편을 찾을 수 없습니다")
        return fragment
    except Exception as e:
        logger.error(f"파편 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파편 조회 중 오류 발생: {str(e)}")

@app.get("/api/stats")
async def get_stats():
    """벡터 DB 통계 조회"""
    try:
        stats = indexing_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"통계 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류 발생: {str(e)}")

@app.post("/api/reset")
async def reset_database():
    """벡터 DB 초기화 (개발용)"""
    try:
        indexing_service.reset_database()
        return {"message": "데이터베이스가 초기화되었습니다"}
    except Exception as e:
        logger.error(f"DB 초기화 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB 초기화 중 오류 발생: {str(e)}")

def run_standalone():
    """
    스크립트로 직접 실행 시 작동하는 함수
    """
    parser = argparse.ArgumentParser(description='React 코드 파편화 및 벡터화 서비스')
    parser.add_argument('--project', type=str, help='React 프로젝트 디렉토리 경로')
    parser.add_argument('--data-dir', type=str, default='./data', help='데이터 저장 디렉토리')
    parser.add_argument('--search', action='store_true', help='대화형 검색 모드 실행')
    parser.add_argument('--query', type=str, help='단일 검색 쿼리 실행')
    
    args = parser.parse_args()
    
    # 프로젝트 처리 로직
    if args.project:
        logger.info(f"프로젝트 경로: {args.project}")
        if not os.path.exists(args.project):
            logger.error(f"프로젝트 경로를 찾을 수 없습니다: {args.project}")
            return
            
        # 프로젝트 처리
        job_id = f"job_{os.urandom(4).hex()}"
        jobs_status[job_id] = {
            "status": "running",
            "progress": 0.0,
            "message": "작업 시작"
        }
        
        result = indexing_service.process_project(
            args.project, 
            job_id, 
            jobs_status, 
            {"data_dir": args.data_dir}
        )
        
        # 검색 모드
        if args.search or args.query:
            try:
                from app.services.search import SearchService
                search_service = SearchService(data_dir=args.data_dir)
                
                if args.query:
                    # 단일 쿼리 검색
                    results = search_service.search(args.query)
                    for i, result in enumerate(results):
                        print(f"[{i+1}] {result['name']} ({result['type']}) - 유사도: {result['score']:.4f}")
                        print(f"  파일: {result['file_name']}")
                        print(f"  {result['content_preview'][:100]}...")
                else:
                    # 대화형 검색
                    search_service.run_interactive_search()
            except ImportError:
                logger.error("검색 서비스를 불러올 수 없습니다.")

if __name__ == "__main__":
    # 스크립트로 직접 실행된 경우
    run_standalone()
else:
    # 모듈로 임포트된 경우 (FastAPI에서 사용)
    pass