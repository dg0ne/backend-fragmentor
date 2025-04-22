# AutoDeploy Backend-Fragmentor - 소스 코드 분석 및 분절화 서비스

이 레포지토리는 레거시 시스템의 소스 코드를 분석하고 의미 단위로 분절화하여 벡터 데이터베이스에 저장하는 서비스입니다. 파편화된 소스 코드를 벡터화하여 효율적인 검색이 가능하도록 합니다.

## 프로젝트 개요

소스 코드를 AST(Abstract Syntax Tree) 기반으로 파편화하고, SentenceTransformer를 활용하여 임베딩을 생성한 후 Qdrant 벡터 데이터베이스에 저장합니다. 파편화된 소스 코드는 `backend-ranker` 서비스에서 사용자 요구사항에 맞는 코드 검색에 활용됩니다.

## 기능 개요

- **소스 코드 파싱**: 다양한 언어(.vue, .ts, .js, .java 등)의 소스 코드 파싱 및 분석
- **AST 기반 파편화**: 추상 구문 트리를 활용한 의미 단위 기반 소스 코드 파편화
- **정규화 및 필터링**: 들여쓰기/네이밍/중복 제거 및 불필요 코드 제거
- **벡터 임베딩 생성**: SentenceTransformer를 활용한 코드 조각 벡터화
- **벡터 DB 저장**: Qdrant에 임베딩 및 메타데이터 저장

## 기술 스택

- **Python 3.11+**
- **FastAPI**: 고성능 비동기 API 서버
- **Qdrant**: 벡터 데이터베이스 (디스크 기반 저장 지원)
- **SentenceTransformers**: 임베딩 생성 모델
- **AST 파서**: 다양한 언어 파싱을 위한 구문 트리 분석기
- **Docker**: 컨테이너화 및 배포

## 프로젝트 구조

```
backend-fragmentor/
├── app/
│   ├── api/                      # API 엔드포인트
│   │   ├── __init__.py
│   │   ├── router.py             # FastAPI 라우터
│   │   └── models.py             # API 요청/응답 모델
│   │
│   ├── core/                     # 코어 설정 및 유틸리티
│   │   ├── __init__.py
│   │   ├── config.py             # 어플리케이션 설정
│   │   ├── logging.py            # 로깅 설정
│   │   └── security.py           # 인증 및 보안
│   │
│   ├── parser/                   # 소스 코드 파싱 모듈
│   │   ├── __init__.py
│   │   ├── javascript.py         # JS/TS 파서
│   │   ├── vue.py                # Vue 파서
│   │   ├── java.py               # Java 파서
│   │   └── ast/                  # AST 처리 모듈
│   │       ├── __init__.py
│   │       ├── java_ast.py       # Java AST 처리
│   │       ├── js_ast.py         # JS/TS AST 처리
│   │       └── vue_ast.py        # Vue AST 처리
│   │
│   ├── embedding/                # 임베딩 생성 및 관리
│   │   ├── __init__.py
│   │   ├── engine.py             # 임베딩 엔진
│   │   ├── sentence_transformer.py # SentenceTransformer 어댑터
│   │   └── utils.py              # 임베딩 유틸리티
│   │
│   ├── db/                       # 데이터베이스 관리
│   │   ├── __init__.py
│   │   ├── qdrant.py             # Qdrant 클라이언트
│   │   └── models.py             # DB 모델
│   │
│   ├── fragmentation/            # 코드 파편화 모듈
│   │   ├── __init__.py
│   │   ├── fragmenter.py         # 파편화 엔진
│   │   ├── normalizer.py         # 코드 정규화 도구
│   │   └── filter.py             # 불필요 코드 필터링
│   │
│   ├── services/                 # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── analyzer.py           # 소스 코드 분석 서비스
│   │   ├── indexing.py           # 인덱싱 서비스
│   │   └── storage.py            # 저장 서비스
│   │
│   └── main.py                   # 애플리케이션 진입점
│
├── scripts/                      # 유틸리티 스크립트
│   ├── index_project.py          # 프로젝트 인덱싱
│   ├── cleanup_code.py           # 코드 정리 스크립트
│   └── test_fragmenter.py        # 파편화 테스트
│
├── data/                         # 데이터 저장소
│   ├── index/                    # 벡터 인덱스
│   ├── embeddings/               # 임베딩 캐시
│   └── fragments/                # 파편화된 코드 저장소
│
├── Dockerfile                    # Docker 설정
├── docker-compose.yml            # Docker Compose 설정
└── requirements.txt              # Python 의존성
```

