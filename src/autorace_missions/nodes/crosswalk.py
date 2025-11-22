#!/usr/bin/env python
"""
횡단보도 미션
- 횡단보도 검출 시 서행
- 통과 후 정상 속도 복귀
"""

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class CrosswalkMission:
    def __init__(self):
        rospy.init_node('crosswalk_mission', anonymous=False)
        
        # 파라미터
        
        self.slow_speed = rospy.get_param('~slow_speed', 0.1)
        self.normal_speed = rospy.get_param('~normal_speed', 0.1)
        self.debug_mode = rospy.get_param('~debug_mode', 0.1)
        self.stripe_threshold = rospy.get_param('~stripe_threshold', 0.1)
        
        # 상태
        self.mission_active = False
        self.crosswalk_detected = False
        self.is_crossing = False
        self.detection_count = 0
        self.detection_confirm_threshold = 3
        self.no_detection_count = 0
        
        self.bridge = CvBridge()
        
        # Subscriber
        rospy.Subscriber('/mission/current', String, self.mission_callback, queue_size=10)
        rospy.Subscriber('/camera/image_raw', Image, self.image_callback, queue_size=10)
        
        # Publisher
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.mission_complete_pub = rospy.Publisher('/mission/complete', String, queue_size=10)
        self.debug_image_pub = rospy.Publisher('/vision/crosswalk_debug', Image, queue_size=10)
        
        rospy.loginfo('횡단보도 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 CROSSWALK인지 확인"""
        if msg.data == 'CROSSWALK':
            if not self.mission_active:
                rospy.loginfo('🚶 횡단보도 미션 시작!')
                self.mission_active = True
                self.detection_count = 0
                self.no_detection_count = 0
        else:
            self.mission_active = False
    
    def image_callback(self, msg):
        """횡단보도 검출"""
        if not self.mission_active:
            return
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            detected = self.detect_crosswalk(cv_image)
            
            # 검출 확정
            if detected:
                self.detection_count += 1
                self.no_detection_count = 0
            else:
                self.detection_count = max(0, self.detection_count - 1)
                if self.is_crossing:
                    self.no_detection_count += 1
            
            confirmed = self.detection_count >= self.detection_confirm_threshold
            
            # 횡단보도 진입 (정지)
            if confirmed and not self.is_crossing:
                self.enter_crosswalk()
                
        except Exception as e:
            rospy.logerr(f'이미지 처리 실패: {str(e)}')
    
    def detect_crosswalk(self, image):
        """횡단보도 검출 알고리즘"""
        height, width = image.shape[:2]
        roi_top = int(height * 0.5)
        roi_bottom = int(height * 0.9)
        roi = image[roi_top:roi_bottom, 0:width]
        
        # 전처리
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 엣지 검출
        edges = cv2.Canny(blur, 50, 150)
        
        # Hough 라인 검출
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, 
                               minLineLength=30, maxLineGap=10)
        
        detected = False
        debug_image = image.copy()
        
        if lines is not None:
            horizontal_lines = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                
                # 수평선 필터링
                if angle < 15 or angle > 165:
                    horizontal_lines.append(line)
                    if self.debug_mode:
                        cv2.line(debug_image, (x1, roi_top + y1), 
                               (x2, roi_top + y2), (0, 255, 255), 2)
            
            # 횡단보도 판단
            if len(horizontal_lines) >= self.stripe_threshold:
                detected = True
                if self.debug_mode:
                    cv2.putText(debug_image, 'CROSSWALK', (10, 50),
                              cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
        
        # 디버그 이미지
        if self.debug_mode:
            cv2.rectangle(debug_image, (0, roi_top), (width, roi_bottom), (255, 0, 0), 2)
            try:
                debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                self.debug_image_pub.publish(debug_msg)
            except:
                pass
        
        return detected
    
    def enter_crosswalk(self):
        """횡단보도 진입 - 정지"""
        rospy.loginfo('🚶 횡단보도 감지! 정지합니다.')
        self.is_crossing = True
        
        # 정지 명령
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(cmd)
        
        # 3초 후 출발
        self.create_timer(3.0, self.resume_after_crosswalk, one_shot=True)
    
    def resume_after_crosswalk(self):
        """횡단보도 정지 후 재출발"""
        rospy.loginfo('✅ 횡단보도 통과! 재출발합니다.')
        
        # 정상 속도 복귀
        cmd = Twist()
        cmd.linear.x = self.normal_speed
        cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(cmd)
        
        # 미션 완료
        complete_msg = String()
        complete_msg.data = 'CROSSWALK'
        self.mission_complete_pub.publish(complete_msg)
        
        # 상태 초기화
        self.mission_active = False
        self.is_crossing = False
        self.detection_count = 0
        self.no_detection_count = 0
    



def main():
    try:
        node = CrosswalkMission()
        node.run()
    except rospy.ROSInterruptException:
        pass

if __name__ == '__main__':
    main()
