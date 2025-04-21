"""
코드 파편화에 필요한 유틸리티 함수들
"""

import re
from typing import Dict, List, Any, Optional, Tuple

# 정규 표현식 패턴
WHITESPACE_PATTERN = re.compile(r'\s+')
COMMENTS_PATTERN = re.compile(r'//.*?$|/\*.*?\*/', re.MULTILINE | re.DOTALL)

def normalize_code(code: str) -> str:
    """
    코드 정규화: 주석 제거, 들여쓰기 정리
    
    Args:
        code: 정규화할 코드
        
    Returns:
        str: 정규화된 코드
    """
    # 주석 제거
    code = COMMENTS_PATTERN.sub('', code)
    # 과도한 공백 정규화
    code = WHITESPACE_PATTERN.sub(' ', code)
    # 양쪽 공백 제거
    code = code.strip()
    return code

def extract_code_block(code: str, start_pos: int) -> Optional[str]:
    """
    괄호 매칭을 통한 코드 블록 추출
    
    Args:
        code: 전체 코드
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
    return None

def extract_jsx_element(code: str, start_pos: int) -> Optional[str]:
    """
    주어진 위치에서 JSX 요소 전체 추출
    
    Args:
        code: 전체 코드
        start_pos: 시작 위치
        
    Returns:
        Optional[str]: 추출된 JSX 요소 또는 None
    """
    # 태그 이름 추출
    tag_match = re.search(r'<([A-Z][a-zA-Z0-9]*)', code[start_pos:])
    if not tag_match:
        return None
        
    tag_name = tag_match.group(1)
    open_tags = 1
    current_pos = start_pos + tag_match.end()
    
    # 닫는 태그 찾기
    while current_pos < len(code) and open_tags > 0:
        open_tag_pos = code.find(f'<{tag_name}', current_pos)
        close_tag_pos = code.find(f'</{tag_name}>', current_pos)
        
        if close_tag_pos == -1:
            # 닫는 태그를 찾지 못함
            return None
            
        if open_tag_pos != -1 and open_tag_pos < close_tag_pos:
            open_tags += 1
            current_pos = open_tag_pos + 1
        else:
            open_tags -= 1
            current_pos = close_tag_pos + len(f'</{tag_name}>') if open_tags == 0 else close_tag_pos + 1
    
    if open_tags == 0:
        return code[start_pos:current_pos]
        
    return None

def extract_effect_block(code: str, start_pos: int) -> Optional[str]:
    """
    useEffect 블록 추출
    
    Args:
        code: 전체 코드
        start_pos: 시작 위치
        
    Returns:
        Optional[str]: 추출된 useEffect 블록 또는 None
    """
    # useEffect(() => { ... }, [dependencies]) 형태 추출
    bracket_count = 0
    in_callback = False
    callback_end = None
    dependencies_start = None
    dependencies_end = None
    
    for i in range(start_pos, len(code)):
        if code[i] == '{' and not in_callback:
            bracket_count += 1
            in_callback = True
        elif code[i] == '{' and in_callback:
            bracket_count += 1
        elif code[i] == '}':
            bracket_count -= 1
            
        if in_callback and bracket_count == 0:
            callback_end = i + 1
            dependencies_start = code.find('[', callback_end)
            if dependencies_start > 0:
                dependencies_end = code.find(']', dependencies_start)
                if dependencies_end > 0:
                    return code[start_pos:dependencies_end + 1]
                else:
                    return code[start_pos:callback_end]
            else:
                return code[start_pos:callback_end]
    
    return None

def extract_effect_dependencies(effect_code: str) -> List[str]:
    """
    useEffect 의존성 배열 추출
    
    Args:
        effect_code: useEffect 코드
        
    Returns:
        List[str]: 추출된 의존성 목록
    """
    dependencies = []
    
    # 의존성 배열 찾기
    dep_match = re.search(r'\[(.*?)\]$', effect_code)
    if dep_match:
        deps_str = dep_match.group(1)
        # 쉼표로 구분된 의존성 추출
        dependencies = [d.strip() for d in deps_str.split(',') if d.strip()]
        
    return dependencies

def detect_component_type(code: str) -> str:
    """
    컴포넌트 타입 감지 (함수형/클래스/메모/훅)
    
    Args:
        code: 컴포넌트 코드
        
    Returns:
        str: 감지된 컴포넌트 타입
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