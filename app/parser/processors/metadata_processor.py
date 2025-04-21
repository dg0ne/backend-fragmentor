"""
파일 및 컴포넌트 메타데이터 처리 모듈
"""

import os
import re
from typing import Dict, List, Any, Optional

from app.parser.base import MetadataExtractor
from app.parser.utils import extract_lifesub_metadata, extract_component_purpose

class LifesubMetadataExtractor(MetadataExtractor):
    """
    lifesub-web 프로젝트 특화 메타데이터 추출기
    """
    
    def __init__(self):
        # 주석 패턴
        self.description_pattern = re.compile(r'/\*\s*(.*?)\s*\*/', re.DOTALL)
        
        # 기능 패턴
        self.feature_patterns = {
            '인증': [r'auth', r'login', r'사용자', r'계정'],
            '구독': [r'subscription', r'구독', r'payment', r'결제'],
            '추천': [r'recommend', r'추천', r'suggestion']
        }
    
    def extract_file_metadata(self, file_path: str, code: str) -> Dict[str, Any]:
        """
        파일 메타데이터 추출
        
        Args:
            file_path: 파일 경로
            code: 파일 내용
            
        Returns:
            Dict[str, Any]: 추출된 메타데이터
        """
        # 기본 파일 메타데이터
        metadata = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'extension': os.path.splitext(file_path)[1],
            'size': os.path.getsize(file_path),
        }
        
        # lifesub 특화 메타데이터 추출
        lifesub_metadata = extract_lifesub_metadata(file_path, code)
        metadata.update(lifesub_metadata)
        
        # 파일 내용에서 추가 메타데이터 추출
        if not metadata.get('description'):
            description_match = self.description_pattern.search(code)
            if description_match:
                metadata['description'] = description_match.group(1).strip()
        
        # 기능 특성 추출
        if not metadata.get('features'):
            features = self._detect_features(code)
            if features:
                metadata['features'] = features
        
        return metadata
    
    def extract_component_metadata(self, component: Dict[str, Any], file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        컴포넌트 메타데이터 추출
        
        Args:
            component: 컴포넌트 정보
            file_info: 파일 메타데이터
            
        Returns:
            Dict[str, Any]: 추출된 메타데이터
        """
        # 기본 메타데이터
        metadata = {
            'file_path': file_info.get('file_path', ''),
            'file_name': file_info.get('file_name', ''),
            'start_pos': component.get('start_pos', 0),
            'length': len(component.get('code', '')),
            'component_type': component.get('component_type', 'unknown')
        }
        
        # props와 states가 있으면 추가
        if 'props' in component:
            metadata['props'] = component['props']
            
        if 'states' in component:
            metadata['states'] = component['states']
        
        # 카테고리 추가 (파일 정보에서 가져오기)
        if 'category' in file_info:
            metadata['category'] = file_info['category']
        
        # 목적 추론
        name = component.get('name', '')
        code = component.get('code', '')
        
        if not component.get('purpose'):
            purpose = extract_component_purpose(name, code)
            if purpose:
                metadata['purpose'] = purpose
        else:
            metadata['purpose'] = component['purpose']
        
        return metadata
    
    def _detect_features(self, code: str) -> List[str]:
        """
        코드에서 기능 특성 감지
        
        Args:
            code: 소스 코드
            
        Returns:
            List[str]: 감지된 기능 목록
        """
        features = []
        code_lower = code.lower()
        
        for feature, patterns in self.feature_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code_lower):
                    features.append(feature)
                    break
        
        return features