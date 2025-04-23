# Vue 코드 파편화 및 검색 개선 방안

## 현재 시스템 분석

### 파편화 구조
현재 Vue 컴포넌트를 4가지 단위로 파편화하는 접근법:
- **component**: 컴포넌트 전체
- **template**: 템플릿 섹션
- **script**: 스크립트 섹션
- **style**: 스타일 섹션

이 구조는 Vue SFC(Single File Component)의 실제 구성을 자연스럽게 반영하여 효과적입니다.

### 현재 검색 메커니즘
- **Bi-Encoder 기반 벡터 검색**: 'jhgan/ko-sroberta-multitask' 모델 사용
- **앙상블 검색 기법**: 벡터 검색과 키워드 검색을 결합하여 검색 품질 향상
- **메타데이터 보강**: 파편 간의 관계 및 컨텍스트 정보 유지

## 검색 정확도 향상 전략

### 현재 한계점
- Bi-Encoder 기반 검색은 속도가 빠르지만 정확한 의미 매칭에 한계가 있음
- 사용자 요구사항과 코드 파편 간의 정교한 매칭이 필요

### 제안: 2단계 검색 파이프라인

#### 1. Bi-Encoder 앙상블 검색 (기존)
- 빠른 1차 후보군 선별
- 광범위한 관련 파편 확보

#### 2. Cross-Encoder 재랭킹 (추가)
- 사용자 질문 ↔ 파편 간의 직접적인 관계 평가
- 더 정확한 의미적 매칭 제공

```python
def rerank_with_cross_encoder(query, candidates, cross_encoder_model, top_k=3):
    """Cross-Encoder를 사용하여 후보군 재랭킹"""
    pairs = [[query, candidate['content_preview']] for candidate in candidates]
    scores = cross_encoder_model.predict(pairs)
    
    # 스코어와 후보를 결합하고 정렬
    scored_candidates = list(zip(scores, candidates))
    reranked = sorted(scored_candidates, key=lambda x: x[0], reverse=True)
    
    return [item[1] for item in reranked[:top_k]]
```

### 모델 선택 제안
- **Bi-Encoder (기존)**: 'jhgan/ko-sroberta-multitask'
- **Cross-Encoder (추가)**: 'cross-encoder/ms-marco-MiniLM-L-6-v2' 또는 한국어 최적화 모델

## 장단점 분석

### 장점
- **정확도 향상**: 사용자 질문과 코드 파편 간의 의미적 일치도 상승
- **구현 용이성**: 기존 아키텍처에 모듈로 추가 가능
- **실시간 성능 유지**: 1차 검색으로 후보군을 제한하여 계산 비용 관리

### 단점
- **추가 계산 비용**: Cross-Encoder는 각 (질문, 파편) 쌍마다 개별 추론 필요
- **시스템 복잡성 증가**: 추가 모델 관리 및 2단계 파이프라인 구현

## 장기적 개선 방향

### 파인튜닝 전략
- 사용자 질문-파편 매칭 데이터 수집
- Vue 코드에 특화된 도메인 특화 임베딩 모델 훈련
- 실제 사용 패턴 기반 모델 개선

### 구현 로드맵
1. **즉시**: Cross-Encoder 재랭킹 추가 (단기 정확도 향상)
2. **중기**: 사용 데이터 수집 및 분석
3. **장기**: 도메인 특화 임베딩 모델 파인튜닝

## 결론

Vue 코드 파편화의 현재 구조(component, script, style, template)는 매우 효과적이며, 앙상블 검색 기법은 좋은 기반을 제공합니다. Cross-Encoder 재랭킹을 추가하는 것이 정확도와 구현 용이성 측면에서 최선의 접근법으로 판단됩니다. 이는 시스템의 핵심 목표인 "정확한 소스 파편 탐지"를 향상시키는 데 직접적으로 기여할 것입니다.