"""
JSX 파싱에 필요한 유틸리티 함수
"""

import os
import re
from typing import Dict, List, Any, Optional, Tuple

# 정규 표현식 패턴
COMPONENT_PATTERNS = [
    # 함수형 컴포넌트
    re.compile(r'function\s+([A-Z][a-zA-Z0-9]*)\s*\('),
    # 클래스 컴포넌트
    re.compile(r'class\s+([A-Z][a-zA-Z0-9]*)\s+extends\s+React\.Component'),
    # 화살표 함수 컴포넌트
    re.compile(r'const\s+([A-Z][a-zA-Z0-9]*)\s*=\s*\(.*\)\s*=>\s*{'),
    # 화살표 함수 간단 표현
    re.compile(r'const\s+([A-Z][a-zA-Z0-9]*)\s*=\s*\(.*\)\s*=>\s*\('),
    # memo 래핑된 컴포넌트
    re.compile(r'const\s+([A-Z][a-zA-Z0-9]*)\s*=\s*React\.memo\('),
]

# 훅 패턴
HOOK_PATTERN = re.compile(r'(use[A-Z][a-zA-Z0-9]*)')

# JSX 요소 패턴
JSX_ELEMENT_PATTERN = re.compile(r'<([A-Z][a-zA-Z0-9]*)[\s\w=>"/\'\.:\-\(\)]*>[\s\S]*?</\1>', re.DOTALL)

# MUI 컴포넌트 감지 패턴
MUI_IMPORT_PATTERN = re.compile(r'import\s+\{(.*?)\}\s+from\s+[\'"]@mui/material[\'"](.*?);')

# 주석 패턴
COMMENTS_PATTERN = re.compile(r'//.*?$|/\*.*?\*/', re.MULTILINE | re.DOTALL)

def extract_code_block(code: str, start_pos: int) -> Optional[str]:
    """
    괄호 매칭을 통한 코드 블록 추출
    
    Args:
        code: 소스 코드
        start_pos: 시작 위치
        
    Returns:
        Optional[str]: 추출된 코드 블록 또는 None
    """
    # { 기호 위치 찾기
    bracket_pos = code.find('{', start_pos)
    if bracket_pos == -1:
        return None
        
    # 괄호 매칭
    bracket_count = 1
    end_pos = bracket_pos + 1
    
    while bracket_count > 0 and end_pos < len(code):
        if code[end_pos] == '{':
            bracket_count += 1
        elif code[end_pos] == '}':
            bracket_count -= 1
        end_pos += 1
        
    if bracket_count == 0:
        return code[start_pos:end_pos]
        
    # 괄호를 찾지 못했거나 잘못된 경우, 화살표 함수 간단 표현식 체크
    if '=> (' in code[start_pos:start_pos+100]:
        paren_count = 0
        found_opening_paren = False
        
        for i in range(start_pos, len(code)):
            if code[i] == '(' and not found_opening_paren:
                # 화살표 다음의 첫 여는 괄호
                if '=> ' in code[start_pos:i]:
                    paren_count += 1
                    found_opening_paren = True
            elif code[i] == '(' and found_opening_paren:
                paren_count += 1
            elif code[i] == ')':
                paren_count -= 1
                
            if found_opening_paren and paren_count == 0:
                end_pos = i + 1
                return code[start_pos:end_pos]
    
    # 여전히 찾지 못한 경우 적당한 길이 반환
    return code[start_pos:min(start_pos + 500, len(code))]

def detect_component_type(code: str) -> str:
    """
    컴포넌트 타입 감지 (함수형/클래스/메모/훅)
    
    Args:
        code: 컴포넌트 코드
        
    Returns:
        str: 컴포넌트 타입
    """
    if code.startswith('function'):
        return 'functional'
    elif code.startswith('class'):
        return 'class'
    elif 'React.memo' in code or 'memo(' in code:
        return 'memo'
    elif code.startswith('const') and 'use' in code[:20]:
        return 'hook'
    elif code.startswith('const') and '=>' in code[:50]:
        return 'arrow_function'
    else:
        return 'unknown'

