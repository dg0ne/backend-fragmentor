# React-Fragmentor-POC

React 소스 코드를 의미 단위로 파편화하고 벡터 임베딩을 생성하여 Faiss 벡터 저장소에 저장하는, 간단한 POC(Proof of Concept) 프로젝트입니다.

## 개요

이 프로젝트는 React로 작성된 코드를 효과적으로 검색하고 재사용하기 위한 POC로, 다음과 같은 기능을 제공합니다:

- **React/JSX 코드 파싱**: 프로젝트의 React 컴포넌트 파일을 파싱
- **의미 단위 파편화**: 함수, 컴포넌트, JSX 요소 등을 의미 단위로 분절
- **임베딩 생성**: SentenceTransformer를 이용한 코드 조각 벡터화
- **벡터 저장 및 검색**: Faiss를 이용한 효율적인 벡터 저장 및 유사 코드 검색

## 설치 방법

### 요구 사항

- Python 3.9 이상
- 최소 4GB 이상의 RAM (SentenceTransformer 모델 로드용)

### 설치

```bash
# 저장소 클론
git clone https://github.com/your-username/react-fragmentor-poc.git
cd react-fragmentor-poc

# 가상 환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

## 사용 방법

### 기본 사용법

```bash
# React 프로젝트 파편화 및 벡터화
python src/main.py --project /path/to/react-project

# 데이터 저장 디렉토리 지정 (기본값: ./data)
python src/main.py --project /path/to/react-project --data-dir /path/to/save/data
```

### 코드 검색

```bash
# 단일 쿼리로 검색
python src/main.py --project /path/to/react-project --query "axios 요청 처리 함수"

# 대화형 검색 모드
python src/main.py --project /path/to/react-project --search
```

## 프로젝트 구조

```
react-fragmentor-poc/
├── src/
│   ├── parser/                   # 코드 파서
│   │   └── jsx_parser.py         # React JSX 파서
│   │
│   ├── fragmenter/               # 파편화 로직  
│   │   └── fragmenter.py         # 코드 파편화 엔진
│   │
│   ├── embedding/                # 임베딩 생성
│   │   └── embedder.py           # SentenceTransformer 활용
│   │
│   ├── storage/                  # 벡터 저장소
│   │   └── faiss_store.py        # Faiss 벡터 DB
│   │
│   └── main.py                   # 메인 스크립트
│
├── data/                         # 데이터 저장소 (자동 생성)
│   ├── faiss/                    # Faiss 인덱스
│   ├── metadata/                 # 메타데이터
│   └── embeddings/               # 임베딩 캐시
│
├── requirements.txt              # 의존성 패키지
└── README.md                     # 본 문서
```

## 파편화 프로세스

이 프로젝트의

1. **파싱**: React/JSX 파일 파싱 및 컴포넌