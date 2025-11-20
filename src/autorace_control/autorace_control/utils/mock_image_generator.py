#!/usr/bin/env python3
import cv2
import numpy as np

class MockImageGenerator:
    """Gazebo 없이 테스트용 이미지 생성"""
    
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
    
    def generate_red_zone_image(self):
        """빨간색 구역이 있는 이미지 생성"""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # 배경 (도로)
        img[:] = (50, 50, 50)  # 회색 도로
        
        # 노란 차선 (왼쪽)
        cv2.rectangle(img, (50, 0), (100, self.height), (0, 255, 255), -1)
        
        # 흰 차선 (오른쪽)
        cv2.rectangle(img, (540, 0), (590, self.height), (255, 255, 255), -1)
        
        # 빨간색 구역 (하단 30%)
        red_start_y = int(self.height * 0.7)
        cv2.rectangle(img, (150, red_start_y), (490, self.height), 
                      (0, 0, 255), -1)  # BGR: 빨강
        
        return img
    
    def generate_blue_zone_image(self):
        """파란색 구역이 있는 이미지 생성"""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        img[:] = (50, 50, 50)
        cv2.rectangle(img, (50, 0), (100, self.height), (0, 255, 255), -1)
        cv2.rectangle(img, (540, 0), (590, self.height), (255, 255, 255), -1)
        
        # 파란색 구역
        blue_start_y = int(self.height * 0.7)
        cv2.rectangle(img, (150, blue_start_y), (490, self.height), 
                      (255, 0, 0), -1)  # BGR: 파랑
        
        return img
    
    def generate_normal_zone_image(self):
        """일반 도로 이미지 생성"""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        img[:] = (50, 50, 50)
        cv2.rectangle(img, (50, 0), (100, self.height), (0, 255, 255), -1)
        cv2.rectangle(img, (540, 0), (590, self.height), (255, 255, 255), -1)
        
        return img
    
    def save_test_images(self, output_dir='test_images'):
        """테스트 이미지 파일로 저장"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        cv2.imwrite(f'{output_dir}/red_zone.png', self.generate_red_zone_image())
        cv2.imwrite(f'{output_dir}/blue_zone.png', self.generate_blue_zone_image())
        cv2.imwrite(f'{output_dir}/normal_zone.png', self.generate_normal_zone_image())
        
        print(f"Test images saved to {output_dir}/")

if __name__ == '__main__':
    generator = MockImageGenerator()
    generator.save_test_images()
