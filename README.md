# Backend-Fragmentor - lifesub-web 소스 코드 분석 및 파편화 

이 프로젝트는 React 기반의 lifesub-web 애플리케이션 소스 코드를 의미 단위로 파편화하고 벡터화하여 효율적인 검색이 가능하도록 구현한 시스템입니다.

## 개요

Backend-Fragmentor는 다음과 같은 핵심 기능을 제공합니다:

- **코드 파싱**: React 소스 코드를 효율적으로 파싱하여 AST(Abstract Syntax Tree) 분석
- **의미 단위 파편화**: 컴포넌트, 함수, JSX 요소, API 호출 등을 의미 단위로 분절
- **컨텍스트 인식 임베딩**: 코드 파편에 컨텍스트 정보를 추가하여 더 의미 있는 벡터 생성
- **벡터 저장 및 검색**: 효율적인 벡터 저장 및 유사도 기반 검색 
- **대화형 검색 인터페이스**: 코드 파편을 검색하고 탐색할 수 있는 CLI 도구

## 아키텍처

### 모듈 구조

Backend-Fragmentor는 다음과 같은 주요 모듈로 구성되어 있습니다:

```
app/
├── parser/                    # 코드 파싱 모듈
│   ├── base.py                # 기본 인터페이스 및 추상 클래스
│   ├── jsx_parser.py          # JSX 파서 구현
│   ├── utils.py               # 파싱 유틸리티
│   ├── processors/            # 각종 코드 프로세서
│   │   ├── component_processor.py  # 컴포넌트 처리
│   │   ├── hook_processor.py  # 훅 처리
│   │   ├── jsx_processor.py   # JSX 요소 처리
│   │   ├── import_processor.py # import 문 처리
│   │   └── metadata_processor.py # 메타데이터 처리
│   └── models/                # 파싱 결과 모델
│       ├── parsed_component.py # 컴포넌트 모델
│       ├── parsed_file.py     # 파일 모델
│       └── parsed_project.py  # 프로젝트 모델
│
├── fragmentation/             # 코드 파편화 모듈
│   ├── base.py                # 기본 인터페이스 및 추상 클래스
│   ├── fragmenter.py          # 메인 파편화 로직
│   ├── utils.py               # 파편화 유틸리티
│   ├── extractors/            # 파편 추출기
│   │   ├── component_extractor.py  # 컴포넌트 추출
│   │   ├── function_extractor.py # 함수 추출
│   │   ├── jsx_extractor.py   # JSX 요소 추출
│   │   ├── api_call_extractor.py # API 호출 추출
│   │   └── ...                # 기타 추출기들
│   └── models/                # 파편 모델
│       └── fragment.py        # 코드 파편 모델
│
├── embedding/                 # 임베딩 생성 모듈
│   ├── base.py                # 기본 인터페이스 및 추상 클래스
│   ├── embedder.py            # 메인 임베딩 생성 로직
│   ├── context_enhancer.py    # 컨텍스트 향상 로직
│   ├── cache_manager.py       # 임베딩 캐싱 관리
│   └── models/                # 임베딩 모델
│       ├── embedding_model.py # 임베딩 모델 추상화
│       ├── codebert_model.py  # CodeBERT 모델 구현
│       └── keyword_context.py # 키워드 컨텍스트 모델
│
├── storage/                   # 벡터 저장소 모듈 (향후 개선 예정)
│   └── faiss_store.py         # Faiss 벡터 저장소
│
├── services/                  # 서비스 로직
│   ├── analyzer.py            # 소스코드 분석
│   ├── indexing.py            # 인덱싱 서비스
│   └── search.py              # 검색 서비스
│
├── core/                      # 핵심 유틸리티
│   ├── config.py              # 설정 관리
│   └── logging.py             # 로깅 설정
│
└── main.py                    # 애플리케이션 엔트리포인트
```

### 데이터 흐름

1. **파싱 (Parser)**: 소스 코드를 구조화된 객체로 변환
2. **파편화 (Fragmentation)**: 파싱된 코드를 의미 있는 단위로 분리
3. **임베딩 (Embedding)**: 파편에 컨텍스트를 추가하고 벡터로 변환 
4. **저장 (Storage)**: 생성된 벡터와 메타데이터를 벡터 데이터베이스에 저장
5. **검색 (Search)**: 쿼리 벡터와 유사한 코드 파편 검색 및 결과 반환

### 주요 설계 원칙

- **단일 책임 원칙 (SRP)**: 각 클래스와 모듈은 하나의 책임만 가짐
- **인터페이스 분리 (ISP)**: 추상 인터페이스를 통한 느슨한 결합
- **의존성 역전 (DIP)**: 상위 모듈이 하위 모듈에 의존하지 않고 추상화에 의존
- **전략 패턴**: 다양한 프로세서와 추출기를 교체 가능한 구조
- **팩토리 패턴**: 객체 생성 로직의 캡슐화

## 설치 및 실행

### 요구 사항

- Python 3.9 이상
- 필요한 패키지:
  - esprima==4.0.1
  - sentence-transformers==2.2.2
  - faiss-cpu==1.7.4
  - torch==2.0.1
  - colorama
  - tqdm==4.65.0

### 설치

```bash
# 저장소 클론
git clone https://github.com/your-org/backend-fragmentor.git
cd backend-fragmentor

# 가상환경 설정
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 실행 방법

#### 코드 파편화 및 벡터화

```bash
# lifesub-web 프로젝트 파편화
python lifesubweb-fragmentor.py --project ../lifesub-web

# 커스텀 데이터 디렉토리 지정
python lifesubweb-fragmentor.py --project ../lifesub-web --data-dir ./custom-data-dir
```

#### 코드 검색

```bash
# 대화형 검색 인터페이스 실행
python search_ui.py

# 데이터 디렉토리 지정
python search_ui.py --data-dir ./custom-data-dir
```

## 향후 개선 계획

1. **Storage 모듈 리팩토링**:
   - `faiss_store.py`를 여러 작은 모듈로 분리
   - 다양한 벡터 저장소 지원을 위한 인터페이스 설계
   - 캐싱 및 인덱싱 전략 개선

2. **웹 인터페이스 개발**:
   - 코드 파편 검색 및 탐색을 위한 웹 UI
   - 검색 결과 시각화 개선

3. **다국어 지원 확장**:
   - 현재 JavaScript/JSX 중심에서 Python, Java 등으로 확장
   - 언어별 파서 플러그인 구조 구현

4. **성능 최적화**:
   - 병렬 처리를 통한 파싱 및 임베딩 속도 개선
   - 증분 업데이트 지원 (변경된 파일만 재처리)

5. **고급 검색 기능**:
   - 자연어 코드 변환 검색
   - 코드 관계 시각화
   - 유사 코드 클러스터링

## 배운 점 및 기술적 도전

### 아키텍처 개선

초기에는 단순한 모듈 구조였으나, 코드베이스가 성장함에 따라 다음과 같은 방향으로 아키텍처를 개선했습니다:

1. **모듈화**: 큰 클래스들을 더 작고 특화된 컴포넌트로 분리
2. **인터페이스 도입**: 구현체 교체가 용이한 추상 인터페이스 적용
3. **책임 분리**: 각 모듈과 클래스가 명확한 하나의 책임만 갖도록 재설계

이런 개선을 통해 코드 중복을 줄이고, 테스트 용이성을 높이며, 새로운 기능 추가가 쉬워졌습니다.

## 라이선스

이 프로젝트는 내부 사용 목적으로 개발되었습니다.