"""
React 코드 파편화 및 벡터화 POC 메인 스크립트
"""

import os
import sys
import argparse
import time
from typing import Dict, List, Any

from parser.jsx_parser import parse_react_project
from fragmenter.fragmenter import ReactFragmenter
from embedding.embedder import CodeEmbedder
from storage.faiss_store import FaissVectorStore

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

def process_project(project_path: str, data_dir: str = './data'):
    """
    React 프로젝트 처리 파이프라인:
    파싱 -> 파편화 -> 임베딩 -> 벡터 저장
    
    Args:
        project_path: React 프로젝트 디렉토리 경로
        data_dir: 데이터 저장 디렉토리
    """
    print(f"\n{'='*50}")
    print(f"React 프로젝트 파편화 및 벡터화 시작: {project_path}")
    print(f"{'='*50}\n")
    
    start_time = time.time()
    
    # 1. 디렉토리 설정
    data_dir = setup_directories(data_dir)
    embeddings_cache_dir = os.path.join(data_dir, 'embeddings')
    
    # 2. 프로젝트 파싱
    print("\n[1/4] 프로젝트 파싱 중...")
    parsed_project = parse_react_project(project_path)
    
    parsed_files_count = len(parsed_project['parsed_files'])
    print(f"  - 파싱된 파일: {parsed_files_count}개")
    print(f"  - 감지된 컴포넌트: {parsed_project['summary']['components_count']}개")
    print(f"  - 파일 확장자 분포: {parsed_project['summary']['file_extensions']}")
    
    # 3. 코드 파편화
    print("\n[2/4] 코드 파편화 중...")
    fragmenter = ReactFragmenter()
    fragmentation_result = fragmenter.fragment_project(parsed_project)
    
    fragments = fragmentation_result['fragments']
    fragment_stats = fragmentation_result['fragment_stats']
    
    print(f"  - 생성된 파편: {fragment_stats['total_count']}개")
    print(f"  - 파편 타입 분포: {fragment_stats['by_type']}")
    if 'by_component_type' in fragment_stats and fragment_stats['by_component_type']:
        print(f"  - 컴포넌트 타입 분포: {fragment_stats['by_component_type']}")
    
    # 4. 임베딩 생성
    print("\n[3/4] 임베딩 생성 중...")
    embedder = CodeEmbedder(model_name='all-MiniLM-L6-v2', cache_dir=embeddings_cache_dir)
    
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
        index_name='react_fragments'
    )
    
    vector_store.add_fragments(fragments, embeddings)
    
    # 6. 처리 결과 및 통계
    elapsed_time = time.time() - start_time
    stats = vector_store.get_stats()
    
    print(f"\n{'='*50}")
    print(f"처리 완료 (소요 시간: {elapsed_time:.2f}초)")
    print(f"{'='*50}")
    print(f"  - 저장된 벡터: {stats['vector_count']}개")
    print(f"  - 벡터 차원: {stats['dimension']}")
    print(f"  - 인덱스 타입: {stats['index_type']}")
    print(f"  - 파편 타입 분포: {stats['fragment_types']}")
    print(f"  - 처리된 파일 수: {len(stats['file_counts'])}")
    
    return {
        'vector_store': vector_store,
        'fragments': fragments,
        'embeddings': embeddings,
        'stats': stats
    }

def search_code(vector_store: FaissVectorStore, query: str, embedder: CodeEmbedder, k: int = 10):
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
    
    print(f"\n{'='*50}")
    print(f"검색 결과: '{query}'")
    print(f"{'='*50}")
    
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
            
        search_code(vector_store, query, embedder, k=5)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='React 코드 파편화 및 벡터화 POC')
    parser.add_argument('--project', type=str, required=True, help='React 프로젝트 디렉토리 경로')
    parser.add_argument('--data-dir', type=str, default='./data', help='데이터 저장 디렉토리')
    parser.add_argument('--search', action='store_true', help='대화형 검색 모드 실행')
    parser.add_argument('--query', type=str, help='단일 검색 쿼리 실행')
    
    args = parser.parse_args()
    
    # 프로젝트 경로 확인
    if not os.path.exists(args.project):
        print(f"오류: 프로젝트 경로를 찾을 수 없습니다: {args.project}")
        return 1
    
    # 프로젝트 처리
    result = process_project(args.project, args.data_dir)
    
    # 검색 모드
    if args.search or args.query:
        vector_store = result['vector_store']
        embedder = CodeEmbedder(model_name='all-MiniLM-L6-v2')
        
        if args.query:
            # 단일 쿼리 검색
            search_code(vector_store, args.query, embedder)
        else:
            # 대화형 검색
            run_interactive_search(vector_store, embedder)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())