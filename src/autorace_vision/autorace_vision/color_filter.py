#!/usr/bin/env python3
"""
공통 컬러 필터 유틸리티
- HSV 기반 색상 검출
- 재사용 가능한 컬러 필터
"""

import cv2
import numpy as np


class ColorFilter:
    """색상 필터 클래스"""
    
    # 사전 정의된 색상 범위 (HSV)
    COLOR_RANGES = {
        'white': [(0, 0, 200), (180, 30, 255)],
        'yellow': [(20, 100, 100), (30, 255, 255)],
        'red_low': [(0, 100, 100), (10, 255, 255)],
        'red_high': [(170, 100, 100), (180, 255, 255)],
        'green': [(40, 100, 100), (80, 255, 255)],
        'blue': [(100, 100, 100), (130, 255, 255)],
    }
    
    @staticmethod
    def apply_color_filter(image, color_name):
        """
        이미지에 색상 필터 적용
        
        Args:
            image: BGR 이미지
            color_name: 색상 이름 ('white', 'yellow', 'red', 'green', 'blue')
        
        Returns:
            mask: 이진 마스크 이미지
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        if color_name == 'red':
            # 빨간색은 두 범위 조합
            lower1, upper1 = ColorFilter.COLOR_RANGES['red_low']
            lower2, upper2 = ColorFilter.COLOR_RANGES['red_high']
            mask1 = cv2.inRange(hsv, np.array(lower1), np.array(upper1))
            mask2 = cv2.inRange(hsv, np.array(lower2), np.array(upper2))
            mask = cv2.bitwise_or(mask1, mask2)
        elif color_name in ColorFilter.COLOR_RANGES:
            lower, upper = ColorFilter.COLOR_RANGES[color_name]
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        else:
            raise ValueError(f"Unknown color: {color_name}")
        
        return mask
    
    @staticmethod
    def apply_multi_color_filter(image, color_names):
        """
        여러 색상 필터 동시 적용
        
        Args:
            image: BGR 이미지
            color_names: 색상 이름 리스트
        
        Returns:
            mask: 통합 이진 마스크
        """
        masks = []
        for color_name in color_names:
            mask = ColorFilter.apply_color_filter(image, color_name)
            masks.append(mask)
        
        # 모든 마스크 OR 연산
        combined_mask = masks[0]
        for mask in masks[1:]:
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        return combined_mask
    
    @staticmethod
    def morphology_clean(mask, kernel_size=5):
        """
        모폴로지 연산으로 노이즈 제거
        
        Args:
            mask: 이진 마스크
            kernel_size: 커널 크기
        
        Returns:
            cleaned_mask: 정제된 마스크
        """
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        cleaned = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        return cleaned
