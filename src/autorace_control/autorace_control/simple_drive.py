#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class SimpleDrive(Node):
    def __init__(self):
        super().__init__('simple_drive')
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.publish_cmd_vel)
        self.get_logger().info('Simple Drive Started - Moving forward at 0.2 m/s')
    
    def publish_cmd_vel(self):
        msg = Twist()
        msg.linear.x = 0.2  # 직진 0.2m/s
        msg.angular.z = 0.0  # 회전 없음
        self.cmd_vel_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = SimpleDrive()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()