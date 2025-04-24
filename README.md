# Vue Todo 파편화 및 벡터화 도구

이 프로젝트는 Vue Todo 애플리케이션의 소스 코드를 의미 단위로 파편화하고 벡터화하여 효율적인 검색이 가능하도록 구현한 것입니다.

## 개요

이 도구는 다음과 같은 기능을 제공합니다:

- **코드 파싱**: Vue 프로젝트의 SFC(Single File Component) 파일을 파싱하여 분석
- **의미 단위 파편화**: 컴포넌트, 템플릿, 스크립트, 스타일 섹션을 의미 단위로 분절
- **벡터 임베딩 생성**: 각 코드 파편에 대한 임베딩 벡터 생성
- **벡터 저장소**: Faiss를 활용한 벡터 저장 및 효율적인 유사도 검색
- **Cross-Encoder 재랭킹**: 검색 결과의 정확도를 높이기 위한 2단계 재랭킹 적용
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

## 사용중인 AI모델

### Bi-Encoder 모델
- **모델명**: `jhgan/ko-sroberta-multitask`
- **용도**: 초기 벡터 검색에 사용되는 임베딩 생성

### Cross-Encoder 모델
- **기본 모델**: `dragonkue/bge-reranker-v2-m3-ko`
- **파인튜닝된 모델**: `./trained_cross_encoder`
- **용도**: 검색 결과 재랭킹을 통한 정확도 향상

## 실행 방법

### 1. 코드 파편화 및 벡터화

```bash
# 가상환경 활성화 후
# Vue Todo 프로젝트 파편화
python vuetodo-fragmentor.py --project ../todo-web

# 데이터 디렉토리 지정 (기본값: ./data)
python vuetodo-fragmentor.py --project ../todo-web --data-dir {your-data-dir}
```

### 2. 코드 검색

```bash
# 가상환경 활성화 후
# 대화형 검색 인터페이스 실행
python search_ui.py

# 데이터 디렉토리 지정
python search_ui.py --data-dir ./custom-data-dir
```

### 3. Cross-Encoder 모델 파인튜닝 (필요시)

파인튜닝된 모델은 이미 `./trained_cross_encoder` 디렉토리에 저장되어 있으므로, 별도의 파인튜닝 없이 바로 사용 가능합니다. 추가 파인튜닝이 필요한 경우에만 아래 명령어를 실행하세요:

```bash
# Cross-Encoder 모델 파인튜닝
python train_cross_encoder.py --examples cross_encoding.json --output-dir ./trained_cross_encoder --test
```

### 4. 추가 파인튜닝(필요시)


```bash
# Cross-Encoder 모델 파인튜닝
python train_cross_encoder.py --examples cross_encoding.json --output-dir ./trained_cross_encoder --test

# 커스텀 설정 실행
python continue_training.py --examples my_custom_data.json --checkpoint 282 --epochs 2
```


## 검색 쿼리 예시

대화형 검색 모드에서 사용할 수 있는 예시 명령어:

```
코드검색> search 할일 목록 컴포넌트
코드검색> search 템플릿 섹션 --type=template
코드검색> search 로그인 처리 --rerank (Cross-Encoder 재랭킹 적용)
코드검색> view 2
코드검색> similar
코드검색> similar --rerank
코드검색> file src/components/TodoItem.vue
코드검색> stats
```

## 프로젝트 구조

```
vue-todo-fragmentor/
├── vuetodo-fragmentor.py     # 파편화 및 벡터화 실행 스크립트
├── search_ui.py              # 검색 UI
├── train_cross_encoder.py    # Cross-Encoder 모델 파인튜닝 스크립트
├── cross_encoding.json       # 파인튜닝용 예제 데이터
├── trained_cross_encoder/    # 파인튜닝된 Cross-Encoder 모델
├── requirements.txt          # 의존성 패키지
├── README.md                 # 프로젝트 설명
└── app/                      # 핵심 모듈
    ├── parser/               # Vue 파서
    │   └── vue_parser.py     # Vue SFC 파서
    ├── fragmenter/           # 파편화 모듈
    │   └── fragmenter.py     # 파편화 엔진
    ├── embedding/            # 임베딩 모듈
    │   ├── embedder.py       # 임베딩 생성기
    │   └── cross_encoder.py  # Cross-Encoder 재랭킹 모듈
    └── storage/              # 벡터 저장소
        └── faiss_store.py    # Faiss 벡터 저장소
```

## 파편화 및 검색 프로세스

### 파편화 프로세스

1. **코드 파싱**: Vue SFC 파일을 파싱하여 템플릿, 스크립트, 스타일 섹션 분리
2. **파편화**: 각 파일을 컴포넌트, 템플릿, 스크립트, 스타일 단위로 파편화
3. **임베딩 생성**: SentenceTransformer 모델을 사용하여 각 파편의 임베딩 벡터 생성
4. **벡터 저장**: 생성된 임베딩을 Faiss 인덱스에 저장하고 메타데이터 관리

### 검색 프로세스

1. **벡터 검색**: 사용자 쿼리를 임베딩하여 Faiss 인덱스에서 유사한 코드 파편 검색
2. **앙상블 검색**: 벡터 검색과 키워드 검색을 결합하여 초기 검색 품질 향상
3. **Cross-Encoder 재랭킹**: 파인튜닝된 Cross-Encoder 모델을 사용하여 검색 결과 재랭킹
4. **결과 반환**: 관련성 높은 코드 파편을 사용자에게 제공

## Cross-Encoder 재랭킹

이 프로젝트는 2단계 검색 파이프라인을 구현하여 검색 정확도를 향상시켰습니다:

1. **Bi-Encoder 앙상블 검색**: 빠른 1차 후보 선별 (Faiss)
2. **Cross-Encoder 재랭킹**: 사용자 질문과 코드 파편 간의 직접적인 관계 평가로 정밀한 순위 결정

Cross-Encoder 모델은 `dragonkue/bge-reranker-v2-m3-ko`를 기반으로 `cross_encoding.json`의 예제 데이터를 사용하여 파인튜닝되었으며, 파인튜닝된 모델은 `./trained_cross_encoder` 디렉토리에 저장되어 있습니다.

## 주의사항

- 현재 구현은 Vue SFC 파일에 대한 기본적인 파편화만 지원합니다.
- 향후 더 세부적인 파편화(메서드, 함수 단위 등)로 확장할 예정입니다.
- Cross-Encoder 재랭킹은 정확도를 높이지만 약간의 추가 지연을 발생시킬 수 있습니다.