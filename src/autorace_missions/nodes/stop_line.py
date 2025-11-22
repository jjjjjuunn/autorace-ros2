#!/usr/bin/env python
"""
정지선 미션
- 정지선 검출 시 정지
- 3초 대기
- 출발
"""

import rospy
from std_msgs.msg import Bool, String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class StopLineMission:
    def __init__(self):
        rospy.init_node('stop_line_mission', anonymous=False)
        
        # 파라미터
        
        self.stop_duration = rospy.get_param('~stop_duration', 0.1)
        self.debug_mode = rospy.get_param('~debug_mode', 0.1)
        self.detection_threshold = rospy.get_param('~detection_threshold', 0.1)
        
        # 상태
        self.mission_active = False
        self.stop_line_detected = False
        self.is_stopped = False
        self.stop_timer = None
        self.detection_count = 0
        self.detection_confirm_threshold = 3
        
        self.bridge = CvBridge()
        
        # Subscriber
        rospy.Subscriber('/mission/current', String, self.mission_callback, queue_size=10)
        rospy.Subscriber('/camera/image_raw', Image, self.image_callback, queue_size=10)
        
        # Publisher
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.mission_complete_pub = rospy.Publisher('/mission/complete', String, queue_size=10)
        self.debug_image_pub = rospy.Publisher('/vision/stop_line_debug', Image, queue_size=10)
        
        rospy.loginfo('정지선 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 STOP_LINE인지 확인"""
        if msg.data == 'STOP_LINE':
            if not self.mission_active:
                rospy.loginfo('🛑 정지선 미션 시작!')
                self.mission_active = True
                self.detection_count = 0
        else:
            self.mission_active = False
    
    def image_callback(self, msg):
        """정지선 검출"""
        if not self.mission_active or self.is_stopped:
            return
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            detected = self.detect_stop_line(cv_image)
            
            # 검출 확정 (노이즈 방지)
            if detected:
                self.detection_count += 1
            else:
                self.detection_count = max(0, self.detection_count - 1)
            
            confirmed = self.detection_count >= self.detection_confirm_threshold
            
            if confirmed and not self.is_stopped:
                self.execute_stop_behavior()
        except Exception as e:
            rospy.logerr(f'이미지 처리 실패: {str(e)}')
    
    def detect_stop_line(self, image):
        """정지선 검출 알고리즘"""
        height, width = image.shape[:2]
        roi_top = int(height * 0.7)
        roi = image[roi_top:height, 0:width]
        
        # 전처리
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 흰색 영역 추출
        _, binary = cv2.threshold(blur, 200, 255, cv2.THRESH_BINARY)
        
        # 모폴로지 연산
        kernel = np.ones((5, 5), np.uint8)
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
        
        # 윤곽선 검출
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected = False
        debug_image = image.copy()
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h) if h > 0 else 0
            area = cv2.contourArea(contour)
            
            # 정지선 조건: 가로로 긴 사각형
            if aspect_ratio > 5.0 and area > 1000:
                detected = True
                if self.debug_mode:
                    cv2.rectangle(debug_image, (x, roi_top + y), 
                                (x + w, roi_top + y + h), (0, 255, 0), 3)
                    cv2.putText(debug_image, 'STOP LINE', (x, roi_top + y - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 디버그 이미지 발행
        if self.debug_mode:
            cv2.line(debug_image, (0, roi_top), (width, roi_top), (255, 0, 0), 2)
            try:
                debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                self.debug_image_pub.publish(debug_msg)
            except:
                pass
        
        return detected
    
    def execute_stop_behavior(self):
        """정지 → 대기 → 출발"""
        rospy.loginfo('🛑 정지선 검출! 정차합니다.')
        self.is_stopped = True
        
        # 정지
        stop_cmd = Twist()
        stop_cmd.linear.x = 0.0
        stop_cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(stop_cmd)
        
        # 지정 시간 후 재출발
        self.stop_timer = rospy.Timer(rospy.Duration(self.stop_duration), self.resume_driving)
    
    def resume_driving(self):
        """재출발 및 미션 완료"""
        rospy.loginfo('✅ 재출발!')
        
        # 타이머 해제
        if self.stop_timer:
            self.stop_timer.cancel()
            self.stop_timer = None
        
        # 미션 완료 신호
        complete_msg = String()
        complete_msg.data = 'STOP_LINE'
        self.mission_complete_pub.publish(complete_msg)
        
        # 상태 초기화
        self.mission_active = False
        self.is_stopped = False
        self.detection_count = 0


def main():
    try:
        node = StopLineMission()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass

if __name__ == '__main__':
    main()
