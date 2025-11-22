#!/usr/bin/env python3
"""
라인 검출 유틸리티
- 엣지 기반 라인 검출
- Hough Transform
"""

import cv2
import numpy as np


class LineDetector:
    """라인 검출 클래스"""
    
    @staticmethod
    def detect_edges(image, low_threshold=50, high_threshold=150):
        """
        Canny 엣지 검출
        
        Args:
            image: 그레이스케일 이미지
            low_threshold: 하한 임계값
            high_threshold: 상한 임계값
        
        Returns:
            edges: 엣지 이미지
        """
        return cv2.Canny(image, low_threshold, high_threshold)
    
    @staticmethod
    def detect_lines(edges, threshold=50, min_line_length=30, max_line_gap=10):
        """
        Hough Line Transform으로 라인 검출
        
        Args:
            edges: 엣지 이미지
            threshold: 검출 임계값
            min_line_length: 최소 라인 길이
            max_line_gap: 최대 간격
        
        Returns:
            lines: 검출된 라인 배열 [[x1, y1, x2, y2], ...]
        """
        lines = cv2.HoughLinesP(
            edges, 
            rho=1, 
            theta=np.pi/180, 
            threshold=threshold,
            minLineLength=min_line_length, 
            maxLineGap=max_line_gap
        )
        return lines if lines is not None else []
    
    @staticmethod
    def filter_horizontal_lines(lines, angle_threshold=15):
        """
        수평선만 필터링
        
        Args:
            lines: 라인 배열
            angle_threshold: 각도 허용 범위 (도)
        
        Returns:
            horizontal_lines: 수평선 배열
        """
        horizontal_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            
            # 거의 수평인 선 (0도 또는 180도 근처)
            if angle < angle_threshold or angle > (180 - angle_threshold):
                horizontal_lines.append(line)
        
        return horizontal_lines
    
    @staticmethod
    def filter_vertical_lines(lines, angle_threshold=15):
        """
        수직선만 필터링
        
        Args:
            lines: 라인 배열
            angle_threshold: 각도 허용 범위 (도)
        
        Returns:
            vertical_lines: 수직선 배열
        """
        vertical_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            
            # 거의 수직인 선 (90도 근처)
            if 90 - angle_threshold < angle < 90 + angle_threshold:
                vertical_lines.append(line)
        
        return vertical_lines
    
    @staticmethod
    def get_line_center(lines):
        """
        라인들의 평균 중심점 계산
        
        Args:
            lines: 라인 배열
        
        Returns:
            (cx, cy): 중심 좌표
        """
        if len(lines) == 0:
            return None
        
        centers = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            centers.append((cx, cy))
        
        avg_cx = int(np.mean([c[0] for c in centers]))
        avg_cy = int(np.mean([c[1] for c in centers]))
        
        return (avg_cx, avg_cy)
