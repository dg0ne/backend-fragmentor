#!/usr/bin/env python
"""
Vue Todo 애플리케이션 파편화 스크립트
"""

import os
import sys
import argparse
import time
from typing import Dict, List, Any
import json

# 상대 경로 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parser.vue_parser import parse_vue_project
from app.fragmenter.fragmenter import VueFragmenter
from app.embedding.embedder import CodeEmbedder
from app.storage.faiss_store import FaissVectorStore

def setup_directories(base_dir: str = './data'):
    """필요한 디렉토리 생성"""
    dirs = [
        os.path.join(base_dir, 'faiss'),
        os.path.join(base_dir, 'metadata'),
        os.path.join(base_dir, 'embeddings'),
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    return base_dir

def process_vue_todo(project_path: str, data_dir: str = './data'):
    """
    Vue Todo 프로젝트 처리 파이프라인:
    파싱 -> 파편화 -> 임베딩 -> 벡터 저장
    
    Args:
        project_path: Vue Todo 프로젝트 디렉토리 경로
        data_dir: 데이터 저장 디렉토리
    """
    print(f"\n{'='*60}")
    print(f" Vue Todo 프로젝트 파편화 및 벡터화 시작: {project_path}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    # 1. 디렉토리 설정
    data_dir = setup_directories(data_dir)
    embeddings_cache_dir = os.path.join(data_dir, 'embeddings')
    
    # 2. 프로젝트 파싱
    print("\n[1/4] 프로젝트 파싱 중...")
    parsed_project = parse_vue_project(project_path)
    
    parsed_files_count = len(parsed_project['parsed_files'])
    print(f"  - 파싱된 파일: {parsed_files_count}개")
    print(f"  - 감지된 컴포넌트: {parsed_project['summary']['components_count']}개")
    print(f"  - 파일 확장자 분포: {parsed_project['summary']['file_extensions']}")
    
    # 3. 코드 파편화
    print("\n[2/4] 코드 파편화 중...")
    fragmenter = VueFragmenter()
    fragmentation_result = fragmenter.fragment_project(parsed_project)
    
    fragments = fragmentation_result['fragments']
    fragment_stats = fragmentation_result['fragment_stats']
    
    print(f"  - 생성된 파편: {fragment_stats['total_count']}개")
    print(f"  - 파편 타입 분포: {fragment_stats['by_type']}")
    if 'by_component_type' in fragment_stats and fragment_stats['by_component_type']:
        print(f"  - 컴포넌트 타입 분포: {fragment_stats['by_component_type']}")
    
    # 4. 임베딩 생성
    print("\n[3/4] 임베딩 생성 중...")
    embedder = CodeEmbedder(model_name='dragonkue/BGE-m3-ko', cache_dir=embeddings_cache_dir)
    
    print(f"  - 모델: {embedder.model_name}")
    print(f"  - 벡터 차원: {embedder.vector_dim}")
    
    embeddings = embedder.embed_fragments(fragments)
    print(f"  - 생성된 임베딩: {len(embeddings)}개")
    
    # 5. Faiss 벡터 저장
    print("\n[4/4] 벡터 저장소에 저장 중...")
    vector_store = FaissVectorStore(
        dimension=embedder.vector_dim,
        index_type='Cosine',  # 코사인 유사도 사용
        data_dir=data_dir,
        index_name='vue_todo_fragments'
    )
    
    vector_store.add_fragments(fragments, embeddings)
    
    # 6. 처리 결과 및 통계
    elapsed_time = time.time() - start_time
    stats = vector_store.get_stats()
    
    print(f"\n{'='*60}")
    print(f" 처리 완료 (소요 시간: {elapsed_time:.2f}초)")
    print(f"{'='*60}")
    print(f"  - 저장된 벡터: {stats['vector_count']}개")
    print(f"  - 벡터 차원: {stats['dimension']}")
    print(f"  - 인덱스 타입: {stats['index_type']}")
    
    # 파일 수 출력
    if isinstance(stats['file_counts'], int):
        print(f"  - 처리된 파일 수: {stats['file_counts']}")
    else:
        print(f"  - 처리된 파일 수: {len(stats['file_counts'])}")
    
    # 파편 타입 분포가 있는 경우에만 출력
    if 'fragment_types' in stats:
        print(f"  - 파편 타입 분포: {stats['fragment_types']}")
    
    return {
        'vector_store': vector_store,
        'fragments': fragments,
        'embeddings': embeddings,
        'stats': stats
    }

def search_vue_code(vector_store: FaissVectorStore, query: str, embedder: CodeEmbedder, k: int = 5):
    """
    쿼리 텍스트를 이용해 유사한 코드 파편 검색
    
    Args:
        vector_store: Faiss 벡터 저장소
        query: 검색 쿼리 텍스트
        embedder: 임베딩 생성기
        k: 검색 결과 수
    """
    # 쿼리 임베딩 생성
    query_embedding = embedder.model.encode(query)
    
    # 유사한 코드 파편 검색
    results = vector_store.search(query_embedding, k=k)
    
    print(f"\n{'='*60}")
    print(f" 검색 결과: '{query}'")
    print(f"{'='*60}")
    
    if not results:
        print("일치하는 결과가 없습니다.")
        return []
    
    # 결과 출력
    for i, result in enumerate(results):
        print(f"\n[{i+1}] 파편 ID: {result['id']} (유사도 점수: {result['score']:.4f})")
        print(f"  - 타입: {result['type']}")
        print(f"  - 이름: {result['name']}")
        print(f"  - 파일: {result['file_name']}")
        print(f"  - 내용 미리보기: {result['content_preview']}")
    
    return results

def run_interactive_search(vector_store: FaissVectorStore, embedder: CodeEmbedder):
    """대화형 검색 인터페이스"""
    print("\n대화형 검색 모드를 시작합니다. 종료하려면 'exit' 또는 'quit'를 입력하세요.")
    
    while True:
        query = input("\n>> 검색어를 입력하세요: ").strip()
        
        if query.lower() in ['exit', 'quit', 'q']:
            print("검색을 종료합니다.")
            break
            
        if not query:
            continue
            
        search_vue_code(vector_store, query, embedder, k=5)

def load_preexisting_index(data_dir: str):
    """
    기존에 생성된 인덱스가 있다면 로드
    
    Args:
        data_dir: 데이터 디렉토리 경로
    
    Returns:
        tuple: (vector_store, embedder) 또는 None
    """
    try:
        # Faiss 인덱스 파일 경로
        index_path = os.path.join(data_dir, 'faiss', 'vue_todo_fragments.index')
        if not os.path.exists(index_path):
            return None
            
        # 임베더 초기화
        embedder = CodeEmbedder(model_name='dragonkue/BGE-m3-ko', normalize_embeddings=True)
        
        # 벡터 스토어 초기화 (기존 인덱스 로드)
        vector_store = FaissVectorStore(
            dimension=embedder.vector_dim,
            index_type='Cosine',
            data_dir=data_dir,
            index_name='vue_todo_fragments'
        )
        
        if vector_store.index.ntotal > 0:
            print(f"\n기존 인덱스 로드됨 (벡터 수: {vector_store.index.ntotal})")
            return (vector_store, embedder)
        
        return None
    except Exception as e:
        print(f"인덱스 로드 실패: {str(e)}")
        return None

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Vue Todo 코드 파편화 및 벡터화')
    parser.add_argument('--project', type=str, help='Vue Todo 프로젝트 디렉토리 경로')
    parser.add_argument('--data-dir', type=str, default='./data', help='데이터 저장 디렉토리')
    parser.add_argument('--search', action='store_true', help='대화형 검색 모드 실행')
    parser.add_argument('--query', type=str, help='단일 검색 쿼리 실행')
    parser.add_argument('--reload', action='store_true', help='기존 인덱스 무시하고 다시 처리')
    
    args = parser.parse_args()
    data_dir = os.path.abspath(args.data_dir)
    
    # 검색만 수행하는 경우
    if (args.search or args.query) and not args.project:
        # 기존 인덱스 로드
        loaded_data = load_preexisting_index(data_dir)
        if loaded_data:
            vector_store, embedder = loaded_data
            
            if args.query:
                # 단일 쿼리 검색
                search_vue_code(vector_store, args.query, embedder)
            else:
                # 대화형 검색
                run_interactive_search(vector_store, embedder)
            return 0
        else:
            print("기존 인덱스를 찾을 수 없습니다. --project 옵션을 사용해 먼저 인덱스를 생성하세요.")
            return 1
    
    # 프로젝트 경로가 필요한 경우
    if not args.project:
        print("오류: --project 인자가 필요합니다. Vue Todo 프로젝트 경로를 지정하세요.")
        return 1
        
    project_path = os.path.abspath(args.project)
    
    # 프로젝트 경로 확인
    if not os.path.exists(project_path):
        print(f"오류: 프로젝트 경로를 찾을 수 없습니다: {project_path}")
        return 1
    
    # 기존 인덱스 확인
    if not args.reload:
        loaded_data = load_preexisting_index(data_dir)
        if loaded_data and not args.reload:
            vector_store, embedder = loaded_data
            print("기존 인덱스를 재사용합니다. 인덱스를 새로 만들려면 --reload 옵션을 사용하세요.")
            
            if args.query:
                # 단일 쿼리 검색
                search_vue_code(vector_store, args.query, embedder)
            elif args.search:
                # 대화형 검색
                run_interactive_search(vector_store, embedder)
                
            return 0
    
    # 프로젝트 처리 (파싱, 파편화, 임베딩, 저장)
    result = process_vue_todo(project_path, data_dir)
    
    # 검색 모드
    if args.search or args.query:
        vector_store = result['vector_store']
        embedder = CodeEmbedder(model_name='dragonkue/BGE-m3-ko')
        
        if args.query:
            # 단일 쿼리 검색
            search_vue_code(vector_store, args.query, embedder)
        else:
            # 대화형 검색
            run_interactive_search(vector_store, embedder)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())