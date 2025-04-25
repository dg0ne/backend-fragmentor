"""
Vue Todo 코드 검색 UI (Cross-Encoder 재랭킹 기능 추가)
"""

import os
import sys
import cmd
import argparse
import time
import json
from typing import Dict, List, Any, Optional
import colorama
from colorama import Fore, Style

# 상대 경로 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parser.vue_parser import parse_vue_project
from app.fragmenter.fragmenter import VueFragmenter
from app.embedding.embedder import CodeEmbedder
from app.embedding.cross_encoder import CrossEncoder
from app.storage.faiss_store import FaissVectorStore

# 색상 초기화
colorama.init()

class CodeSearchShell(cmd.Cmd):
    """대화형 코드 검색 인터페이스"""
    
    intro = f"{Fore.CYAN}Vue Todo 코드 검색 쉘에 오신 것을 환영합니다. 도움말을 보려면 'help'를 입력하세요.{Style.RESET_ALL}"
    prompt = f"{Fore.GREEN}코드검색> {Style.RESET_ALL}"
    
    def __init__(self, vector_store: FaissVectorStore, embedder: CodeEmbedder, cross_encoder=None):
        super().__init__()
        self.vector_store = vector_store
        self.embedder = embedder
        self.cross_encoder = cross_encoder
        self.last_results = []
        self.current_fragment_id = None
        self.rerank_enabled = cross_encoder is not None
    
    def do_search(self, arg):
        """검색 쿼리를 입력하여 코드 파편 검색. 
        예: search 할일 목록 컴포넌트
        필터링: search 로그인 처리 --type=component
        재랭킹: search 할일 추가 --rerank (Cross-Encoder 사용)"""
        
        if not arg:
            print(f"{Fore.YELLOW}검색어를 입력하세요.{Style.RESET_ALL}")
            return
            
        # 필터 파싱
        filters = {}
        args = arg.split('--')
        query = args[0].strip()
        
        # 재랭킹 옵션 기본값
        rerank = self.rerank_enabled
        
        for filter_arg in args[1:]:
            if '=' in filter_arg:
                key, value = filter_arg.split('=', 1)
                filters[key.strip()] = value.strip()
            else:
                # 단일 플래그 처리
                flag = filter_arg.strip()
                if flag == 'rerank':
                    rerank = True
                elif flag == 'norerank':
                    rerank = False
        
        # Cross-Encoder가 없으면 재랭킹 비활성화
        if rerank and not self.cross_encoder:
            print(f"{Fore.YELLOW}경고: Cross-Encoder 모델이 로드되지 않아 재랭킹을 사용할 수 없습니다.{Style.RESET_ALL}")
            rerank = False
        
        # 쿼리 임베딩 생성
        query_embedding = self.embedder.model.encode(query)
        
        # 앙상블 검색을 위해 원본 쿼리 텍스트도 필터에 추가
        filters['query_text'] = query
        
        # 앙상블 가중치 설정 (기본값 0.5)
        if 'weight' in filters:
            try:
                filters['ensemble_weight'] = float(filters.pop('weight'))
            except (ValueError, TypeError):
                pass
        
        # 재랭킹 옵션 추가
        filters['rerank'] = rerank
        
        # 검색 실행
        start_time = time.time()
        results = self.vector_store.search(
            query_vector=query_embedding,
            k=5, 
            filters=filters if filters else None,
            rerank=rerank
        )

        elapsed_time = time.time() - start_time
        
        if not results:
            print(f"{Fore.YELLOW}검색 결과가 없습니다.{Style.RESET_ALL}")
            return
                
        # 결과 저장
        self.last_results = results
        
        # 결과 출력
        print(f"\n{Fore.CYAN}검색 결과: '{query}' (총 {len(results)}개, {elapsed_time:.3f}초){Style.RESET_ALL}")
        if rerank:
            print(f"{Fore.MAGENTA}[Cross-Encoder 재랭킹 적용됨]{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        for i, result in enumerate(results):
            # 기본 점수 표시
            score_text = f"유사도: {result['score']:.4f}"
            
            # Cross-Encoder 점수가 있으면 함께 표시
            if 'cross_score' in result:
                score_text += f" | 재랭킹 점수: {result['cross_score']:.4f}"
                
            print(f"\n{Fore.GREEN}[{i+1}] {result['name']} ({result['type']}){Style.RESET_ALL} - {score_text}")
            print(f"  파일: {Fore.BLUE}{result['file_name']}{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}{result['content_preview']}{Style.RESET_ALL}")


    def do_view(self, arg):
        """검색 결과 항목 자세히 보기. 
        예: view 2"""
        
        if not self.last_results:
            print(f"{Fore.YELLOW}먼저 검색을 실행하세요.{Style.RESET_ALL}")
            return
            
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(self.last_results):
                result = self.last_results[idx]
                self.current_fragment_id = result['id']
                
                # 메타데이터 가져오기
                metadata = self.vector_store.fragment_metadata.get(result['id'], {})
                
                print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}[{idx+1}] {result['name']} ({result['type']}){Style.RESET_ALL}")
                print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                
                print(f"파일: {Fore.BLUE}{result['file_path']}{Style.RESET_ALL}")
                
                # 점수 정보 표시
                print(f"벡터 유사도: {result['score']:.4f}")
                if 'cross_score' in result:
                    print(f"재랭킹 점수: {result['cross_score']:.4f}")
                
                # 타입별 메타데이터 출력
                if result['type'] == 'component':
                    print(f"컴포넌트 타입: {metadata.get('component_type', 'unknown')}")
                    props = metadata.get('props', [])
                    if props:
                        print(f"Props: {', '.join(props)}")
                
                # 코드 콘텐츠
                if 'content_preview' in result:
                    print(f"\n{Fore.YELLOW}코드 미리보기:{Style.RESET_ALL}")
                    print(f"{result['content_preview']}")
            else:
                print(f"{Fore.YELLOW}유효한 인덱스 번호를 입력하세요. (1-{len(self.last_results)}){Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.YELLOW}유효한 숫자를 입력하세요.{Style.RESET_ALL}")
    
    def do_exit(self, arg):
        """프로그램 종료"""
        print(f"{Fore.CYAN}프로그램을 종료합니다.{Style.RESET_ALL}")
        return True
        
    def do_quit(self, arg):
        """프로그램 종료"""
        return self.do_exit(arg)

