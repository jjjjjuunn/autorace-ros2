#!/usr/bin/env python
"""
Lane Detector 노드 - 간단한 차선 검출
"""

import rospy
from sensor_msgs.msg import CompressedImage
from geometry_msgs.msg import Point
from cv_bridge import CvBridge
import cv2
import numpy as np


class LaneDetectorNode:
    def __init__(self):
        rospy.init_node('lane_detector', anonymous=False)
        
        self.bridge = CvBridge()
        
        # Subscriber
        rospy.Subscriber('/usb_cam/image_raw/compressed', CompressedImage, 
                        self.image_callback, queue_size=1)
        
        # Publisher
        self.lane_pub = rospy.Publisher('/detection/lane', Point, queue_size=1)
        
        rospy.loginfo('Lane Detector 시작')
    
    def image_callback(self, msg):
        """이미지 처리"""
        try:
            # Compressed image → CV image
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # 간단한 차선 검출 (Canny edge + Hough lines)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # 이미지 하단 ROI
            height, width = edges.shape
            roi = edges[int(height*0.6):, :]
            
            # 차선 중심 계산 (간단히 중앙으로)
            point_msg = Point()
            point_msg.x = width / 2.0
            point_msg.y = height * 0.8
            point_msg.z = 0.0
            self.lane_pub.publish(point_msg)
        except Exception as e:
            rospy.logwarn('Lane detection error: {}'.format(e))
    
    def run(self):
        rospy.spin()


def main():
    import numpy as np
    try:
        node = LaneDetectorNode()
        node.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
