"""
Cross-Encoder 기반 재랭킹 모듈
"""

import os
import json
import pickle
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer

class CrossEncoder:
    """
    질문-파편 쌍의 관련성을 평가하기 위한 Cross-Encoder
    """
    
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2', 
                 device: str = 'cpu',
                 cache_dir: Optional[str] = None,
                 max_seq_length: int = 512):
        """
        Args:
            model_name: Hugging Face 모델 이름
            device: 'cpu' 또는 'cuda'
            cache_dir: 캐싱 디렉토리
            max_seq_length: 최대 시퀀스 길이
        """
        self.model_name = model_name
        self.device = device
        self.max_seq_length = max_seq_length
        self.cache_dir = cache_dir
        
        # 캐시 디렉토리 설정
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
        
        # 모델 및 토크나이저 로드
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(device)
        
        # 평가 모드 설정
        self.model.eval()
        
    def score(self, query: str, passage: str) -> float:
        """
        질문과 파편 간의 관련성 점수 계산
        
        Args:
            query: 사용자 질문
            passage: 코드 파편 내용
            
        Returns:
            float: 관련성 점수 (높을수록 관련성 높음)
        """
        # 캐시 확인
        cache_key = self._create_cache_key(query, passage)
        cached_score = self._get_from_cache(cache_key)
        if cached_score is not None:
            return cached_score
        
        # 입력 인코딩
        features = self.tokenizer(
            query, 
            passage, 
            padding=True, 
            truncation='longest_first',
            max_length=self.max_seq_length, 
            return_tensors='pt'
        )
        
        # 모델에 입력 전달
        features = {key: val.to(self.device) for key, val in features.items()}
        
        # 모델 추론 (no_grad로 메모리 효율성 높이기)
        import torch
        with torch.no_grad():
            outputs = self.model(**features)
            scores = outputs.logits.detach().cpu().numpy()
            
            # 이진 분류 모델인 경우 첫 번째 레이블의 로짓 사용
            if len(scores[0]) == 2:
                score = float(scores[0][1])  # 긍정 클래스 로짓
            else:
                score = float(scores[0][0])  # 단일 점수
        
        # 캐시에 저장
        self._save_to_cache(cache_key, score)
        
        return score
    
    def rerank(self, query: str, passages: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        후보 파편들을 재랭킹
        
        Args:
            query: 사용자 질문
            passages: 후보 파편 목록 (1차 검색 결과)
            top_k: 반환할 상위 결과 수
            
        Returns:
            List[Dict]: 재랭킹된 결과 목록
        """
        if not passages:
            return []
            
        scores = []
        
        # 각 파편에 대한 점수 계산
        for passage in passages:
            content = passage.get('content_preview', '')
            score = self.score(query, content)
            scores.append((score, passage))
        
        # 점수 기준 내림차순 정렬
        ranked_results = sorted(scores, key=lambda x: x[0], reverse=True)
        
        # 스코어를 각 결과에 추가하고 상위 k개 반환
        results = []
        for score, passage in ranked_results[:top_k]:
            result = passage.copy()
            result['cross_score'] = float(score)  # Cross-Encoder 점수 추가
            results.append(result)
        
        return results
    
    def train_from_examples(self, examples_file: str, epochs: int = 3, batch_size: int = 16):
        """
        예제 데이터에서 파인튜닝
        
        Args:
            examples_file: 예제 데이터 파일 경로(JSON)
            epochs: 학습 에포크 수
            batch_size: 배치 크기
        """
        # 예제 데이터 로드
        with open(examples_file, 'r', encoding='utf-8') as f:
            examples = json.load(f)
        
        print(f"파인튜닝 데이터 {len(examples)}개 로드됨")
        
        # 학습 데이터 준비
        train_samples = []
        
        for example in examples:
            fragment_content = example.get('fragment_summary', '')
            questions = example.get('questions', [])
            
            for question in questions:
                # 긍정 예제 (질문-관련 파편)
                train_samples.append({
                    'query': question,
                    'passage': fragment_content,
                    'label': 1  # 관련 있음
                })
                
                # TODO: 부정 예제 추가 (다른 파편과 조합)
        
        print(f"총 {len(train_samples)}개 학습 데이터 생성됨")
        
        # TODO: 실제 파인튜닝 로직 구현 
        # (transformers의 Trainer 사용)
        
        print("모델 파인튜닝 완료")
    
    def _create_cache_key(self, query: str, passage: str) -> str:
        """캐시 키 생성"""
        import hashlib
        combined = query + "|" + passage
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[float]:
        """캐시에서 점수 가져오기"""
        if not self.cache_dir:
            return None
            
        cache_path = os.path.join(self.cache_dir, f"score_{cache_key}.pkl")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"캐시 로드 오류: {str(e)}")
                return None
        
        return None
    
    def _save_to_cache(self, cache_key: str, score: float) -> None:
        """점수를 캐시에 저장"""
        if not self.cache_dir:
            return
            
        cache_path = os.path.join(self.cache_dir, f"score_{cache_key}.pkl")
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(score, f)
        except Exception as e:
            print(f"캐시 저장 오류: {str(e)}")