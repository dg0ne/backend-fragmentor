# upload_model_card.py
from huggingface_hub import HfApi, login

# Hugging Face 로그인
login()

# API 초기화
api = HfApi()

# 모델 카드 내용 직접 작성
model_card_content = """---
language: ko
license: mit
tags:
- vue
- code-search
- cross-encoder
- korean
- reranking
- ktds
datasets:
- custom-vue-code-dataset
base_model: dragonkue/bge-reranker-v2-m3-ko
---

# KT DS Vue Code Search Reranker (Korean)

이 모델은 KT DS에서 Vue.js 프로젝트의 코드 검색을 위해 파인튜닝한 Cross-Encoder입니다.

## 모델 설명
- **개발자**: SeoJHeasdw (KT DS)
- **기반 모델**: [dragonkue/bge-reranker-v2-m3-ko](https://huggingface.co/dragonkue/bge-reranker-v2-m3-ko)
- **용도**: Vue.js 컴포넌트와 관련 코드 검색 결과 재랭킹
- **학습 데이터**: Vue.js 프로젝트 코드베이스
- **지원 언어**: 한국어

## 사용 방법
```""" + """python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

model = AutoModelForSequenceClassification.from_pretrained("SeoJHeasdw/ktds-vue-code-search-reranker-ko")
tokenizer = AutoTokenizer.from_pretrained("SeoJHeasdw/ktds-vue-code-search-reranker-ko")
""" + """```

## 특징
- Vue SFC (Single File Component) 구조에 최적화
- 컴포넌트, 템플릿, 스크립트, 스타일 섹션 이해
- 한국어 코드 주석 및 변수명 처리 강화
- KT DS 내부 Vue 프로젝트 구조에 최적화

## 성능
- 1차 검색 후 재랭킹으로 검색 정확도 향상
- Vue 컴포넌트 관련 질의 처리에 특화
"""

# README.md 파일로 업로드
api.upload_file(
    path_or_fileobj=model_card_content.encode(),
    path_in_repo="README.md",
    repo_id="SeoJHeasdw/ktds-vue-code-search-reranker-ko",
    repo_type="model"
)

print("모델 카드가 성공적으로 업로드되었습니다!")