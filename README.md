# Vue Todo 파편화 및 벡터화 도구

이 프로젝트는 Vue Todo 애플리케이션의 소스 코드를 의미 단위로 파편화하고 벡터화하여 효율적인 검색이 가능하도록 구현한 것입니다.

## 개요

이 도구는 다음과 같은 기능을 제공합니다:

- **코드 파싱**: Vue 프로젝트의 SFC(Single File Component) 파일을 파싱하여 분석
- **의미 단위 파편화**: 컴포넌트, 템플릿, 스크립트, 스타일 섹션을 의미 단위로 분절
- **벡터 임베딩 생성**: 각 코드 파편에 대한 임베딩 벡터 생성
- **벡터 저장소**: Faiss를 활용한 벡터 저장 및 효율적인 유사도 검색
- **대화형 검색 인터페이스**: 코드 파편을 검색하고 탐색할 수 있는 CLI 도구

## 설치 및 실행

### 요구 사항

- Python 3.11.9
- 필요한 패키지는 requirements.txt 참고

### 설치

```bash
# 저장소 클론
git clone https://github.com/your-org/vue-todo-fragmentor.git
cd vue-todo-fragmentor

# 가상환경 설정
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

## 사용중인 모델
snunlp/KR-SBERT-V40K-klueNLI-augSTS

추가 개선 예정
1. BAAI/bge-m3
검색 성능 특화: 8K 토큰 길이 지원과 다중 언어 기능을 갖춘 검색 최적화 모델

코드-질문 매칭 강점: 코드 구조와 사용자 질문 간의 의미적 관계 파악에 우수

2. jhgan/ko-sroberta-multitask  <<< 가장 vue에 최적화(500줄 미만의 코드에서 제일 월등한 성능보장)
한국어 최적화: KorSTS 벤치마크에서 85.6 스피어만 상관계수 기록

멀티태스크 학습: 코드 문맥 이해와 자연어 질문 매칭에 효과적

### 실행 방법

#### 1. 코드 파편화 및 벡터화

```bash
# 가상환경 활성화 후
# Vue Todo 프로젝트 파편화
python vuetodo-fragmentor.py --project ../todo-web

# 데이터 디렉토리 지정 (기본값: ./data)
python vuetodo-fragmentor.py --project ../todo-web --data-dir {your-data-dir}
```

#### 2. 코드 검색

```bash
# 가상환경 활성화 후
# 대화형 검색 인터페이스 실행
python search_ui.py

# 데이터 디렉토리 지정
python search_ui.py --data-dir ./custom-data-dir
```

## 검색 쿼리 예시

대화형 검색 모드에서 사용할 수 있는 예시 명령어:

```
코드검색> search 할일 목록 컴포넌트
코드검색> search 템플릿 섹션 --type=template
코드검색> view 2
코드검색> similar
코드검색> file src/components/TodoItem.vue
코드검색> stats
```

## 프로젝트 구조

```
vue-todo-fragmentor/
├── vuetodo-fragmentor.py     # 파편화 및 벡터화 실행 스크립트
├── search_ui.py              # 검색 UI
├── requirements.txt          # 의존성 패키지
├── README.md                 # 프로젝트 설명
└── app/                      # 핵심 모듈
    ├── parser/               # Vue 파서
    │   └── vue_parser.py     # Vue SFC 파서
    ├── fragmenter/           # 파편화 모듈
    │   └── fragmenter.py     # 파편화 엔진
    ├── embedding/            # 임베딩 모듈
    │   └── embedder.py       # 임베딩 생성기
    └── storage/              # 벡터 저장소
        └── faiss_store.py    # Faiss 벡터 저장소
```

## 파편화 프로세스

1. **코드 파싱**: Vue SFC 파일을 파싱하여 템플릿, 스크립트, 스타일 섹션 분리
2. **파편화**: 각 파일을 컴포넌트, 템플릿, 스크립트, 스타일 단위로 파편화
3. **임베딩 생성**: SentenceTransformer 모델을 사용하여 각 파편의 임베딩 벡터 생성
4. **벡터 저장**: 생성된 임베딩을 Faiss 인덱스에 저장하고 메타데이터 관리

## 주의사항

- 현재 구현은 Vue SFC 파일에 대한 기본적인 파편화만 지원합니다.
- 향후 더 세부적인 파편화(메서드, 함수 단위 등)로 확장할 예정입니다.