## API 엔드포인트

### 소스 코드 수집 및 파편화
- `POST /api/collect`: 소스 코드 수집 및 파싱 요청
- `GET /api/status/{job_id}`: 파편화 작업 상태 확인

### 파편화 및 임베딩
- `POST /api/fragment`: 파편화 및 임베딩 생성 요청
- `GET /api/fragments/{fragment_id}`: 특정 파편 조회

### 벡터 데이터베이스 관리
- `GET /api/stats`: 벡터 DB 통계 조회
- `POST /api/reset`: 벡터 DB 초기화 (개발용)

## 파편화 프로세스

### 1. 소스 코드 수집
- 로컬 파일 시스템에서 레거시 코드 수집 (약 3GB 규모)
- 언어 및 파일 타입별 분류

### 2. AST 기반 파편화
- 각 언어별 AST(Abstract Syntax Tree) 생성
- 함수/클래스/메소드 단위로 코드 분해
- 비정형 구조까지 포함하여 의미 단위 파편화

### 3. 정규화 및 필터링
- 들여쓰기, 네이밍 규칙 정규화
- 중복 코드 제거
- 불필요한 코드 필터링

### 4. 메타데이터 추출
- 파일 경로, 언어, 종속성 관계 등 메타데이터 추출
- 코드 조각 간 관계 정보 식별

### 5. 벡터 임베딩 생성
- SentenceTransformer를 활용한 코드 조각 벡터화
- 각 코드 조각에 대한 임베딩 벡터 생성

### 6. Qdrant 저장
- 생성된 임베딩과 메타데이터를 Qdrant에 저장
- 디스크 기반 저장으로 대용량 데이터 처리 가능

## 벡터 데이터베이스 스키마

파편화된 소스 코드 조각은 다음과 같은 구조로 벡터 데이터베이스에 저장됩니다:

```json
{
  "id": "unique-fragment-id",
  "vector": [0.1, 0.2, ..., 0.768],  // 임베딩 벡터
  "payload": {
    "content": "public void processPayment(Order order) {...}",
    "language": "java",
    "file_path": "src/services/PaymentService.java",
    "start_line": 45,
    "end_line": 60,
    "type": "method",
    "parent": "PaymentService",
    "imports": ["com.example.model.Order", "com.example.exception.PaymentException"],
    "relations": ["OrderService", "PaymentGateway"]
  }
}
```

## Backend-Ranker 연계

Backend-Fragmentor 서비스는 Backend-Ranker 서비스와 다음과 같이 연계됩니다:

1. Fragmentor는 모든 소스 코드를 파편화하고 벡터화하여 Qdrant에 저장
2. Ranker는 사용자 요구사항에 따라 Qdrant에 벡터 검색 요청
3. Fragmentor는 백엔드 API를 통해 검색 결과 제공
4. 관련 파편 및 메타데이터를 구조화된 형태로 Ranker에 전달

## 설치 및 실행 방법

### 로컬 개발 환경

```bash
# 저장소 클론
git clone https://github.com/your-org/AutoDeploy-fragmentor.git
cd AutoDeploy-fragmentor

# 가상환경 설정
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 서버 실행
uvicorn app.main:app --reload
```

### Docker 환경

```bash
# Docker 이미지 빌드
docker build -t AutoDeploy-fragmentor .

# Docker 실행
docker run -p 8000:8000 --env-file .env AutoDeploy-fragmentor

# 또는 Docker Compose 사용
docker-compose up
```

## 성능 최적화

소스 코드 파편화 및 벡터화 성능 최적화를 위한 전략:

1. **병렬 처리**: 파편화 및 임베딩 생성 작업 병렬화
2. **배치 처리**: 임베딩 생성 및 DB 저장 작업 배치 처리
3. **증분 업데이트**: 변경된 소스 파일만 재파편화 및 재벡터화
4. **캐싱**: 중간 결과 캐싱으로 반복 계산 방지

## 주의사항

이 프로젝트는 MacBook M4 + NPU 환경에서 로컬 실행을 목표로 설계되었습니다:

- FastAPI 서버, SentenceTransformer 임베딩, Qdrant 실행 모두 로컬 환경에서 가능
- 대용량 데이터(10GB 이상)나 다수 사용자 처리 시 클라우드 환경 고려 필요
- 파편화는 파서 기반으로 진행해야 하며, 딥러닝 모델은 이 작업에 적합하지 않음

## 라이선스

이 프로젝트는 내부 사용 목적으로 개발되었으며, 모든 권리는 회사에 있습니다.
