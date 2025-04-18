# lifesub-web 소스 코드 분석 및 파편화 POC

이 프로젝트는 lifesub-web React 애플리케이션의 소스 코드를 의미 단위로 파편화하고, 벡터화하여 효율적인 검색이 가능하도록 만든 POC(Proof of Concept)입니다.

## 개요

이 POC는 다음과 같은 기능을 제공합니다:

- **코드 파싱**: lifesub-web 프로젝트의 React 소스 코드를 파싱하여 AST(Abstract Syntax Tree) 분석
- **의미 단위 파편화**: 컴포넌트, 함수, JSX 요소, API 호출 등을 의미 단위로 분절
- **벡터 임베딩 생성**: 각 코드 파편에 대한 임베딩 벡터 생성
- **벡터 저장소**: Faiss를 활용한 벡터 저장 및 효율적인 유사도 검색
- **대화형 검색 인터페이스**: 코드 파편을 검색하고 탐색할 수 있는 CLI 도구

## 파편화 프로세스 다이어그램

아래는 lifesub-web 프로젝트의 소스 코드 파편화 및 벡터화 과정을 보여주는 다이어그램입니다:

![lifesub-web 파편화 프로세스](fragmentor_process.mmd)

## 설치 및 실행

### 요구 사항

- Python 3.9 이상
- 필요한 패키지:
  - esprima
  - sentence-transformers
  - faiss-cpu
  - colorama
  - tqdm

### 설치

```bash
# 저장소 클론
git clone https://github.com/your-username/lifesub-web-fragmentor.git
cd lifesub-web-fragmentor

# 의존성 설치
pip install -r requirements.txt
```

### 실행 방법

#### 1. 코드 파편화 및 벡터화

```bash
# lifesub-web 프로젝트 파편화
python lifesub_fragmentor.py --project /path/to/lifesub-web

# 데이터 디렉토리 지정 (기본값: ./data)
python lifesub_fragmentor.py --project /path/to/lifesub-web --data-dir ./custom-data-dir
```

#### 2. 코드 검색

```bash
# 대화형 검색 인터페이스 실행
python search_ui.py

# 데이터 디렉토리 지정
python search_ui.py --data-dir ./custom-data-dir
```

## 검색 쿼리 예시

```bash
# 특정 쿼리로 직접 검색
python lifesub_fragmentor.py --project /path/to/lifesub-web --query "구독 서비스 목록 컴포넌트"

# 대화형 검색 모드
python lifesub_fragmentor.py --project /path/to/lifesub-web --search

# 필터링을 적용한 검색 (대화형 UI 내에서)
코드검색> search 구독 컴포넌트 --type=component
코드검색> search API 호출 --type=api_call
```

## 검색 UI 스크린샷

대화형 코드 검색 인터페이스:

![검색 UI 예시](search_ui_example.svg)

## 사용 예시

다음은 실제 실행 과정과 사용 예시입니다:

```bash
# 1. 파편화 및 벡터화 실행
$ python lifesub_fragmentor.py --project ./lifesub-web --data-dir ./data

================================================
 lifesub-web 프로젝트 파편화 및 벡터화 시작: ./lifesub-web
================================================

[1/4] 프로젝트 파싱 중...
lifesub-web 프로젝트 파싱 중: ./lifesub-web
처리 중... 10개 파일 완료
처리 중... 20개 파일 완료
처리 중... 30개 파일 완료
  - 파싱된 파일: 31개
  - 감지된 컴포넌트: 24개
  - 파일 확장자 분포: {'.js': 28, '.html': 1, '.json': 2}

[2/4] 코드 파편화 중...
  - 생성된 파편: 112개
  - 파편 타입 분포: {'component': 24, 'function': 43, 'jsx_element': 21, 'import_block': 14, 'api_call': 8, 'routing': 2}
  - 컴포넌트 타입 분포: {'functional': 22, 'arrow_function': 2}

[3/4] 임베딩 생성 중...
  - 모델: all-MiniLM-L6-v2
  - 벡터 차원: 384
100%|██████████| 4/4 [00:02<00:00,  1.47it/s]
  - 생성된 임베딩: 112개

[4/4] 벡터 저장소에 저장 중...
112개 벡터 추가 완료 (현재 총 112개)

================================================
 처리 완료 (소요 시간: 12.34초)
================================================
  - 저장된 벡터: 112개
  - 벡터 차원: 384
  - 인덱스 타입: Cosine
  - 파편 타입 분포: {'component': 24, 'function': 43, 'jsx_element': 21, 'import_block': 14, 'api_call': 8, 'routing': 2}
  - 처리된 파일 수: 31

# 2. 대화형 검색 UI 실행
$ python search_ui.py --data-dir ./data

# (이하 검색 UI 예시 생략)
```