def extract_component_purpose(name: str, code: str) -> Optional[str]:
    """
    컴포넌트 이름과 코드로부터 목적 추론
    
    Args:
        name: 컴포넌트 이름
        code: 컴포넌트 코드
        
    Returns:
        Optional[str]: 추론된 목적
    """
    # 이름 기반 추론
    if 'Auth' in name or 'Login' in name:
        return '인증'
    elif 'Subscription' in name:
        return '구독'
    elif 'List' in name or 'Item' in name:
        return '목록'
    elif 'Detail' in name:
        return '상세'
    elif 'Form' in name:
        return '양식'
    
    # 코드 내용 기반 추론
    if ('login' in code.lower() or 'auth' in code.lower()) and ('form' in code.lower() or 'input' in code.lower()):
        return '인증'
    elif 'subscription' in code.lower() or '구독' in code.lower():
        return '구독'
    elif ('list' in code.lower() or 'item' in code.lower()) and ('map(' in code.lower() or '.map(' in code.lower()):
        return '목록'
    elif 'detail' in code.lower() or '상세' in code.lower():
        return '상세'
    elif 'form' in code.lower() or 'input' in code.lower() or 'submit' in code.lower():
        return '양식'
    
    return '기타'

def extract_lifesub_metadata(file_path: str, code: str) -> Dict[str, Any]:
    """
    lifesub-web 프로젝트 특화 메타데이터 추출
    
    Args:
        file_path: 파일 경로
        code: 파일 내용
        
    Returns:
        Dict: 추가 메타데이터
    """
    metadata = {}
    
    # 파일 경로에서 카테고리 추출
    path_parts = file_path.split(os.path.sep)
    if 'src' in path_parts:
        src_idx = path_parts.index('src')
        if len(path_parts) > src_idx + 1:
            category = path_parts[src_idx + 1]
            metadata['category'] = category
    
    # 컴포넌트 설명 주석 추출
    description_match = re.search(r'/\*\s*(.*?)\s*\*/', code, re.DOTALL)
    if description_match:
        metadata['description'] = description_match.group(1).strip()
    
    # 코드 내 주요 기능 라벨 추출
    features = []
    if 'auth' in code.lower() or 'login' in code.lower():
        features.append('인증')
    if 'subscription' in code.lower() or '구독' in code.lower():
        features.append('구독')
    if 'recommend' in code.lower() or '추천' in code.lower():
        features.append('추천')
    
    if features:
        metadata['features'] = features
    
    return metadata

def strip_comments(code: str) -> str:
    """
    코드에서 주석 제거
    
    Args:
        code: 소스 코드
        
    Returns:
        str: 주석이 제거된 코드
    """
    return COMMENTS_PATTERN.sub('', code)

def get_ignore_patterns() -> List[str]:
    """무시할 디렉토리 패턴 목록 반환"""
    return [
        r'\.git',
        r'node_modules',
        r'\.idea',
        r'build',
        r'public',
        r'\.env'
    ]

def should_ignore_file(file_path: str, ignore_patterns: Optional[List[str]] = None) -> bool:
    """
    무시해야 할 파일 경로인지 확인
    
    Args:
        file_path: 확인할 파일 경로
        ignore_patterns: 무시할 패턴 목록
            
    Returns:
        bool: 무시해야 하면 True, 그렇지 않으면 False
    """
    if ignore_patterns is None:
        ignore_patterns = get_ignore_patterns()
        
    for pattern in ignore_patterns:
        if re.search(pattern, file_path):
            return True
    return False

def get_file_content(file_path: str) -> str:
    """
    파일 내용 읽기 (인코딩 처리 포함)
    
    Args:
        file_path: 파일 경로
        
    Returns:
        str: 파일 내용
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # 인코딩 문제 발생 시 latin-1로 시도
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()