#!/usr/bin/env python3
"""
미션 4: 차선 변경 (마커 감지)
- 좌/우 화살표 마커 감지
- 마커 방향으로 차선 변경
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class LaneChangeMission(Node):
    def __init__(self):
        super().__init__('lane_change_mission')
        
        # 파라미터
        self.declare_parameter('debug_mode', True)
        self.declare_parameter('normal_speed', 0.15)
        self.declare_parameter('lane_change_speed', 0.1)
        self.declare_parameter('angular_speed', 0.6)
        self.declare_parameter('marker_area_threshold', 3000)
        
        self.debug_mode = self.get_parameter('debug_mode').value
        self.normal_speed = self.get_parameter('normal_speed').value
        self.lane_change_speed = self.get_parameter('lane_change_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.marker_area_threshold = self.get_parameter('marker_area_threshold').value
        
        # 상태
        self.mission_active = False
        self.lane_changing = False
        self.change_direction = None  # 'LEFT' or 'RIGHT'
        self.lane_change_stage = 0  # 0: 감지, 1: 변경중, 2: 복귀중
        self.lane_change_timer = 0
        
        self.bridge = CvBridge()
        
        # Subscriber
        self.create_subscription(String, '/mission/current', 
                               self.mission_callback, 10)
        self.create_subscription(Image, '/camera/image_raw', 
                               self.image_callback, 10)
        
        # Publisher
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.mission_complete_pub = self.create_publisher(String, '/mission/complete', 10)
        self.debug_image_pub = self.create_publisher(Image, '/vision/lane_change_debug', 10)
        
        self.get_logger().info('차선 변경 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 LANE_CHANGE인지 확인"""
        if msg.data == 'LANE_CHANGE':
            if not self.mission_active:
                self.get_logger().info('🔄 차선 변경 미션 시작!')
                self.mission_active = True
                self.lane_changing = False
                self.lane_change_stage = 0
        else:
            if self.mission_active:
                complete_msg = String()
                complete_msg.data = 'LANE_CHANGE'
                self.mission_complete_pub.publish(complete_msg)
            self.mission_active = False
    
    def image_callback(self, msg):
        """마커 검출 및 차선 변경"""
        if not self.mission_active:
            return
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            if not self.lane_changing:
                # 마커 감지
                direction = self.detect_marker(cv_image)
                
                if direction:
                    self.start_lane_change(direction)
            else:
                # 차선 변경 진행
                self.execute_lane_change()
            
        except Exception as e:
            self.get_logger().error(f'이미지 처리 실패: {str(e)}')
    
    def detect_marker(self, image):
        """좌/우 화살표 마커 감지"""
        height, width = image.shape[:2]
        
        # ROI: 중앙 상단 (도로 표지판 위치)
        roi_top = int(height * 0.2)
        roi_bottom = int(height * 0.5)
        roi_left = int(width * 0.3)
        roi_right = int(width * 0.7)
        roi = image[roi_top:roi_bottom, roi_left:roi_right]
        
        # 파란색 마커 검출 (화살표가 파란색이라고 가정)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([100, 100, 100])
        upper_blue = np.array([130, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # 노이즈 제거
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 윤곽선 검출
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        direction = None
        
        if contours:
            # 가장 큰 윤곽선
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if area > self.marker_area_threshold:
                # 바운딩 박스
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # 화살표 모멘트로 방향 판단
                M = cv2.moments(largest_contour)
                if M['m00'] > 0:
                    cx = int(M['m10'] / M['m00'])
                    roi_center = roi.shape[1] // 2
                    
                    # 중심이 ROI 왼쪽에 있으면 좌회전, 오른쪽에 있으면 우회전
                    if cx < roi_center - 20:
                        direction = 'LEFT'
                    elif cx > roi_center + 20:
                        direction = 'RIGHT'
                
                # 디버그 시각화
                if self.debug_mode and direction:
                    debug_image = image.copy()
                    cv2.rectangle(debug_image, 
                                (roi_left + x, roi_top + y), 
                                (roi_left + x + w, roi_top + y + h), 
                                (0, 255, 0), 2)
                    
                    arrow_text = '⬅️ LEFT' if direction == 'LEFT' else '➡️ RIGHT'
                    cv2.putText(debug_image, arrow_text, 
                              (roi_left + x, roi_top + y - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    
                    try:
                        debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                        self.debug_image_pub.publish(debug_msg)
                    except:
                        pass
        
        return direction
    
    def start_lane_change(self, direction):
        """차선 변경 시작"""
        self.lane_changing = True
        self.change_direction = direction
        self.lane_change_stage = 1
        self.lane_change_timer = 0
        
        arrow = '⬅️' if direction == 'LEFT' else '➡️'
        self.get_logger().info(f'{arrow} {direction} 차선 변경 시작!')
    
    def execute_lane_change(self):
        """차선 변경 실행"""
        cmd = Twist()
        self.lane_change_timer += 1
        
        # 3단계 차선 변경
        # Stage 1: 대각선으로 이동 (30 프레임)
        if self.lane_change_stage == 1:
            cmd.linear.x = self.lane_change_speed
            
            if self.change_direction == 'LEFT':
                cmd.angular.z = self.angular_speed
            else:
                cmd.angular.z = -self.angular_speed
            
            if self.lane_change_timer > 30:
                self.lane_change_stage = 2
                self.lane_change_timer = 0
        
        # Stage 2: 복귀 (30 프레임)
        elif self.lane_change_stage == 2:
            cmd.linear.x = self.lane_change_speed
            
            if self.change_direction == 'LEFT':
                cmd.angular.z = -self.angular_speed * 0.5
            else:
                cmd.angular.z = self.angular_speed * 0.5
            
            if self.lane_change_timer > 30:
                self.lane_change_stage = 3
                self.lane_change_timer = 0
        
        # Stage 3: 완료 (20 프레임 직진)
        elif self.lane_change_stage == 3:
            cmd.linear.x = self.normal_speed
            cmd.angular.z = 0.0
            
            if self.lane_change_timer > 20:
                self.complete_lane_change()
        
        self.cmd_vel_pub.publish(cmd)
    
    def complete_lane_change(self):
        """차선 변경 완료"""
        self.get_logger().info('✅ 차선 변경 완료!')
        
        # 미션 완료
        complete_msg = String()
        complete_msg.data = 'LANE_CHANGE'
        self.mission_complete_pub.publish(complete_msg)
        
        self.mission_active = False
        self.lane_changing = False
        self.lane_change_stage = 0


def main(args=None):
    rclpy.init(args=args)
    node = LaneChangeMission()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
