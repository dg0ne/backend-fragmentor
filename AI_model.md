# 모델 정리

---

## 🔁 Bi-Encoder 모델

| 구분        | 모델명                                      | 설명 |
|------------|---------------------------------------------|------|
| 최초 모델   | `all-MiniLM-L6-v2`                          | 6개 Transformer 레이어로 구성된 경량 모델 (10M 파라미터), 다국어 지원, 빠른 추론. 의료 데이터셋에서 0.9375 정확도.<br>❗ 복잡한 의미 분석에서 BERT 기반보다 성능 낮을 수 있음. |
| 이전 모델   | `snunlp/KR-SBERT-V40K-klueNLI-augSTS`       | KLUE 기반 한국어 특화. NLI/STS에 강점. 검색에 안정적.<br>❗ 40K 어휘 제한, 구어체 처리 성능 저하 가능성. |
| 현재 모델   | `jhgan/ko-sroberta-multitask`               | RoBERTa 기반 멀티태스크 학습. 의도 분류/감정 분석에 최적화. 768차원 임베딩 제공.<br>❗ 모델 크기로 인한 추론 속도 감소 가능성. |
| 특이사항    | 👉 Vue 코드(500줄 미만) 대응 성능 최고 |

---

## 🔀 Cross-Encoder 모델

| 구분              | 모델명                                           | 설명 |
|------------------|--------------------------------------------------|------|
| 초기 모델         | `cross-encoder/ms-marco-MiniLM-L-6-v2`           | MS Marco 기준 74.3 NDCG@10, 1800 docs/sec 처리.<br>❗ 3000개 문서 재정렬 시 latency 증가(6–7초). |
| 현재 모델         | `dragonkue/bge-reranker-v2-m3-ko`                | MIRACL 한국어 평가 74.83점. 다국어 지원, 경량화 BGE 시리즈.<br>❗ 초대형 모델보다 정밀도 낮음. |
| 다운그레이드 필요시 | `bongsoo/albert-small-kor-cross-encoder-v1`      | ALBERT-small 기반(13M 파라미터), KorSTS 0.8455 기록.<br>❗ 대형 모델 대비 정확도 약 4% 낮음. |

---

dragonkue/BGE-m3-ko 로 변경중...

## ✅ 참고 요약

- Vue에 특화된 Bi-Encoder 모델: **`jhgan/ko-sroberta-multitask`**
- 검색/질문 매칭 특화: **`BAAI/bge-m3`**
- 빠른 재정렬 + 다국어: **`dragonkue/bge-reranker-v2-m3-ko`**
- 경량화 대안: **`bongsoo/albert-small-kor-cross-encoder-v1`**
