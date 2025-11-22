#!/usr/bin/env python
"""
Traffic Light Detector 노드
"""

import rospy
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np


class TrafficLightDetectorNode:
    def __init__(self):
        rospy.init_node('traffic_light_detector', anonymous=False)
        
        self.bridge = CvBridge()
        
        # Subscriber
        rospy.Subscriber('/usb_cam/image_raw/compressed', CompressedImage, 
                        self.image_callback, queue_size=1)
        
        # Publisher
        self.traffic_light_pub = rospy.Publisher('/detection/traffic_light', String, queue_size=1)
        
        rospy.loginfo('Traffic Light Detector 시작')
    
    def image_callback(self, msg):
        """신호등 검출"""
        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # 간단한 신호등 검출 (색상 기반)
            light_state = self.detect_traffic_light(cv_image)
            
            if light_state:
                self.traffic_light_pub.publish(String(data=light_state))
        except Exception as e:
            rospy.logwarn(f'Traffic light detection error: {e}')
    
    def detect_traffic_light(self, image):
        """색상 기반 신호등 검출"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 빨간불 검출
        red_mask = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))
        if cv2.countNonZero(red_mask) > 100:
            return 'red'
        
        # 초록불 검출
        green_mask = cv2.inRange(hsv, (40, 50, 50), (80, 255, 255))
        if cv2.countNonZero(green_mask) > 100:
            return 'green'
        
        return None
    
    def run(self):
        rospy.spin()


def main():
    try:
        node = TrafficLightDetectorNode()
        node.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
