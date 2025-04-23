Bi-Encoder 모델
최초 모델 : all-MiniLM-L6-v2
이전 모델 : snunlp/KR-SBERT-V40K-klueNLI-augSTS
현재 모델 : jhgan/ko-sroberta-multitask

모델 정보
1. BAAI/bge-m3
검색 성능 특화: 8K 토큰 길이 지원과 다중 언어 기능을 갖춘 검색 최적화 모델

코드-질문 매칭 강점: 코드 구조와 사용자 질문 간의 의미적 관계 파악에 우수

2. jhgan/ko-sroberta-multitask  <<< 가장 vue에 최적화(500줄 미만의 코드에서 제일 월등한 성능보장)
한국어 최적화: KorSTS 벤치마크에서 85.6 스피어만 상관계수 기록

멀티태스크 학습: 코드 문맥 이해와 자연어 질문 매칭에 효과적

cross encoding 모델
초기 모델 : cross-encoder/ms-marco-MiniLM-L-6-v2
현재 모델 : dragonkue/bge-reranker-v2-m3-ko

bongsoo/albert-small-kor-cross-encoder-v1