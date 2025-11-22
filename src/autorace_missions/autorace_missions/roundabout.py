#!/usr/bin/env python3
"""
미션 5: 회전 교차로 (동적 장애물 회피)
- 원형 차로 추적
- 움직이는 장애물 회피
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image, LaserScan
from cv_bridge import CvBridge
import cv2
import numpy as np


class RoundaboutMission(Node):
    def __init__(self):
        super().__init__('roundabout_mission')
        
        # 파라미터
        self.declare_parameter('debug_mode', True)
        self.declare_parameter('normal_speed', 0.12)
        self.declare_parameter('slow_speed', 0.06)
        self.declare_parameter('angular_gain', 0.012)
        self.declare_parameter('safe_distance', 0.5)
        self.declare_parameter('roundabout_duration', 150)  # 프레임 (약 5초)
        
        self.debug_mode = self.get_parameter('debug_mode').value
        self.normal_speed = self.get_parameter('normal_speed').value
        self.slow_speed = self.get_parameter('slow_speed').value
        self.angular_gain = self.get_parameter('angular_gain').value
        self.safe_distance = self.get_parameter('safe_distance').value
        self.roundabout_duration = self.get_parameter('roundabout_duration').value
        
        # 상태
        self.mission_active = False
        self.in_roundabout = False
        self.roundabout_timer = 0
        self.obstacle_detected = False
        
        self.bridge = CvBridge()
        
        # Subscriber
        self.create_subscription(String, '/mission/current', 
                               self.mission_callback, 10)
        self.create_subscription(Image, '/camera/image_raw', 
                               self.image_callback, 10)
        self.create_subscription(LaserScan, '/scan', 
                               self.lidar_callback, 10)
        
        # Publisher
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.mission_complete_pub = self.create_publisher(String, '/mission/complete', 10)
        self.debug_image_pub = self.create_publisher(Image, '/vision/roundabout_debug', 10)
        
        self.get_logger().info('회전 교차로 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 ROUNDABOUT인지 확인"""
        if msg.data == 'ROUNDABOUT':
            if not self.mission_active:
                self.get_logger().info('🔄 회전 교차로 미션 시작!')
                self.mission_active = True
                self.in_roundabout = False
                self.roundabout_timer = 0
        else:
            if self.mission_active:
                complete_msg = String()
                complete_msg.data = 'ROUNDABOUT'
                self.mission_complete_pub.publish(complete_msg)
            self.mission_active = False
    
    def image_callback(self, msg):
        """원형 차로 추적"""
        if not self.mission_active:
            return
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # 회전 교차로 진입 감지
            if not self.in_roundabout:
                entered = self.detect_roundabout_entry(cv_image)
                if entered:
                    self.enter_roundabout()
            
            # 차로 추적
            error = self.track_circular_lane(cv_image)
            self.control_vehicle(error)
            
            # 타이머 업데이트
            if self.in_roundabout:
                self.roundabout_timer += 1
                
                if self.roundabout_timer >= self.roundabout_duration:
                    self.exit_roundabout()
            
        except Exception as e:
            self.get_logger().error(f'이미지 처리 실패: {str(e)}')
    
    def lidar_callback(self, msg):
        """동적 장애물 감지"""
        if not self.mission_active or not self.in_roundabout:
            return
        
        try:
            ranges = np.array(msg.ranges)
            ranges[np.isinf(ranges)] = msg.range_max
            ranges[np.isnan(ranges)] = msg.range_max
            
            # 전방 장애물 확인
            num_points = len(ranges)
            front_indices = list(range(0, num_points // 12)) + \
                          list(range(num_points - num_points // 12, num_points))
            front_distances = ranges[front_indices]
            front_min = np.min(front_distances)
            
            # 장애물 감지
            if front_min < self.safe_distance:
                if not self.obstacle_detected:
                    self.get_logger().info('⚠️ 동적 장애물 감지! 서행합니다.')
                self.obstacle_detected = True
            else:
                if self.obstacle_detected:
                    self.get_logger().info('✅ 장애물 통과!')
                self.obstacle_detected = False
        
        except Exception as e:
            self.get_logger().error(f'LiDAR 처리 실패: {str(e)}')
    
    def detect_roundabout_entry(self, image):
        """회전 교차로 진입 감지 (원형 패턴)"""
        height, width = image.shape[:2]
        roi = image[int(height*0.5):height, 0:width]
        
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 원형 검출 (Hough Circle)
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=100,
            param2=30,
            minRadius=20,
            maxRadius=100
        )
        
        if circles is not None:
            self.get_logger().info('회전 교차로 진입 감지!')
            return True
        
        return False
    
    def enter_roundabout(self):
        """회전 교차로 진입"""
        self.get_logger().info('🔄 회전 교차로 진입!')
        self.in_roundabout = True
        self.roundabout_timer = 0
    
    def track_circular_lane(self, image):
        """원형 차로 추적"""
        height, width = image.shape[:2]
        roi_top = int(height * 0.6)
        roi = image[roi_top:height, 0:width]
        
        # 흰색/노란색 차선 검출
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([30, 255, 255])
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        lane_mask = cv2.bitwise_or(white_mask, yellow_mask)
        
        # 오른쪽 차선 우선 추적 (회전 교차로는 반시계방향)
        # ROI를 오른쪽으로 치우쳐서 설정
        roi_mask = np.zeros_like(lane_mask)
        roi_mask[:, width//2:] = lane_mask[:, width//2:]
        
        # 중심 계산
        M = cv2.moments(roi_mask)
        error = 0
        
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            # 회전 교차로에서는 오른쪽으로 약간 치우쳐서 주행
            target_center = int(width * 0.6)
            error = cx - target_center
        
        # 디버그
        if self.debug_mode:
            debug_image = image.copy()
            cv2.rectangle(debug_image, (0, roi_top), (width, height), (255, 0, 0), 2)
            cv2.putText(debug_image, f'Timer: {self.roundabout_timer}/{self.roundabout_duration}',
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            try:
                debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                self.debug_image_pub.publish(debug_msg)
            except:
                pass
        
        return error
    
    def control_vehicle(self, error):
        """차량 제어"""
        cmd = Twist()
        
        if not self.in_roundabout:
            # 아직 진입 전 - 정상 주행
            cmd.linear.x = self.normal_speed
            cmd.angular.z = 0.0
        else:
            # 회전 교차로 내부
            if self.obstacle_detected:
                cmd.linear.x = self.slow_speed
            else:
                cmd.linear.x = self.normal_speed
            
            # 회전 제어 (반시계방향 회전을 위해 약간의 좌회전 바이어스)
            cmd.angular.z = 0.3 - self.angular_gain * error
        
        self.cmd_vel_pub.publish(cmd)
    
    def exit_roundabout(self):
        """회전 교차로 탈출"""
        self.get_logger().info('✅ 회전 교차로 통과 완료!')
        
        # 미션 완료
        complete_msg = String()
        complete_msg.data = 'ROUNDABOUT'
        self.mission_complete_pub.publish(complete_msg)
        
        self.mission_active = False
        self.in_roundabout = False


def main(args=None):
    rclpy.init(args=args)
    node = RoundaboutMission()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
