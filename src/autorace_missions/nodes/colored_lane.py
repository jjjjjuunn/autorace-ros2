#!/usr/bin/env python
"""
미션 1: 색깔 차로 감/가속
- 빨강: 감속
- 초록: 정상 속도
- 파랑: 가속
"""

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge
import cv2
import numpy as np


class ColoredLaneMission:
    def __init__(self):
        rospy.init_node('colored_lane_mission', anonymous=False)
        
        # 파라미터
        
        self.debug_mode = rospy.get_param('~debug_mode', 0.1)
        self.slow_speed = rospy.get_param('~slow_speed', 0.1)
        self.normal_speed = rospy.get_param('~normal_speed', 0.1)
        self.fast_speed = rospy.get_param('~fast_speed', 0.1)
        self.angular_gain = rospy.get_param('~angular_gain', 0.1)
        
        # 상태
        self.mission_active = False
        self.current_color = 'GREEN'  # RED, GREEN, BLUE
        self.color_detection_count = {'RED': 0, 'GREEN': 0, 'BLUE': 0}
        self.detection_confirm_threshold = 5
        
        self.bridge = CvBridge()
        
        # Subscriber
        rospy.Subscriber('/mission/current', String, self.mission_callback, queue_size=10)
        rospy.Subscriber('/usb_cam/image_raw/compressed', CompressedImage, self.image_callback, queue_size=10)
        
        # Publisher
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.mission_complete_pub = rospy.Publisher('/mission/complete', String, queue_size=10)
        self.debug_image_pub = rospy.Publisher('/vision/colored_lane_debug', Image, queue_size=10)
        
        rospy.loginfo('색깔 차로 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 COLORED_LANE인지 확인"""
        if msg.data == 'COLORED_LANE':
            if not self.mission_active:
                rospy.loginfo('🎨 색깔 차로 미션 시작!')
                self.mission_active = True
                self.color_detection_count = {'RED': 0, 'GREEN': 0, 'BLUE': 0}
        else:
            if self.mission_active:
                # 미션 완료
                complete_msg = String()
                complete_msg.data = 'COLORED_LANE'
                self.mission_complete_pub.publish(complete_msg)
            self.mission_active = False
    
    def image_callback(self, msg):
        """차로 색깔 검출 및 속도 조절"""
        if not self.mission_active:
            return
        
        try:
            # Decompress image
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # 차로 색깔 검출
            detected_color = self.detect_lane_color(cv_image)
            
            # 검출 카운트 업데이트
            if detected_color in ['RED', 'GREEN', 'BLUE']:
                self.color_detection_count[detected_color] += 1
                for color in self.color_detection_count:
                    if color != detected_color:
                        self.color_detection_count[color] = max(0, self.color_detection_count[color] - 1)
            
            # 확정된 색깔 판단
            for color, count in self.color_detection_count.items():
                if count >= self.detection_confirm_threshold:
                    if self.current_color != color:
                        self.change_speed(color)
                        self.current_color = color
            
            # 차선 추적 + 속도 제어
            error = self.track_lane(cv_image)
            self.control_vehicle(error)
            
        except Exception as e:
            rospy.logerr(f'이미지 처리 실패: {str(e)}')
    
    def detect_lane_color(self, image):
        """차로 색깔 검출"""
        height, width = image.shape[:2]
        
        # ROI: 하단 중앙 (차로 색깔 확인)
        roi_top = int(height * 0.7)
        roi_left = int(width * 0.3)
        roi_right = int(width * 0.7)
        roi = image[roi_top:height, roi_left:roi_right]
        
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # 색깔별 HSV 범위
        color_ranges = {
            'RED': ([0, 100, 100], [10, 255, 255], [170, 100, 100], [180, 255, 255]),
            'GREEN': ([40, 100, 100], [80, 255, 255]),
            'BLUE': ([100, 100, 100], [130, 255, 255])
        }
        
        # 각 색깔별 픽셀 수 계산
        color_pixels = {}
        
        for color, ranges in color_ranges.items():
            if len(ranges) == 4:  # RED (두 범위)
                mask1 = cv2.inRange(hsv, np.array(ranges[0]), np.array(ranges[1]))
                mask2 = cv2.inRange(hsv, np.array(ranges[2]), np.array(ranges[3]))
                mask = cv2.bitwise_or(mask1, mask2)
            else:  # GREEN, BLUE
                mask = cv2.inRange(hsv, np.array(ranges[0]), np.array(ranges[1]))
            
            color_pixels[color] = cv2.countNonZero(mask)
        
        # 가장 많이 검출된 색깔
        detected_color = max(color_pixels, key=color_pixels.get)
        
        # 충분한 픽셀이 있을 때만 유효
        if color_pixels[detected_color] < 500:
            detected_color = 'NONE'
        
        # 디버그 시각화
        if self.debug_mode:
            debug_image = image.copy()
            cv2.rectangle(debug_image, (roi_left, roi_top), (roi_right, height), (255, 255, 0), 2)
            
            # 색깔별 픽셀 수 표시
            y_offset = 30
            for color, pixels in color_pixels.items():
                color_bgr = {'RED': (0, 0, 255), 'GREEN': (0, 255, 0), 'BLUE': (255, 0, 0)}
                cv2.putText(debug_image, f'{color}: {pixels}', (10, y_offset),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_bgr[color], 2)
                y_offset += 25
            
            # 현재 속도 표시
            speed_text = f'Speed: {self.current_color}'
            cv2.putText(debug_image, speed_text, (10, height - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            
            try:
                debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                self.debug_image_pub.publish(debug_msg)
            except:
                pass
        
        return detected_color
    
    def track_lane(self, image):
        """차선 추적"""
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
        
        # 중심 계산
        M = cv2.moments(lane_mask)
        error = 0
        
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            image_center = width // 2
            error = cx - image_center
        
        return error
    
    def change_speed(self, color):
        """색깔에 따라 속도 변경"""
        speed_map = {
            'RED': self.slow_speed,
            'GREEN': self.normal_speed,
            'BLUE': self.fast_speed
        }
        
        speed_emoji = {
            'RED': '🐢',
            'GREEN': '🚗',
            'BLUE': '🚀'
        }
        
        rospy.loginfo(f'{speed_emoji[color]} {color} 차로 감지! 속도: {speed_map[color]:.2f}m/s')
    
    def control_vehicle(self, error):
        """차량 제어"""
        speed_map = {
            'RED': self.slow_speed,
            'GREEN': self.normal_speed,
            'BLUE': self.fast_speed
        }
        
        cmd = Twist()
        cmd.linear.x = speed_map.get(self.current_color, self.normal_speed)
        cmd.angular.z = -self.angular_gain * error
        self.cmd_vel_pub.publish(cmd)


def main():
    try:
        node = ColoredLaneMission()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass

if __name__ == '__main__':
    main()
