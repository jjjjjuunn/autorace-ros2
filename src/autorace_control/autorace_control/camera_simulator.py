#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
import numpy as np
import math

class CameraSimulator(Node):
    def __init__(self):
        super().__init__('camera_simulator')
        
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10)
        
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.timer = self.create_timer(0.1, self.publish_image)
        
        # 터틀봇 위치
        self.robot_x = -1.762
        self.robot_y = -2.613
        self.robot_theta = 0.0
        
        # 도로 파라미터
        self.road_center_x = -1.8  # 도로 중심 X 좌표
        self.road_width = 1.2      # 도로 폭 (양쪽 0.6m씩)
        
        self.get_logger().info('Camera Simulator - Real-time position-based rendering')
    
    def odom_callback(self, msg):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.robot_theta = math.atan2(siny_cosp, cosy_cosp)
    
    def publish_image(self):
        height, width = 480, 640
        
        # 배경
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:, :] = [40, 40, 40]
        
        # 로봇이 도로 중심에서 얼마나 벗어났는지
        offset_x = self.robot_x - self.road_center_x
        
        # 중요: 로봇이 오른쪽(+X)으로 벗어나면 차선이 왼쪽으로 보여야 함
        # 픽셀 스케일: 1m = 400 pixels
        pixel_per_meter = 400
        
        img_center = width // 2
        
        # 왼쪽 차선: 도로 중심에서 -0.6m
        left_world = self.road_center_x - 0.6
        left_offset_m = left_world - self.robot_x  # 로봇 기준 상대 위치
        left_offset_px = left_offset_m * pixel_per_meter
        
        # 오른쪽 차선: 도로 중심에서 +0.6m
        right_world = self.road_center_x + 0.6
        right_offset_m = right_world - self.robot_x
        right_offset_px = right_offset_m * pixel_per_meter
        
        # 회전 보정
        angle_effect = self.robot_theta * 100
        
        # 차선 그리기
        for y in range(height):
            depth = 1.0 - (y / height)  # 위쪽이 멀리
            perspective = 1.0 + (y / height) * 1.5
            
            # 왼쪽 차선
            left_x = int(img_center + left_offset_px + angle_effect * depth)
            if 0 < left_x < width:
                thickness = int(15 * perspective)
                for dx in range(-thickness, thickness):
                    px = left_x + dx
                    if 0 <= px < width:
                        img[y, px] = [255, 255, 255]
            
            # 오른쪽 차선
            right_x = int(img_center + right_offset_px + angle_effect * depth)
            if 0 < right_x < width:
                thickness = int(15 * perspective)
                for dx in range(-thickness, thickness):
                    px = right_x + dx
                    if 0 <= px < width:
                        img[y, px] = [255, 255, 255]
        
        # 디버깅 로그
        left_px = int(img_center + left_offset_px)
        right_px = int(img_center + right_offset_px)
        
        self.get_logger().info(
            f'Camera: Robot_x={self.robot_x:.2f}, Offset={offset_x:.2f}m, Lanes: L={left_px}, R={right_px}',
            throttle_duration_sec=1.0
        )
        
        # ROS Image
        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_link'
        msg.height = height
        msg.width = width
        msg.encoding = 'bgr8'
        msg.is_bigendian = 0
        msg.step = width * 3
        msg.data = img.tobytes()
        
        self.image_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = CameraSimulator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()