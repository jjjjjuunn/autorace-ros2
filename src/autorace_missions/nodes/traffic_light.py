#!/usr/bin/env python
"""
신호등 미션
- 빨간불: 정지
- 초록불: 출발
"""

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class TrafficLightMission:
    def __init__(self):
        rospy.init_node('traffic_light_mission', anonymous=False)
        
        # 파라미터
        self.debug_mode = rospy.get_param('~debug_mode', 0.1)
        
        # 상태
        self.mission_active = False
        self.current_light = 'UNKNOWN'  # RED, GREEN, UNKNOWN
        self.light_detection_count = {'RED': 0, 'GREEN': 0}
        self.detection_confirm_threshold = 5
        
        self.bridge = CvBridge()
        
        # Subscriber
        rospy.Subscriber('/mission/current', String, self.mission_callback, queue_size=10)
        rospy.Subscriber('/camera/image_raw', Image, self.image_callback, queue_size=10)
        
        # Publisher
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.mission_complete_pub = rospy.Publisher('/mission/complete', String, queue_size=10)
        self.debug_image_pub = rospy.Publisher('/vision/traffic_light_debug', Image, queue_size=10)
        
        rospy.loginfo('신호등 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 TRAFFIC_LIGHT인지 확인"""
        if msg.data == 'TRAFFIC_LIGHT':
            if not self.mission_active:
                rospy.loginfo('🚦 신호등 미션 시작!')
                self.mission_active = True
                self.current_light = 'UNKNOWN'
                self.light_detection_count = {'RED': 0, 'GREEN': 0}
        else:
            self.mission_active = False
    
    def image_callback(self, msg):
        """신호등 검출"""
        if not self.mission_active:
            return
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            detected_light = self.detect_traffic_light(cv_image)
            
            # 검출 카운트 업데이트
            if detected_light in ['RED', 'GREEN']:
                self.light_detection_count[detected_light] += 1
                # 다른 색상 카운트 감소
                for light in self.light_detection_count:
                    if light != detected_light:
                        self.light_detection_count[light] = max(0, self.light_detection_count[light] - 1)
            
            # 확정된 신호 판단
            for light, count in self.light_detection_count.items():
                if count >= self.detection_confirm_threshold:
                    if self.current_light != light:
                        self.handle_traffic_light(light)
                        self.current_light = light
            
        except Exception as e:
            rospy.logerr(f'이미지 처리 실패: {str(e)}')
    
    def detect_traffic_light(self, image):
        """신호등 색상 검출"""
        height, width = image.shape[:2]
        
        # ROI: 상단 중앙
        roi_top = int(height * 0.1)
        roi_bottom = int(height * 0.5)
        roi_left = int(width * 0.3)
        roi_right = int(width * 0.7)
        roi = image[roi_top:roi_bottom, roi_left:roi_right]
        
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # 빨간색 검출 (HSV에서 빨간색은 두 범위)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        
        # 초록색 검출
        lower_green = np.array([40, 100, 100])
        upper_green = np.array([80, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # 각 색상 픽셀 수 계산
        red_pixels = cv2.countNonZero(red_mask)
        green_pixels = cv2.countNonZero(green_mask)
        
        detected_light = 'UNKNOWN'
        
        if red_pixels > 100:
            detected_light = 'RED'
        elif green_pixels > 100:
            detected_light = 'GREEN'
        
        # 디버그 시각화
        if self.debug_mode:
            debug_image = image.copy()
            cv2.rectangle(debug_image, (roi_left, roi_top), 
                         (roi_right, roi_bottom), (255, 255, 0), 2)
            
            color = (0, 0, 255) if detected_light == 'RED' else \
                    (0, 255, 0) if detected_light == 'GREEN' else (128, 128, 128)
            
            cv2.putText(debug_image, f'{detected_light}', (10, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
            
            try:
                debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                self.debug_image_pub.publish(debug_msg)
            except:
                pass
        
        return detected_light
    
    def handle_traffic_light(self, light):
        """신호에 따른 동작"""
        cmd = Twist()
        
        if light == 'RED':
            rospy.loginfo('🔴 빨간불! 정지합니다.')
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            self.cmd_vel_pub.publish(cmd)
        
        elif light == 'GREEN':
            rospy.loginfo('🟢 초록불! 출발합니다.')
            cmd.linear.x = 0.15
            cmd.angular.z = 0.0
            self.cmd_vel_pub.publish(cmd)
            
            # 미션 완료
            complete_msg = String()
            complete_msg.data = 'TRAFFIC_LIGHT'
            self.mission_complete_pub.publish(complete_msg)
            
            self.mission_active = False


def main():
    try:
    node = TrafficLightMission()
    
    try:
        node.run()
    except rospy.ROSInterruptException:
        pass
    finally:
        
        pass


if __name__ == '__main__':
    main()
