#!/usr/bin/env python3
"""
교차로 미션
- 좌회전/우회전/직진 표지판 인식
- 경로에 따른 주행
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class IntersectionMission(Node):
    def __init__(self):
        super().__init__('intersection_mission')
        
        # 파라미터
        self.declare_parameter('debug_mode', True)
        self.declare_parameter('turn_speed', 0.1)
        self.declare_parameter('turn_duration', 2.0)
        
        self.debug_mode = self.get_parameter('debug_mode').value
        self.turn_speed = self.get_parameter('turn_speed').value
        self.turn_duration = self.get_parameter('turn_duration').value
        
        # 상태
        self.mission_active = False
        self.detected_direction = 'NONE'  # LEFT, RIGHT, STRAIGHT
        self.detection_count = {'LEFT': 0, 'RIGHT': 0, 'STRAIGHT': 0}
        self.detection_confirm_threshold = 5
        self.is_turning = False
        
        self.bridge = CvBridge()
        
        # Subscriber
        self.create_subscription(String, '/mission/current', 
                               self.mission_callback, 10)
        self.create_subscription(Image, '/camera/image_raw', 
                               self.image_callback, 10)
        
        # Publisher
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.mission_complete_pub = self.create_publisher(String, '/mission/complete', 10)
        self.debug_image_pub = self.create_publisher(Image, '/vision/intersection_debug', 10)
        
        self.get_logger().info('교차로 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 INTERSECTION인지 확인"""
        if msg.data == 'INTERSECTION':
            if not self.mission_active:
                self.get_logger().info('🛣️ 교차로 미션 시작!')
                self.mission_active = True
                self.detected_direction = 'NONE'
                self.detection_count = {'LEFT': 0, 'RIGHT': 0, 'STRAIGHT': 0}
        else:
            self.mission_active = False
    
    def image_callback(self, msg):
        """표지판 검출"""
        if not self.mission_active or self.is_turning:
            return
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            direction = self.detect_sign(cv_image)
            
            # 검출 카운트 업데이트
            if direction in ['LEFT', 'RIGHT', 'STRAIGHT']:
                self.detection_count[direction] += 1
                # 다른 방향 카운트 감소
                for d in self.detection_count:
                    if d != direction:
                        self.detection_count[d] = max(0, self.detection_count[d] - 1)
            
            # 확정된 방향 판단
            for direction, count in self.detection_count.items():
                if count >= self.detection_confirm_threshold:
                    if self.detected_direction != direction:
                        self.execute_turn(direction)
                        self.detected_direction = direction
            
        except Exception as e:
            self.get_logger().error(f'이미지 처리 실패: {str(e)}')
    
    def detect_sign(self, image):
        """방향 표지판 검출 (간단한 화살표 검출)"""
        height, width = image.shape[:2]
        
        # ROI: 상단 중앙 (표지판 위치)
        roi_top = int(height * 0.1)
        roi_bottom = int(height * 0.5)
        roi_left = int(width * 0.3)
        roi_right = int(width * 0.7)
        roi = image[roi_top:roi_bottom, roi_left:roi_right]
        
        # 전처리
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 엣지 검출
        edges = cv2.Canny(blur, 50, 150)
        
        # 라인 검출
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 30, 
                               minLineLength=20, maxLineGap=10)
        
        detected_direction = 'NONE'
        debug_image = image.copy()
        
        if lines is not None:
            # 선의 각도 분석
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                angles.append(angle)
                
                if self.debug_mode:
                    cv2.line(debug_image, (roi_left + x1, roi_top + y1), 
                           (roi_left + x2, roi_top + y2), (0, 255, 255), 2)
            
            if len(angles) > 0:
                avg_angle = np.mean(angles)
                
                # 각도 기반 방향 판단
                if -60 < avg_angle < -30:  # 좌향 화살표
                    detected_direction = 'LEFT'
                elif 30 < avg_angle < 60:   # 우향 화살표
                    detected_direction = 'RIGHT'
                elif -15 < avg_angle < 15 or abs(avg_angle) > 165:  # 직진
                    detected_direction = 'STRAIGHT'
        
        # 디버그 시각화
        if self.debug_mode:
            cv2.rectangle(debug_image, (roi_left, roi_top), 
                         (roi_right, roi_bottom), (255, 0, 0), 2)
            
            color = (0, 255, 0) if detected_direction != 'NONE' else (128, 128, 128)
            cv2.putText(debug_image, f'Direction: {detected_direction}', (10, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            
            try:
                debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                self.debug_image_pub.publish(debug_msg)
            except:
                pass
        
        return detected_direction
    
    def execute_turn(self, direction):
        """회전 실행"""
        self.get_logger().info(f'🛣️ {direction} 방향으로 회전!')
        self.is_turning = True
        
        cmd = Twist()
        cmd.linear.x = self.turn_speed
        
        if direction == 'LEFT':
            cmd.angular.z = 0.5  # 좌회전
        elif direction == 'RIGHT':
            cmd.angular.z = -0.5  # 우회전
        else:  # STRAIGHT
            cmd.angular.z = 0.0
        
        self.cmd_vel_pub.publish(cmd)
        
        # 회전 지속 시간 후 미션 완료
        self.create_timer(self.turn_duration, self.complete_turn, one_shot=True)
    
    def complete_turn(self):
        """회전 완료"""
        self.get_logger().info('✅ 교차로 통과 완료!')
        
        # 정상 주행 복귀
        cmd = Twist()
        cmd.linear.x = 0.15
        cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(cmd)
        
        # 미션 완료
        complete_msg = String()
        complete_msg.data = 'INTERSECTION'
        self.mission_complete_pub.publish(complete_msg)
        
        self.mission_active = False
        self.is_turning = False


def main(args=None):
    rclpy.init(args=args)
    node = IntersectionMission()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
