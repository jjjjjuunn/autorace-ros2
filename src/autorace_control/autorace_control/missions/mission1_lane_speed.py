#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
import cv2
import numpy as np

class Mission1LaneSpeedController(Node):
    def __init__(self):
        super().__init__('mission1_lane_speed_controller')
        
         # 파라미터로 토픽 이름 설정 (유연하게!)
        self.declare_parameter('camera_topic', '/camera/image_raw')  # 기본값
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('test_mode', False)
        self.declare_parameter('red_speed', 0.25)
        self.declare_parameter('blue_speed', 0.5)
        self.declare_parameter('normal_speed', 0.35)
        
        # 파라미터 읽기
        camera_topic = self.get_parameter('camera_topic').value
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.test_mode = self.get_parameter('test_mode').value
        self.red_speed = self.get_parameter('red_speed').value
        self.blue_speed = self.get_parameter('blue_speed').value
        self.normal_speed = self.get_parameter('normal_speed').value

        # ✅ 추가: 기본 임계값 파라미터
        self.declare_parameter('red_threshold', 1000)
        self.declare_parameter('blue_threshold', 1000)
        self.red_threshold = self.get_parameter('red_threshold').value
        self.blue_threshold = self.get_parameter('blue_threshold').value
        
        self.bridge = CvBridge()
        self.current_zone = "NORMAL"
        
        # Subscriber - 파라미터로 받은 토픽 이름 사용
        self.image_sub = self.create_subscription(
            Image,
            camera_topic,  # ← 유연하게 변경 가능!
            self.image_callback,
            10
        )
        
        # Publisher
        self.cmd_vel_pub = self.create_publisher(Twist, cmd_vel_topic, 10)
        self.debug_image_pub = self.create_publisher(Image, '/mission1/debug_image', 10)
        
        self.get_logger().info(f'Mission 1 Started')
        self.get_logger().info(f'  Camera topic: {camera_topic}')
        self.get_logger().info(f'  Cmd_vel topic: {cmd_vel_topic}')
        self.get_logger().info(f'  Test mode: {self.test_mode}')
        
        # 통계 정보
        self.stats = {
            'RED': 0,
            'BLUE': 0,
            'NORMAL': 0
        }
        
        self.get_logger().info(f'Mission 1 Started (test_mode={self.test_mode})')

        # 임계값 자동 조정
        self.declare_parameter('adaptive_threshold', True)
        self.adaptive_threshold = self.get_parameter('adaptive_threshold').value
        
        # 픽셀 카운트 히스토리 (최근 100프레임)
        from collections import deque
        self.red_history = deque(maxlen=100)
        self.blue_history = deque(maxlen=100)

        self.current_speed = self.normal_speed  # 현재 속도
        self.target_speed = self.normal_speed   # 목표 속도
        
        self.declare_parameter('speed_smoothing', 0.1)  # 0~1 (0.1 = 부드럽게)
        self.speed_smoothing = self.get_parameter('speed_smoothing').value
    
    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # 색상 구역 감지
            zone, speed, debug_info = self.detect_speed_zone(cv_image)
            
            # 통계 업데이트
            self.stats[zone] += 1
            
            # 속도 발행
            self.publish_velocity(speed)
            
            # 디버깅 이미지 발행
            debug_image = self.create_debug_image(cv_image, zone, debug_info)
            debug_msg = self.bridge.cv2_to_imgmsg(debug_image, "bgr8")
            self.debug_image_pub.publish(debug_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error: {e}')
    
    def detect_speed_zone(self, image):
        """색상 구역 감지"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
        height, width = hsv.shape[:2]
        roi_y_start = int(height * 0.7)
        roi_hsv = hsv[roi_y_start:, :]
        
        red_mask = self.detect_red(roi_hsv)
        blue_mask = self.detect_blue(roi_hsv)
        
        red_pixels = cv2.countNonZero(red_mask)
        blue_pixels = cv2.countNonZero(blue_mask)
        
        # 히스토리 업데이트
        self.red_history.append(red_pixels)
        self.blue_history.append(blue_pixels)
        
        # 적응형 임계값 (최근 100프레임의 평균의 50%)
        if self.adaptive_threshold and len(self.red_history) > 50:
            red_threshold = max(500, np.mean(self.red_history) * 0.5)
            blue_threshold = max(500, np.mean(self.blue_history) * 0.5)
        else:
            red_threshold = self.red_threshold
            blue_threshold = self.blue_threshold
        
        # 구역 판단
        if red_pixels > red_threshold:
            zone = "RED"
            speed = self.red_speed
        elif blue_pixels > blue_threshold:
            zone = "BLUE"
            speed = self.blue_speed
        else:
            zone = "NORMAL"
            speed = self.normal_speed
        
        # 로깅
        if zone != self.current_zone:
            self.get_logger().info(
                f'Zone: {self.current_zone} → {zone} '
                f'(R:{red_pixels}, B:{blue_pixels})'
            )
            self.current_zone = zone
        
        debug_info = {
            'red_pixels': red_pixels,
            'blue_pixels': blue_pixels,
            'red_mask': red_mask,
            'blue_mask': blue_mask
        }
        # 목표 속도 설정
        self.target_speed = speed
        
        # 스무딩
        self.current_speed += (self.target_speed - self.current_speed) * self.speed_smoothing
        
        return zone, self.current_speed, debug_info
    
    def detect_red(self, hsv_image):
        """빨간색 감지 - 조명 변화에 강건"""
        # H: 0-10, 170-180
        # S: 70-255 (더 낮은 채도도 허용)
        # V: 80-255 (더 어두운 빨강도 허용)
        lower1 = np.array([0, 70, 80])    # 더 관대하게
        upper1 = np.array([10, 255, 255])
        mask1 = cv2.inRange(hsv_image, lower1, upper1)
        
        lower2 = np.array([170, 70, 80])  # 더 관대하게
        upper2 = np.array([180, 255, 255])
        mask2 = cv2.inRange(hsv_image, lower2, upper2)
        
        # 노이즈 제거
        mask = cv2.bitwise_or(mask1, mask2)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # 작은 점 제거
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # 구멍 메우기
        
        return mask

    def detect_blue(self, hsv_image):
        """파란색 감지 - 조명 변화에 강건"""
        # H: 100-130
        # S: 70-255 (더 낮은 채도도 허용)
        # V: 80-255 (더 어두운 파랑도 허용)
        lower = np.array([100, 70, 80])   # 더 관대하게
        upper = np.array([130, 255, 255])
        mask = cv2.inRange(hsv_image, lower, upper)
        
        # 노이즈 제거
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    def publish_velocity(self, linear_speed):
        """속도 명령 발행"""
        msg = Twist()
        msg.linear.x = linear_speed
        msg.angular.z = 0.0
        self.cmd_vel_pub.publish(msg)
    
    def create_debug_image(self, original, zone, debug_info):
        """디버깅 이미지 생성"""
        debug = original.copy()
        
        # 색상 선택
        color = (0, 0, 255) if zone == "RED" else \
                (255, 0, 0) if zone == "BLUE" else (0, 255, 0)
        
        # 텍스트 오버레이
        cv2.putText(debug, f'ZONE: {zone}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        cv2.putText(debug, f'Red Pixels: {debug_info["red_pixels"]}', (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.putText(debug, f'Blue Pixels: {debug_info["blue_pixels"]}', (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # 통계 표시
        total = sum(self.stats.values())
        if total > 0:
            cv2.putText(debug, f'Stats: R={self.stats["RED"]} B={self.stats["BLUE"]} N={self.stats["NORMAL"]}', 
                        (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return debug
    
    def print_statistics(self):
        """통계 출력"""
        total = sum(self.stats.values())
        if total > 0:
            self.get_logger().info(
                f"Statistics: RED={self.stats['RED']/total*100:.1f}% "
                f"BLUE={self.stats['BLUE']/total*100:.1f}% "
                f"NORMAL={self.stats['NORMAL']/total*100:.1f}%"
            )

def main(args=None):
    rclpy.init(args=args)
    node = Mission1LaneSpeedController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.print_statistics()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
