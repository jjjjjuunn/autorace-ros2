#!/usr/bin/env python3
"""
주차 미션
- 빈 주차 공간 검출
- 후진 주차 수행
- 주차 완료 후 전진 복귀
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import time


class ParkingMission(Node):
    def __init__(self):
        super().__init__('parking_mission')
        
        # 파라미터
        self.declare_parameter('debug_mode', True)
        self.declare_parameter('parking_speed', 0.08)
        self.declare_parameter('reverse_speed', -0.08)
        
        self.debug_mode = self.get_parameter('debug_mode').value
        self.parking_speed = self.get_parameter('parking_speed').value
        self.reverse_speed = self.get_parameter('reverse_speed').value
        
        # 상태
        self.mission_active = False
        self.parking_state = 'SEARCHING'  # SEARCHING, ALIGNING, REVERSING, PARKED, EXITING
        self.empty_space_detected = False
        self.detection_count = 0
        self.detection_confirm_threshold = 5
        self.parking_timer = None
        
        self.bridge = CvBridge()
        
        # Subscriber
        self.create_subscription(String, '/mission/current', 
                               self.mission_callback, 10)
        self.create_subscription(Image, '/camera/image_raw', 
                               self.image_callback, 10)
        
        # Publisher
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.mission_complete_pub = self.create_publisher(String, '/mission/complete', 10)
        self.debug_image_pub = self.create_publisher(Image, '/vision/parking_debug', 10)
        
        self.get_logger().info('주차 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 PARKING인지 확인"""
        if msg.data == 'PARKING':
            if not self.mission_active:
                self.get_logger().info('🅿️ 주차 미션 시작!')
                self.mission_active = True
                self.parking_state = 'SEARCHING'
                self.detection_count = 0
        else:
            self.mission_active = False
    
    def image_callback(self, msg):
        """주차 공간 검출"""
        if not self.mission_active:
            return
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            if self.parking_state == 'SEARCHING':
                detected = self.detect_parking_space(cv_image)
                
                if detected:
                    self.detection_count += 1
                else:
                    self.detection_count = max(0, self.detection_count - 1)
                
                if self.detection_count >= self.detection_confirm_threshold:
                    self.start_parking()
            
        except Exception as e:
            self.get_logger().error(f'이미지 처리 실패: {str(e)}')
    
    def detect_parking_space(self, image):
        """빈 주차 공간 검출 (측면 카메라)"""
        height, width = image.shape[:2]
        
        # ROI: 우측 영역 (주차 공간)
        roi_left = int(width * 0.6)
        roi = image[0:height, roi_left:width]
        
        # 전처리
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 엣지 검출
        edges = cv2.Canny(blur, 50, 150)
        
        # 수직선 검출 (주차 구획선)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, 
                               minLineLength=40, maxLineGap=20)
        
        detected = False
        debug_image = image.copy()
        
        if lines is not None:
            vertical_lines = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                
                # 수직선 필터링 (80-100도)
                if 80 < angle < 100:
                    vertical_lines.append(line)
            
            # 빈 공간 판단: 수직선이 2개 이상 (양쪽 경계)
            if len(vertical_lines) >= 2:
                # 라인 사이 간격 확인
                x_coords = [line[0][0] for line in vertical_lines]
                x_coords.sort()
                
                # 충분한 간격 (주차 가능한 너비)
                if len(x_coords) >= 2 and (x_coords[-1] - x_coords[0]) > 50:
                    detected = True
                    
                    if self.debug_mode:
                        for line in vertical_lines:
                            x1, y1, x2, y2 = line[0]
                            cv2.line(debug_image, (roi_left + x1, y1), 
                                   (roi_left + x2, y2), (0, 255, 0), 3)
                        cv2.putText(debug_image, 'EMPTY SPACE', (10, 50),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        # 디버그 이미지
        if self.debug_mode:
            cv2.rectangle(debug_image, (roi_left, 0), (width, height), (255, 0, 0), 2)
            cv2.putText(debug_image, f'State: {self.parking_state}', (10, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            try:
                debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                self.debug_image_pub.publish(debug_msg)
            except:
                pass
        
        return detected
    
    def start_parking(self):
        """주차 시작"""
        self.get_logger().info('🅿️ 빈 주차 공간 발견! 주차 시작')
        self.parking_state = 'ALIGNING'
        
        # 1단계: 정렬 (약간 전진)
        self.create_timer(0.5, self.align_for_parking, one_shot=True)
    
    def align_for_parking(self):
        """주차 정렬"""
        self.get_logger().info('정렬 중...')
        
        cmd = Twist()
        cmd.linear.x = self.parking_speed
        cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(cmd)
        
        # 0.5초 후 후진 시작
        self.create_timer(0.5, self.start_reversing, one_shot=True)
    
    def start_reversing(self):
        """후진 주차 시작"""
        self.get_logger().info('후진 주차 중...')
        self.parking_state = 'REVERSING'
        
        # 후진
        cmd = Twist()
        cmd.linear.x = self.reverse_speed
        cmd.angular.z = 0.3  # 약간 꺾으면서 후진
        self.cmd_vel_pub.publish(cmd)
        
        # 2초 후 정지
        self.create_timer(2.0, self.stop_in_parking, one_shot=True)
    
    def stop_in_parking(self):
        """주차 완료 - 정지"""
        self.get_logger().info('✅ 주차 완료!')
        self.parking_state = 'PARKED'
        
        # 정지
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(cmd)
        
        # 3초 대기 후 출발
        self.create_timer(3.0, self.exit_parking, one_shot=True)
    
    def exit_parking(self):
        """주차장 탈출"""
        self.get_logger().info('🚗 주차장 탈출 중...')
        self.parking_state = 'EXITING'
        
        # 전진 복귀
        cmd = Twist()
        cmd.linear.x = self.parking_speed
        cmd.angular.z = -0.3  # 반대 방향으로 꺾으면서 전진
        self.cmd_vel_pub.publish(cmd)
        
        # 2초 후 미션 완료
        self.create_timer(2.0, self.complete_mission, one_shot=True)
    
    def complete_mission(self):
        """미션 완료"""
        self.get_logger().info('✅ 주차 미션 완료!')
        
        # 정상 주행 복귀
        cmd = Twist()
        cmd.linear.x = 0.15
        cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(cmd)
        
        # 미션 완료 신호
        complete_msg = String()
        complete_msg.data = 'PARKING'
        self.mission_complete_pub.publish(complete_msg)
        
        self.mission_active = False
        self.parking_state = 'SEARCHING'


def main(args=None):
    rclpy.init(args=args)
    node = ParkingMission()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
