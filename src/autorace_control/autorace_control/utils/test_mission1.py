#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import cv2
import time

class Mission1Tester(Node):
    """미션 1 알고리즘 테스트용 이미지 발행 노드"""
    
    def __init__(self):
        super().__init__('mission1_tester')
        
        self.bridge = CvBridge()
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        
        # 테스트 시퀀스
        self.test_sequence = [
            ('normal', 3),   # 3초간 일반 도로
            ('red', 2),      # 2초간 빨간 구역
            ('normal', 2),   # 2초간 일반 도로
            ('blue', 2),     # 2초간 파란 구역
            ('normal', 3),   # 3초간 일반 도로
        ]
        
        self.current_index = 0
        self.start_time = time.time()
        
        # 타이머 (30Hz)
        self.timer = self.create_timer(1.0/30.0, self.timer_callback)
        
        self.get_logger().info('Mission 1 Tester Started')
    
    def timer_callback(self):
        """주기적으로 테스트 이미지 발행"""
        elapsed = time.time() - self.start_time
        
        # 현재 시퀀스 결정
        total_elapsed = 0
        for i, (zone_type, duration) in enumerate(self.test_sequence):
            if elapsed < total_elapsed + duration:
                self.current_index = i
                break
            total_elapsed += duration
        else:
            # 시퀀스 종료, 처음부터 반복
            self.start_time = time.time()
            self.current_index = 0
        
        # 이미지 생성
        zone_type = self.test_sequence[self.current_index][0]
        img = self.generate_image(zone_type)
        
        # ROS 메시지로 변환 및 발행
        msg = self.bridge.cv2_to_imgmsg(img, "bgr8")
        msg.header.stamp = self.get_clock().now().to_msg()
        self.image_pub.publish(msg)
    
    def generate_image(self, zone_type):
        """테스트 이미지 생성"""
        width, height = 640, 480
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 배경
        img[:] = (50, 50, 50)
        
        # 차선
        cv2.rectangle(img, (50, 0), (100, height), (0, 255, 255), -1)  # 노란 차선
        cv2.rectangle(img, (540, 0), (590, height), (255, 255, 255), -1)  # 흰 차선
        
        # 색상 구역
        roi_y = int(height * 0.7)
        if zone_type == 'red':
            cv2.rectangle(img, (150, roi_y), (490, height), (0, 0, 255), -1)
        elif zone_type == 'blue':
            cv2.rectangle(img, (150, roi_y), (490, height), (255, 0, 0), -1)
        
        return img

def main(args=None):
    rclpy.init(args=args)
    node = Mission1Tester()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()