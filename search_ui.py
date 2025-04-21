"""
lifesub-web 코드 검색 UI
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

from app.parser.jsx_parser import EnhancedJSXParser, parse_react_project
from app.fragmenter.fragmenter import ReactFragmenter
from app.embedding.embedder import CodeEmbedder
from app.storage.faiss_store import FaissVectorStore

# 색상 초기화
colorama.init()

class CodeSearchShell(cmd.Cmd):
    """대화형 코드 검색 인터페이스"""
    
    intro = f"{Fore.CYAN}lifesub-web 코드 검색 쉘에 오신 것을 환영합니다. 도움말을 보려면 'help'를 입력하세요.{Style.RESET_ALL}"
    prompt = f"{Fore.GREEN}코드검색> {Style.RESET_ALL}"
    
    def __init__(self, vector_store: FaissVectorStore, embedder: CodeEmbedder):
        super().__init__()
        self.vector_store = vector_store
        self.embedder = embedder
        self.last_results = []
        self.current_fragment_id = None
    
    def do_search(self, arg):
        """검색 쿼리를 입력하여 코드 파편 검색. 
        예: search 구독 서비스 리스트 컴포넌트
        필터링: search 로그인 처리 --type=function"""
        
        if not arg:
            print(f"{Fore.YELLOW}검색어를 입력하세요.{Style.RESET_ALL}")
            return
            
        # 필터 파싱
        filters = {}
        args = arg.split('--')
        query = args[0].strip()
        
        for filter_arg in args[1:]:
            if '=' in filter_arg:
                key, value = filter_arg.split('=', 1)
                filters[key.strip()] = value.strip()
        
        # 쿼리 임베딩 생성
        query_embedding = self.embedder.model.encode(query)
        
        # 검색 실행
        start_time = time.time()
        results = self.vector_store.search(query_embedding, k=10, filters=filters if filters else None)
        elapsed_time = time.time() - start_time
        
        if not results:
            print(f"{Fore.YELLOW}검색 결과가,  없습니다.{Style.RESET_ALL}")
            return
            
        # 결과 저장
        self.last_results = results
        
        # 결과 출력
        print(f"\n{Fore.CYAN}검색 결과: '{query}' (총 {len(results)}개, {elapsed_time:.3f}초){Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        for i, result in enumerate(results):
            print(f"\n{Fore.GREEN}[{i+1}] {result['name']} ({result['type']}){Style.RESET_ALL} - 유사도: {result['score']:.4f}")
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
                
                # 타입별 메타데이터 출력
                if result['type'] == 'component':
                    print(f"컴포넌트 타입: {metadata.get('component_type', 'unknown')}")
                    props = metadata.get('props', [])
                    if props:
                        print(f"Props: {', '.join(props)}")
                    purpose = metadata.get('purpose', '')
                    if purpose:
                        print(f"목적: {purpose}")
                elif result['type'] == 'api_call':
                    print(f"API 서비스: {metadata.get('api_service', '')}")
                    print(f"HTTP 메서드: {metadata.get('http_method', '')}")
                
                # 코드 콘텐츠
                if 'content_preview' in result:
                    print(f"\n{Fore.YELLOW}코드 미리보기:{Style.RESET_ALL}")
                    print(f"{result['content_preview']}")
                    
                print(f"\n{Fore.CYAN}관련 파편 보기: similar{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}유효한 인덱스 번호를 입력하세요. (1-{len(self.last_results)}){Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.YELLOW}유효한 숫자를 입력하세요.{Style.RESET_ALL}")
    
    def do_similar(self, arg):
        """현재 보고 있는 파편과 유사한 다른 파편 찾기."""
        
        if not self.current_fragment_id:
            print(f"{Fore.YELLOW}먼저 view 명령으로 파편을 선택하세요.{Style.RESET_ALL}")
            return
            
        similar_results = self.vector_store.get_similar_fragments(self.current_fragment_id, k=5)
        
        if not similar_results:
            print(f"{Fore.YELLOW}유사한 파편을 찾을 수 없습니다.{Style.RESET_ALL}")
            return
            
        print(f"\n{Fore.CYAN}유사한 파편 ({len(similar_results)}개):{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        for i, result in enumerate(similar_results):
            print(f"\n{Fore.GREEN}[{i+1}] {result['name']} ({result['type']}){Style.RESET_ALL} - 유사도: {result['score']:.4f}")
            print(f"  파일: {Fore.BLUE}{result['file_name']}{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}{result['content_preview']}{Style.RESET_ALL}")
            
        # 유사 결과를 마지막 결과로 업데이트
        self.last_results = similar_results
    
    def do_stats(self, arg):
        """벡터 저장소 통계 정보 출력."""
        
        stats = self.vector_store.get_stats()
        
        print(f"\n{Fore.CYAN}벡터 저장소 통계:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        print(f"총 벡터 수: {stats['vector_count']}")
        print(f"벡터 차원: {stats['dimension']}")
        print(f"인덱스 타입: {stats['index_type']}")
        
        print(f"\n{Fore.GREEN}파편 타입별 분포:{Style.RESET_ALL}")
        for type_name, count in stats['fragment_types'].items():
            print(f"  {type_name}: {count}개")
        
        if 'component_types' in stats:
            print(f"\n{Fore.GREEN}컴포넌트 타입별 분포:{Style.RESET_ALL}")
            for comp_type, count in stats['component_types'].items():
                print(f"  {comp_type}: {count}개")
        
        if 'categories' in stats:
            print(f"\n{Fore.GREEN}카테고리별 분포:{Style.RESET_ALL}")
            for category, count in stats['categories'].items():
                print(f"  {category}: {count}개")
        
        if 'purposes' in stats:
            print(f"\n{Fore.GREEN}목적별 분포:{Style.RESET_ALL}")
            for purpose, count in stats['purposes'].items():
                print(f"  {purpose}: {count}개")
    
    def do_file(self, arg):
        """특정 파일의 모든 파편 조회.
        예: file src/components/common/LoadingSpinner.js"""
        
        if not arg:
            print(f"{Fore.YELLOW}파일 경로를 입력하세요.{Style.RESET_ALL}")
            return
            
        results = self.vector_store.get_fragments_by_file(arg)
        
        if not results:
            print(f"{Fore.YELLOW}해당 파일의 파편을 찾을 수 없습니다: {arg}{Style.RESET_ALL}")
            return
            
        print(f"\n{Fore.CYAN}파일 '{arg}'의 파편 ({len(results)}개):{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        for i, result in enumerate(results):
            print(f"\n{Fore.GREEN}[{i+1}] {result['name']} ({result['type']}){Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}{result['content_preview']}{Style.RESET_ALL}")
            
        # 파일 파편 결과를 마지막 결과로 업데이트
        self.last_results = results
    
    def do_query(self, arg):
        """search 명령어의 별칭"""
        return self.do_search(arg)
    
    def do_exit(self, arg):
        """검색 쉘 종료"""
        print(f"{Fore.CYAN}lifesub-web 코드 검색을 종료합니다.{Style.RESET_ALL}")
        return True
        
    def do_quit(self, arg):
        """exit의 별칭"""
        return self.do_exit(arg)
        
    def do_q(self, arg):
        """exit의 별칭"""
        return self.do_exit(arg)
    
    def default(self, line):
        """알 수 없는 명령어 처리"""
        if line.strip():
            print(f"{Fore.YELLOW}알 수 없는 명령어: {line}{Style.RESET_ALL}")
            print(f"도움말을 보려면 'help'를 입력하세요.")

def run_search_ui(data_dir: str = './data'):
    """
    코드 검색 UI 실행
    
    Args:
        data_dir: 데이터 디렉토리 경로
    """
    try:
        # 임베더 초기화
        embedder = CodeEmbedder(model_name='microsoft/codebert-base')
        
        # 인덱스 로드
        vector_store = FaissVectorStore(
            dimension=embedder.vector_dim,
            index_type='Cosine',
            data_dir=data_dir,
            index_name='lifesub_web_fragments'
        )
        
        if vector_store.index.ntotal == 0:
            print(f"{Fore.RED}오류: 인덱스가 비어 있습니다. 먼저 lifesub_fragmentor.py를 실행하여 인덱스를 생성하세요.{Style.RESET_ALL}")
            return
            
        # 검색 UI 실행
        search_shell = CodeSearchShell(vector_store, embedder)
        search_shell.cmdloop()
    
    except Exception as e:
        print(f"{Fore.RED}오류 발생: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='lifesub-web 코드 검색 UI')
    parser.add_argument('--data-dir', type=str, default='./data', help='데이터 저장 디렉토리')
    
    args = parser.parse_args()
    run_search_ui(args.data_dir)