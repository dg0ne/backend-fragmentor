#!/usr/bin/env python
"""
Cross-Encoder 모델 추가 학습 스크립트
"""

import os
import sys
import json
import argparse
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    TrainingArguments, 
    Trainer
)
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# 상대 경로 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CrossEncoderDataset(Dataset):
    """Cross-Encoder 학습용 데이터셋"""
    def __init__(self, tokenizer, query_passage_pairs, labels, max_length=512):
        self.tokenizer = tokenizer
        self.query_passage_pairs = query_passage_pairs
        self.labels = labels
        self.max_length = max_length
        
    def __len__(self):
        return len(self.query_passage_pairs)
    
    def __getitem__(self, index):
        query, passage = self.query_passage_pairs[index]
        label = self.labels[index]
        
        encoding = self.tokenizer(
            query, 
            passage, 
            padding='max_length',
            truncation='longest_first',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        encoding = {key: val.squeeze(0) for key, val in encoding.items()}
        encoding['labels'] = torch.tensor(label, dtype=torch.float)
        
        return encoding

def prepare_training_data(examples_file, negative_ratio=3):
    """새로운 학습 데이터 준비"""
    with open(examples_file, 'r', encoding='utf-8') as f:
        examples = json.load(f)
    
    print(f"추가 학습 데이터 {len(examples)}개 로드됨")
    
    # 모든 파편 수집
    all_fragments = {}
    for example in examples:
        fragment_type = example['fragment_type']
        fragment_path = example['fragment_path']
        fragment_summary = example['fragment_summary']
        
        fragment_id = f"{fragment_type}:{fragment_path}"
        all_fragments[fragment_id] = fragment_summary
    
    # 학습 데이터 준비
    query_passage_pairs = []
    labels = []
    
    for example in examples:
        fragment_type = example['fragment_type']
        fragment_path = example['fragment_path']
        fragment_summary = example['fragment_summary']
        fragment_id = f"{fragment_type}:{fragment_path}"
        questions = example.get('questions', [])
        
        for question in questions:
            # 긍정 예제
            query_passage_pairs.append((question, fragment_summary))
            labels.append(1)
            
            # 부정 예제 생성
            negative_fragments = []
            fragments_ids = list(all_fragments.keys())
            np.random.shuffle(fragments_ids)
            
            for other_frag_id in fragments_ids:
                if other_frag_id != fragment_id and len(negative_fragments) < negative_ratio:
                    negative_fragments.append(all_fragments[other_frag_id])
            
            for neg_fragment in negative_fragments:
                query_passage_pairs.append((question, neg_fragment))
                labels.append(0)
    
    print(f"총 {len(query_passage_pairs)}개 학습 데이터 생성됨")
    print(f"- 긍정 샘플: {labels.count(1)}개")
    print(f"- 부정 샘플: {labels.count(0)}개")
    
    return query_passage_pairs, labels

def continue_training(
    examples_file='cross_encoding_additional.json',
    model_dir='./trained_cross_encoder',
    output_dir='./trained_cross_encoder_v2',
    epochs=3,
    checkpoint_num=282
):
    """기존 모델에 추가 학습"""
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 학습 데이터 준비
    query_passage_pairs, labels = prepare_training_data(examples_file)
    
    # 훈련/검증 데이터 분할
    train_pairs, val_pairs, train_labels, val_labels = train_test_split(
        query_passage_pairs, labels, test_size=0.1, random_state=42, stratify=labels
    )
    
    print(f"훈련 데이터: {len(train_pairs)}개")
    print(f"검증 데이터: {len(val_pairs)}개")
    
    # 기존 모델 및 토크나이저 로드
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    print(f"기존 모델 로드됨: {model_dir}")
    
    # 데이터셋 생성
    train_dataset = CrossEncoderDataset(tokenizer, train_pairs, train_labels)
    val_dataset = CrossEncoderDataset(tokenizer, val_pairs, val_labels)
    
    # 학습 인자 설정 (RTX 4090 + 안정성 우선)
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,  # 3 epochs as default
        per_device_train_batch_size=4,  # 안정적으로 동작했던 배치 사이즈
        per_device_eval_batch_size=4,   # 평가도 동일한 배치 사이즈
        gradient_accumulation_steps=4,  # 효과적으로 배치 사이즈 16
        warmup_steps=50,                # 데이터셋 크기를 고려하여 조정
        weight_decay=0.01,
        logging_dir=f"{output_dir}/logs",
        logging_steps=5,                # 더 자주 로깅
        eval_strategy="steps",
        eval_steps=50,                  # 50 스텝마다 평가
        save_strategy="steps",
        save_steps=50,                  # 50 스텝마다 저장
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        greater_is_better=False,
        fp16=True,                      # RTX 4090에서 FP16 활용
        dataloader_num_workers=4,       # 안정성을 위해 적절히 조정
        disable_tqdm=False,
        learning_rate=1e-5,             # 안전한 학습률
        max_grad_norm=1.0,              # 그래디언트 클리핑
        save_total_limit=3,             # 체크포인트 개수 제한
        optim="adamw_torch",            # 최적화된 옵티마이저
        lr_scheduler_type="cosine",     # 코사인 스케줄러
    )
    
    # 트레이너 초기화
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
    )
    
    # 체크포인트에서 이어서 학습
    checkpoint_path = os.path.join(model_dir, f"checkpoint-{checkpoint_num}")
    if os.path.exists(checkpoint_path):
        print(f"체크포인트에서 이어서 학습: {checkpoint_path}")
        trainer.train(resume_from_checkpoint=checkpoint_path)
    else:
        print(f"체크포인트를 찾을 수 없음: {checkpoint_path}")
        print("처음부터 학습 시작...")
        trainer.train()
    
    # 모델 저장
    print(f"모델 저장 중: {output_dir}")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print("추가 학습 완료!")
    print(f"새로운 모델이 저장됨: {output_dir}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Cross-Encoder 모델 추가 학습')
    parser.add_argument('--examples', type=str, default='cross_encoding_additional.json', help='추가 학습 데이터 파일')
    parser.add_argument('--model-dir', type=str, default='./trained_cross_encoder', help='기존 모델 디렉토리')
    parser.add_argument('--output-dir', type=str, default='./trained_cross_encoder_v2', help='새 모델 저장 디렉토리')
    parser.add_argument('--epochs', type=int, default=3, help='추가 학습 에포크 수')
    parser.add_argument('--checkpoint', type=int, default=282, help='이어서 학습할 체크포인트 번호')
    
    args = parser.parse_args()
    
    # 추가 학습 실행
    continue_training(
        examples_file=args.examples,
        model_dir=args.model_dir,
        output_dir=args.output_dir,
        epochs=args.epochs,
        checkpoint_num=args.checkpoint
    )
    
    return 0

if __name__ == "__main__":
    sys.exit(main())