## 실행 스크립트

프로젝트에는 편리한 실행을 위한 Bash 스크립트도 포함되어 있습니다:

```bash
# 스크립트 실행 권한 부여
chmod +x run.sh

# 스크립트 실행
./run.sh
```

## 파편화 프로세스 상세

### 1. 코드 파싱
- JSX/JS 파일을 파싱하여 AST 생성
- 컴포넌트, 훅, 함수 등의 의미 단위 식별
- 파일 메타데이터 수집
- lifesub-web 특화 정보(카테고리, 목적) 추출

### 2. 코드 파편화
- 다양한 단위로 코드 파편화:
  - 컴포넌트 (함수형, 클래스, 메모)
  - 커스텀 훅
  - 내부 함수
  - JSX 요소
  - API 호출
  - MUI 컴포넌트
  - 라우팅 관련 코드
  - Import 블록
  - 상태 관리 로직

### 3. 임베딩 생성
- SentenceTransformer 모델을 사용하여 코드 파편의 벡터 임베딩 생성
- 코드 내용과 함께 메타데이터 컨텍스트를 포함한 임베딩
- lifesub-web 특화 키워드 및 개념 포함
- 배치 처리 및 캐싱을 통한 성능 최적화

### 4. 벡터 저장
- Faiss를 이용한 벡터 인덱싱
- 코사인 유사도를 통한 검색
- 메타데이터와 매핑 정보 저장
- 필터링 기능 지원

### 5. 검색 인터페이스
- 대화형 CLI 검색 도구
- 컬러 하이라이팅된 결과 출력
- 파편 상세 보기 및 유사 파편 탐색
- 파일별, 타입별 필터링 옵션

## 프로젝트 구조

```
.
├── lifesub_fragmentor.py     # 메인 실행 스크립트
├── search_ui.py              # 검색 UI
├── requirements.txt          # 의존성 패키지
├── README.md                 # 본 문서
├── run.sh                    # 실행 스크립트
├── docs/
│   └── images/               # 문서 이미지
│       ├── fragmentor_process.svg
│       └── search_ui_example.svg
└── src/
    ├── parser/               # 코드 파서
    │   └── jsx_parser_enhanced.py  # 향상된 JSX 파서
    ├── fragmenter/           # 파편화 모듈
    │   └── fragmenter_enhanced.py  # 향상된 파편화 엔진
    ├── embedding/            # 임베딩 모듈
    │   └── embedder_enhanced.py    # 향상된 임베딩 생성기
    └── storage/              # 벡터 저장소
        └── faiss_store_enhanced.py  # 향상된 Faiss 벡터 저장소
```

## 확장 및 개선 방향

### 향후 개발 방향
1. **구문 분석 강화** - 더 정확한 AST 분석과 의미 단위 추출
2. **다중 언어 지원** - Java, Python, TypeScript 등 추가 언어 지원
3. **웹 인터페이스** - 웹 기반 코드 검색 및 탐색 UI 개발
4. **Fine-Tuned 임베딩** - 코드 특화 임베딩 모델 훈련
5. **코드 생성 통합** - LLM과 연동한 코드 생성 및 수정 기능

### 파편화 성능 개선
- 임베딩 생성 병렬 처리 최적화
- 증분 업데이트 지원 (변경된 파일만 재처리)
- 언어별 특화 파서 통합

### 검색 기능 확장
- 자연어 코드 변환 검색
- 유사 코드 클러스터링
- 시각적 코드 관계 탐색
- 복잡한 쿼리 구문 지원

## 기여 방법

이 프로젝트에 기여하고 싶으시다면:
1. 이슈 제출 또는 기능 요청
2. Pull Request 제출
3. 문서 개선 제안

## 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 LICENSE 파일을 참조하세요.