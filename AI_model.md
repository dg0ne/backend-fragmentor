# 모델 정리
https://github.com/su-park/mteb_ko_leaderboard  참고
---

## 🔁 Bi-Encoder 모델

| 구분        | 모델명                                      | 설명 |
|------------|---------------------------------------------|------|
| 최초 모델   | `all-MiniLM-L6-v2`                          | 6개 Transformer 레이어로 구성된 경량 모델 (10M 파라미터), 다국어 지원, 빠른 추론. 의료 데이터셋에서 0.9375 정확도.<br>❗ 복잡한 의미 분석에서 BERT 기반보다 성능 낮을 수 있음. |
| 이전 모델   | `jhgan/ko-sroberta-multitask`       | RoBERTa 기반 멀티태스크 학습(의도 분류+감정 분석). 768차원 임베딩 제공. |
| 현재 모델   | `dragonkue/BGE-m3-ko`               | BGE-m3 기반 한국어 최적화. 밀집/희소/멀티벡터 통합 검색 지원. 8,192 토큰 장문 처리
✅ FP16 양자화 시 3.3GB 메모리 사용. 재랭킹 모델과의 호환성 우수. |

---

## 🔀 Cross-Encoder 모델

| 구분              | 모델명                                           | 설명 |
|------------------|--------------------------------------------------|------|
| 초기 모델         | `cross-encoder/ms-marco-MiniLM-L-6-v2`           | MS Marco 기준 74.3 NDCG@10, 1800 docs/sec 처리.<br>❗ 3000개 문서 재정렬 시 latency 증가(6–7초). |
| 현재 모델         | `dragonkue/bge-reranker-v2-m3-ko`                | MIRACL 한국어 평가 74.83점. 다국어 지원, 경량화 BGE 시리즈.<br>❗ 초대형 모델보다 정밀도 낮음.|


---

 로 변경중...

## ✅ 참고 요약

- Vue에 특화된 Bi-Encoder 모델: **`jhgan/ko-sroberta-multitask`**
- 검색/질문 매칭 특화: **`BAAI/bge-m3`**
- 빠른 재정렬 + 다국어: **`dragonkue/bge-reranker-v2-m3-ko`**
- 경량화 대안: **`bongsoo/albert-small-kor-cross-encoder-v1`**
