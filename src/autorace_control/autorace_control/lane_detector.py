#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan

class LaneDetector(Node):
    def __init__(self):
        super().__init__('lane_detector')
        
        # LiDAR 구독
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)
        
        # 제어 명령 발행
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.get_logger().info('Lane Detector Node Started')
    
    def scan_callback(self, msg):
        """LiDAR 데이터 처리"""
        # 임시 구현: 앞으로만 계속 전진
        cmd = Twist()
        cmd.linear.x = 0.2  # 0.2 m/s
        cmd.angular.z = 0.0
        
        self.cmd_vel_pub.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = LaneDetector()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
