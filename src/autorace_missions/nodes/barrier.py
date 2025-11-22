#!/usr/bin/env python
"""
미션 7: 차단기
- 차단기 감지
- 차단기가 올라갈 때까지 대기
- 올라가면 통과
"""

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class BarrierMission:
    def __init__(self):
        rospy.init_node('barrier_mission', anonymous=False)
        
        # 파라미터
        
        self.debug_mode = rospy.get_param('~debug_mode', 0.1)
        self.normal_speed = rospy.get_param('~normal_speed', 0.1)
        self.approach_speed = rospy.get_param('~approach_speed', 0.1)
        self.barrier_area_threshold = rospy.get_param('~barrier_area_threshold', 0.1)
        self.open_angle_threshold = rospy.get_param('~open_angle_threshold', 0.1)
        
        # 상태
        self.mission_active = False
        self.barrier_detected = False
        self.waiting_for_open = False
        self.barrier_open = False
        self.wait_count = 0
        
        self.bridge = CvBridge()
        
        # Subscriber
        rospy.Subscriber('/mission/current', String, self.mission_callback, queue_size=10)
        rospy.Subscriber('/camera/image_raw', Image, self.image_callback, queue_size=10)
        
        # Publisher
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.mission_complete_pub = rospy.Publisher('/mission/complete', String, queue_size=10)
        self.debug_image_pub = rospy.Publisher('/vision/barrier_debug', Image, queue_size=10)
        
        rospy.loginfo('차단기 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 BARRIER인지 확인"""
        if msg.data == 'BARRIER':
            if not self.mission_active:
                rospy.loginfo('🚧 차단기 미션 시작!')
                self.mission_active = True
                self.barrier_detected = False
                self.waiting_for_open = False
                self.barrier_open = False
                self.wait_count = 0
        else:
            if self.mission_active:
                complete_msg = String()
                complete_msg.data = 'BARRIER'
                self.mission_complete_pub.publish(complete_msg)
            self.mission_active = False
    
    def image_callback(self, msg):
        """차단기 검출 및 대기"""
        if not self.mission_active:
            return
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # 차단기 검출
            barrier_angle = self.detect_barrier(cv_image)
            
            if barrier_angle is not None:
                if not self.barrier_detected:
                    rospy.loginfo('🚧 차단기 감지!')
                    self.barrier_detected = True
                    self.waiting_for_open = True
                
                # 차단기 각도 확인
                if barrier_angle > self.open_angle_threshold:
                    if not self.barrier_open:
                        rospy.loginfo('✅ 차단기 열림! 통과합니다.')
                        self.barrier_open = True
                        self.wait_count = 0
                else:
                    if self.waiting_for_open:
                        self.wait_count += 1
                        if self.wait_count % 30 == 0:  # 1초마다 로그
                            rospy.loginfo(f'⏳ 차단기 대기 중... ({self.wait_count // 30}초)')
            
            # 차량 제어
            self.control_vehicle()
            
        except Exception as e:
            rospy.logerr(f'이미지 처리 실패: {str(e)}')
    
    def detect_barrier(self, image):
        """차단기 검출 및 각도 측정"""
        height, width = image.shape[:2]
        
        # ROI: 중앙 상단
        roi_top = int(height * 0.2)
        roi_bottom = int(height * 0.6)
        roi_left = int(width * 0.3)
        roi_right = int(width * 0.7)
        roi = image[roi_top:roi_bottom, roi_left:roi_right]
        
        # 빨간색/주황색 차단기 검출
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # 빨강 + 주황
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        
        lower_orange = np.array([10, 100, 100])
        upper_orange = np.array([20, 255, 255])
        mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)
        
        mask = cv2.bitwise_or(mask_red1, mask_red2)
        mask = cv2.bitwise_or(mask, mask_orange)
        
        # 노이즈 제거
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 윤곽선 검출
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        barrier_angle = None
        
        if contours:
            # 가장 큰 윤곽선
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if area > self.barrier_area_threshold:
                # 최소 영역 사각형으로 각도 계산
                rect = cv2.minAreaRect(largest_contour)
                angle = rect[2]
                
                # 각도 정규화 (0~90도)
                if angle < -45:
                    angle = 90 + angle
                
                barrier_angle = abs(angle)
                
                # 디버그 시각화
                if self.debug_mode:
                    debug_image = image.copy()
                    
                    # 바운딩 박스
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    # ROI 좌표로 변환
                    box[:, 0] += roi_left
                    box[:, 1] += roi_top
                    cv2.drawContours(debug_image, [box], 0, (0, 255, 0), 2)
                    
                    # 각도 및 상태 표시
                    status_text = f'Angle: {barrier_angle:.1f}°'
                    if barrier_angle > self.open_angle_threshold:
                        status_text += ' OPEN'
                        color = (0, 255, 0)
                    else:
                        status_text += ' CLOSED'
                        color = (0, 0, 255)
                    
                    cv2.putText(debug_image, status_text, (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    
                    if self.waiting_for_open:
                        cv2.putText(debug_image, f'Waiting: {self.wait_count // 30}s',
                                  (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                    
                    try:
                        debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                        self.debug_image_pub.publish(debug_msg)
                    except:
                        pass
        
        return barrier_angle
    
    def control_vehicle(self):
        """차량 제어"""
        cmd = Twist()
        
        if not self.barrier_detected:
            # 차단기 접근
            cmd.linear.x = self.approach_speed
            cmd.angular.z = 0.0
        elif self.waiting_for_open and not self.barrier_open:
            # 차단기 대기 - 정지
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
        elif self.barrier_open:
            # 차단기 통과
            cmd.linear.x = self.normal_speed
            cmd.angular.z = 0.0
            
            # 통과 후 미션 완료
            if self.wait_count > 60:  # 2초 후
                self.complete_mission()
        
        self.cmd_vel_pub.publish(cmd)
    
    def complete_mission(self):
        """미션 완료"""
        rospy.loginfo('✅ 차단기 통과 완료!')
        
        complete_msg = String()
        complete_msg.data = 'BARRIER'
        self.mission_complete_pub.publish(complete_msg)
        
        self.mission_active = False


def main():
    try:
    node = BarrierMission()
    
    try:
        node.run()
    except rospy.ROSInterruptException:
        pass
    finally:
        
        pass


if __name__ == '__main__':
    main()
