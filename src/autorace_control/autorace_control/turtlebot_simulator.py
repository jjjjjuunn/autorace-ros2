#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from tf2_ros import TransformBroadcaster
import math

class TurtleBotSimulator(Node):
    def __init__(self):
        super().__init__('turtlebot_simulator')
        
        # Subscribers
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        
        # Publishers
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)
        
        # TF Broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # 초기 위치 - 실제 도로 시작점!
        self.x = -1.762
        self.y = -2.613
        self.theta = -0.02  # orientation.z * 2 (약 -1.2도)
        
        # 속도
        self.linear_vel = 0.0
        self.angular_vel = 0.0
        
        # 타이머 (10Hz)
        self.timer = self.create_timer(0.1, self.update_state)
        
        self.get_logger().info('TurtleBot Simulator Started')
        self.get_logger().info(f'Initial position: x={self.x:.3f}, y={self.y:.3f}, theta={self.theta:.3f}')
        self.get_logger().info('🚗 Ready on the road!')
    
    def cmd_vel_callback(self, msg):
        self.linear_vel = msg.linear.x
        self.angular_vel = msg.angular.z
    
    def update_state(self):
        dt = 0.1  # 10Hz
        
        # 오도메트리 업데이트
        self.x += self.linear_vel * math.cos(self.theta) * dt
        self.y += self.linear_vel * math.sin(self.theta) * dt
        self.theta += self.angular_vel * dt
        
        # theta 정규화
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
        
        # Odometry 발행
        self.publish_odometry()
        
        # LaserScan 발행
        self.publish_scan()
    
    def publish_odometry(self):
        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        
        # Position
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.03
        
        # Orientation (quaternion)
        odom.pose.pose.orientation.x = 0.0
        odom.pose.pose.orientation.y = 0.0
        odom.pose.pose.orientation.z = math.sin(self.theta / 2)
        odom.pose.pose.orientation.w = math.cos(self.theta / 2)
        
        # Velocity
        odom.twist.twist.linear.x = self.linear_vel
        odom.twist.twist.angular.z = self.angular_vel
        
        self.odom_pub.publish(odom)
        
        # TF 발행
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.03
        t.transform.rotation = odom.pose.pose.orientation
        
        self.tf_broadcaster.sendTransform(t)
    
    def publish_scan(self):
        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = 'base_scan'
        scan.angle_min = -math.pi
        scan.angle_max = math.pi
        scan.angle_increment = math.pi / 180
        scan.time_increment = 0.0
        scan.scan_time = 0.1
        scan.range_min = 0.12
        scan.range_max = 3.5
        scan.ranges = [3.5] * 360
        
        self.scan_pub.publish(scan)

def main(args=None):
    rclpy.init(args=args)
    node = TurtleBotSimulator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()