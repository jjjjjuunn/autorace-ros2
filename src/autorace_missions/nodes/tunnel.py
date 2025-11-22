#!/usr/bin/env python
"""
터널 미션
- 조명 변화(어두운 환경) 대응
- 터널 내부 차선 추적
- 터널 통과 완료 검출
"""

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class TunnelMission:
    def __init__(self):
        rospy.init_node('tunnel_mission', anonymous=False)
        
        # 파라미터
        
        self.debug_mode = rospy.get_param('~debug_mode', 0.1)
        self.tunnel_speed = rospy.get_param('~tunnel_speed', 0.1)
        self.angular_gain = rospy.get_param('~angular_gain', 0.1)
        self.brightness_threshold = rospy.get_param('~brightness_threshold', 0.1)
        
        # 상태
        self.mission_active = False
        self.in_tunnel = False
        self.tunnel_entry_count = 0
        self.tunnel_exit_count = 0
        self.detection_threshold = 10
        
        self.bridge = CvBridge()
        
        # Subscriber
        rospy.Subscriber('/mission/current', String, self.mission_callback, queue_size=10)
        rospy.Subscriber('/camera/image_raw', Image, self.image_callback, queue_size=10)
        
        # Publisher
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.mission_complete_pub = rospy.Publisher('/mission/complete', String, queue_size=10)
        self.debug_image_pub = rospy.Publisher('/vision/tunnel_debug', Image, queue_size=10)
        
        rospy.loginfo('터널 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 TUNNEL인지 확인"""
        if msg.data == 'TUNNEL':
            if not self.mission_active:
                rospy.loginfo('🚇 터널 미션 시작!')
                self.mission_active = True
                self.in_tunnel = False
                self.tunnel_entry_count = 0
                self.tunnel_exit_count = 0
        else:
            self.mission_active = False
    
    def image_callback(self, msg):
        """터널 진입/통과 검출 및 제어"""
        if not self.mission_active:
            return
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # 밝기 분석
            is_dark = self.check_darkness(cv_image)
            
            # 터널 진입/탈출 판단
            if is_dark:
                self.tunnel_entry_count += 1
                self.tunnel_exit_count = 0
            else:
                self.tunnel_exit_count += 1
                self.tunnel_entry_count = max(0, self.tunnel_entry_count - 1)
            
            # 터널 진입 확정
            if not self.in_tunnel and self.tunnel_entry_count >= self.detection_threshold:
                self.enter_tunnel()
            
            # 터널 탈출 확정
            if self.in_tunnel and self.tunnel_exit_count >= self.detection_threshold:
                self.exit_tunnel()
            
            # 터널 내부에서 차선 추적
            if self.in_tunnel:
                error = self.detect_lane_in_tunnel(cv_image)
                self.control_in_tunnel(error)
            
        except Exception as e:
            rospy.logerr(f'이미지 처리 실패: {str(e)}')
    
    def check_darkness(self, image):
        """이미지 밝기 체크 (터널 진입 판단)"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        
        # 디버그
        if self.debug_mode:
            debug_image = image.copy()
            color = (0, 0, 255) if avg_brightness < self.brightness_threshold else (0, 255, 0)
            cv2.putText(debug_image, f'Brightness: {int(avg_brightness)}', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(debug_image, f'Tunnel: {self.in_tunnel}', (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            try:
                debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                self.debug_image_pub.publish(debug_msg)
            except:
                pass
        
        return avg_brightness < self.brightness_threshold
    
    def detect_lane_in_tunnel(self, image):
        """터널 내부 차선 검출 (어두운 환경)"""
        height, width = image.shape[:2]
        roi_top = int(height * 0.6)
        roi = image[roi_top:height, 0:width]
        
        # CLAHE로 대비 향상 (어두운 환경 대응)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # 차선 검출
        blur = cv2.GaussianBlur(enhanced, (5, 5), 0)
        _, binary = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY)
        
        # 모폴로지
        kernel = np.ones((5, 5), np.uint8)
        lane_mask = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # 중심 계산
        M = cv2.moments(lane_mask)
        error = 0
        
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            image_center = width // 2
            error = cx - image_center
        
        return error
    
    def control_in_tunnel(self, error):
        """터널 내부 제어"""
        cmd = Twist()
        cmd.linear.x = self.tunnel_speed
        cmd.angular.z = -self.angular_gain * error
        self.cmd_vel_pub.publish(cmd)
    
    def enter_tunnel(self):
        """터널 진입"""
        rospy.loginfo('🚇 터널 진입!')
        self.in_tunnel = True
    
    def exit_tunnel(self):
        """터널 탈출 - 미션 완료"""
        rospy.loginfo('✅ 터널 통과 완료!')
        
        # 미션 완료
        complete_msg = String()
        complete_msg.data = 'TUNNEL'
        self.mission_complete_pub.publish(complete_msg)
        
        self.mission_active = False
        self.in_tunnel = False


def main():
    try:
    node = TunnelMission()
    
    try:
        node.run()
    except rospy.ROSInterruptException:
        pass
    finally:
        
        pass


if __name__ == '__main__':
    main()
