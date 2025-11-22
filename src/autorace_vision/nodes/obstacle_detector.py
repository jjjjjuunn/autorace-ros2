#!/usr/bin/env python
"""
Obstacle Detector 노드
"""

import rospy
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Bool
from cv_bridge import CvBridge
import cv2
import numpy as np


class ObstacleDetectorNode:
    def __init__(self):
        rospy.init_node('obstacle_detector', anonymous=False)
        
        self.bridge = CvBridge()
        
        # Subscriber
        rospy.Subscriber('/usb_cam/image_raw/compressed', CompressedImage, 
                        self.image_callback, queue_size=1)
        
        # Publisher
        self.obstacle_pub = rospy.Publisher('/detection/obstacle', Bool, queue_size=1)
        
        rospy.loginfo('Obstacle Detector 시작')
    
    def image_callback(self, msg):
        """장애물 검출"""
        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # 장애물 검출
            detected = self.detect_obstacle(cv_image)
            
            self.obstacle_pub.publish(Bool(data=detected))
        except Exception as e:
            rospy.logwarn(f'Obstacle detection error: {e}')
    
    def detect_obstacle(self, image):
        """장애물 검출 (간단한 색상 기반)"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 장애물 색상 범위 (예: 빨간색)
        obstacle_mask = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))
        
        # 일정 면적 이상이면 장애물
        contours, _ = cv2.findContours(obstacle_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # 최소 면적
                return True
        
        return False
    
    def run(self):
        rospy.spin()


def main():
    try:
        node = ObstacleDetectorNode()
        node.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
