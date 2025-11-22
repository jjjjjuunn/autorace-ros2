#!/usr/bin/env python
"""
기본 차선 추적 노드 (테스트/백업용)

⚠️ 주의: 이 노드는 대회 미션에서 직접 사용되지 않습니다!
각 미션 노드(colored_lane, obstacle_avoidance 등)가 
자체적으로 차선 추적 기능을 포함하고 있습니다.

사용 목적:
1. 차선 추적 알고리즘 단독 테스트
2. 카메라 캘리브레이션 검증  
3. 기본 주행 로직 백업

대회 실행 시에는 full_autorace.launch.py를 사용하세요.
"""

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class LaneFollowingMission:
    def __init__(self):
        rospy.init_node('lane_following_mission', anonymous=False)
        
        # 파라미터
        
        self.linear_speed = rospy.get_param('~linear_speed', 0.1)
        self.angular_gain = rospy.get_param('~angular_gain', 0.1)
        self.debug_mode = rospy.get_param('~debug_mode', 0.1)
        
        # 상태
        self.mission_active = False
        
        self.bridge = CvBridge()
        
        # Subscriber
        rospy.Subscriber('/mission/current', String, self.mission_callback, queue_size=10)
        rospy.Subscriber('/camera/image_raw', Image, self.image_callback, queue_size=10)
        
        # Publisher
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.debug_image_pub = rospy.Publisher('/vision/lane_debug', Image, queue_size=10)
        
        rospy.loginfo('차선 추적 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 LANE_FOLLOWING인지 확인"""
        if msg.data == 'LANE_FOLLOWING':
            if not self.mission_active:
                rospy.loginfo('🛣️ 차선 추적 시작!')
                self.mission_active = True
        else:
            self.mission_active = False
    
    def image_callback(self, msg):
        """차선 검출 및 제어"""
        if not self.mission_active:
            return
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            error = self.detect_lane(cv_image)
            
            # 제어 명령 생성
            cmd = Twist()
            cmd.linear.x = self.linear_speed
            cmd.angular.z = -self.angular_gain * error
            self.cmd_vel_pub.publish(cmd)
            
        except Exception as e:
            rospy.logerr(f'이미지 처리 실패: {str(e)}')
    
    def detect_lane(self, image):
        """차선 검출 및 중심 오차 계산"""
        height, width = image.shape[:2]
        
        # ROI 설정
        roi_top = int(height * 0.6)
        roi = image[roi_top:height, 0:width]
        
        # 노란색/흰색 차선 검출
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # 흰색 마스크
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # 노란색 마스크
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([30, 255, 255])
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # 통합 마스크
        lane_mask = cv2.bitwise_or(white_mask, yellow_mask)
        
        # 모폴로지 연산
        kernel = np.ones((5, 5), np.uint8)
        lane_mask = cv2.morphologyEx(lane_mask, cv2.MORPH_CLOSE, kernel)
        
        # 모멘트로 중심 찾기
        M = cv2.moments(lane_mask)
        
        error = 0
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            
            # 중심 오차 계산 (픽셀 단위)
            image_center = width // 2
            error = cx - image_center
            
            # 디버그 시각화
            if self.debug_mode:
                debug_image = image.copy()
                cv2.circle(debug_image, (cx, roi_top + cy), 10, (0, 255, 0), -1)
                cv2.line(debug_image, (image_center, roi_top), 
                        (image_center, height), (255, 0, 0), 2)
                cv2.line(debug_image, (cx, roi_top), (cx, height), (0, 255, 0), 2)
                cv2.putText(debug_image, f'Error: {error}', (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                try:
                    debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                    self.debug_image_pub.publish(debug_msg)
                except:
                    pass
        
        return error


def main():
    try:
        node = LaneFollowingMission()
        node.run()
    except rospy.ROSInterruptException:
        pass

if __name__ == '__main__':
    main()
