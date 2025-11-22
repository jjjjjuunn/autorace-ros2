#!/usr/bin/env python
"""
Crosswalk Detector 노드
"""

import rospy
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Bool
from cv_bridge import CvBridge
import cv2
import numpy as np


class CrosswalkDetectorNode:
    def __init__(self):
        rospy.init_node('crosswalk_detector', anonymous=False)
        
        self.bridge = CvBridge()
        
        # Subscriber
        rospy.Subscriber('/usb_cam/image_raw/compressed', CompressedImage, 
                        self.image_callback, queue_size=1)
        
        # Publisher
        self.crosswalk_pub = rospy.Publisher('/detection/crosswalk', Bool, queue_size=1)
        
        rospy.loginfo('Crosswalk Detector 시작')
    
    def image_callback(self, msg):
        """횡단보도 검출"""
        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # 횡단보도 검출
            detected = self.detect_crosswalk(cv_image)
            
            self.crosswalk_pub.publish(Bool(data=detected))
        except Exception as e:
            rospy.logwarn(f'Crosswalk detection error: {e}')
    
    def detect_crosswalk(self, image):
        """횡단보도 검출 (흰색 줄무늬)"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # 횡단보도 패턴 검출
        white_pixels = cv2.countNonZero(thresh)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        
        # 흰색 비율이 높으면 횡단보도
        return (white_pixels / total_pixels) > 0.3
    
    def run(self):
        rospy.spin()


def main():
    try:
        node = CrosswalkDetectorNode()
        node.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