# 메인 함수 정의
def main():
    parser = argparse.ArgumentParser(description='Vue Todo 코드 검색 인터페이스')
    parser.add_argument('--data-dir', type=str, default='./data', help='데이터 디렉토리 경로')
    parser.add_argument('--model', type=str, default='SeoJHeasdw/ktds-vue-code-search-reranker-ko', 
                        help='Cross-Encoder 모델 (HuggingFace 모델 ID 또는 로컬 경로)')
    
    args = parser.parse_args()
    
    # 데이터 디렉토리 확인
    data_dir = args.data_dir  # 하이픈이 언더스코어로 변환됨
    if not os.path.exists(data_dir):
        print(f"{Fore.YELLOW}경고: 데이터 디렉토리가 존재하지 않습니다: {data_dir}{Style.RESET_ALL}")
        print("데이터 디렉토리를 생성합니다.")
        os.makedirs(data_dir, exist_ok=True)
    
    try:
        # 임베더 초기화
        embedder = CodeEmbedder(model_name='dragonkue/BGE-m3-ko')
        
        # Cross-Encoder 초기화 (있는 경우)
        cross_encoder = None
        try:
            cross_encoder = CrossEncoder(model_name=args.model)
            print(f"{Fore.GREEN}Cross-Encoder 모델 로드 성공: {args.model}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}Cross-Encoder 모델 로드 실패: {str(e)}{Style.RESET_ALL}")
            print("재랭킹 기능 없이 계속합니다.")
        
        # Faiss 벡터 저장소 초기화
        vector_store = FaissVectorStore(
            dimension=embedder.vector_dim,
            index_type='Cosine',
            data_dir=data_dir,
            index_name='vue_todo_fragments',
            cross_encoder=cross_encoder
        )
        
        # 인터페이스 실행
        shell = CodeSearchShell(vector_store, embedder, cross_encoder)
        shell.cmdloop()
    except Exception as e:
        print(f"{Fore.RED}오류 발생: {str(e)}{Style.RESET_ALL}")
        import traceback
        print(traceback.format_exc())
    
    return 0

# 메인 함수 실행
if __name__ == "__main__":
    sys.exit(main())