#!/usr/bin/env python
"""
Lane Detector 노드
"""

import rospy
from sensor_msgs.msg import CompressedImage
from geometry_msgs.msg import Point
from autorace_vision.line_detector import LineDetector
from cv_bridge import CvBridge
import cv2
import numpy as np


class LaneDetectorNode:
    def __init__(self):
        rospy.init_node('lane_detector', anonymous=False)
        
        self.bridge = CvBridge()
        self.detector = LineDetector()
        
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
            
            # 차선 검출
            lane_center = self.detector.detect_lane(cv_image)
            
            # 발행
            if lane_center is not None:
                point_msg = Point()
                point_msg.x = lane_center[0]
                point_msg.y = lane_center[1]
                point_msg.z = 0.0
                self.lane_pub.publish(point_msg)
        except Exception as e:
            rospy.logwarn(f'Lane detection error: {e}')
    
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
