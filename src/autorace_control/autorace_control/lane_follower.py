#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
import numpy as np

class LaneFollower(Node):
    def __init__(self):
        super().__init__('lane_follower')
        
        self.subscription = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.debug_image_pub = self.create_publisher(Image, '/lane_debug', 10)
        
        self.prev_error = 0
        self.integral = 0
        self.no_lane_counter = 0
        
        self.get_logger().info('Lane Follower Started - Enhanced debugging')
    
    def image_callback(self, msg):
        img_array = np.frombuffer(msg.data, dtype=np.uint8)
        cv_image = img_array.reshape((msg.height, msg.width, 3))
        
        lane_center, debug_img = self.detect_lane(cv_image.copy())
        
        # 디버깅 이미지 발행
        debug_msg = Image()
        debug_msg.header.stamp = self.get_clock().now().to_msg()
        debug_msg.header.frame_id = 'camera_link'
        debug_msg.height = debug_img.shape[0]
        debug_msg.width = debug_img.shape[1]
        debug_msg.encoding = 'bgr8'
        debug_msg.is_bigendian = 0
        debug_msg.step = debug_img.shape[1] * 3
        debug_msg.data = debug_img.tobytes()
        self.debug_image_pub.publish(debug_msg)
        
        self.control_robot(lane_center, cv_image.shape[1])
    
    def detect_lane(self, image):
        gray = np.dot(image[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
        
        height, width = gray.shape
        
        # ROI - 하단 1/2
        roi_start = int(height * 0.5)
        roi = gray[roi_start:height, :]
        
        # 이진화
        binary = (roi > 150).astype(np.uint8) * 255
        
        # 디버깅 이미지
        debug_img = image.copy()
        
        # ROI 경계선 (빨간 수평선)
        debug_img[roi_start, :] = [0, 0, 255]
        
        # 이미지 중앙 (흰 세로선)
        img_center = width // 2
        debug_img[:, img_center] = [255, 255, 255]
        
        white_pixels = np.where(binary > 0)
        
        self.get_logger().info(f'White pixels detected: {len(white_pixels[1])}', throttle_duration_sec=0.5)
        
        if len(white_pixels[1]) > 50:
            self.no_lane_counter = 0
            
            x_coords = white_pixels[1]
            y_coords = white_pixels[0] + roi_start
            
            # 감지된 픽셀 표시 (초록 점)
            for i in range(0, len(x_coords), 5):
                x, y = x_coords[i], y_coords[i]
                if 0 <= x < width and 0 <= y < height:
                    debug_img[y, x] = [0, 255, 0]
            
            mid = width // 2
            left_half = x_coords[x_coords < mid]
            right_half = x_coords[x_coords >= mid]
            
            lane_center = width // 2  # 기본값
            
            if len(left_half) > 20 and len(right_half) > 20:
                # 양쪽 차선 모두
                left_lane = int(np.mean(left_half))
                right_lane = int(np.mean(right_half))
                lane_center = (left_lane + right_lane) // 2
                
                # 왼쪽 차선 (파란 세로선)
                debug_img[:, left_lane] = [255, 0, 0]
                
                # 오른쪽 차선 (파란 세로선)
                debug_img[:, right_lane] = [255, 0, 0]
                
                # 목표 중앙 (노란 세로선)
                debug_img[:, lane_center] = [0, 255, 255]
                
                self.get_logger().info(
                    f'✓ Both lanes: L={left_lane}, R={right_lane}, Center={lane_center}, Error={lane_center - img_center}'
                )
                
            elif len(left_half) > 20:
                # 왼쪽만
                left_lane = int(np.mean(left_half))
                lane_center = left_lane + 150
                
                debug_img[:, left_lane] = [255, 0, 0]
                debug_img[:, lane_center] = [0, 255, 255]
                
                self.get_logger().info(
                    f'← Left only: Lane={left_lane}, Target={lane_center}, Error={lane_center - img_center}'
                )
                
            elif len(right_half) > 20:
                # 오른쪽만
                right_lane = int(np.mean(right_half))
                lane_center = right_lane - 150
                
                debug_img[:, right_lane] = [255, 0, 0]
                debug_img[:, lane_center] = [0, 255, 255]
                
                self.get_logger().info(
                    f'→ Right only: Lane={right_lane}, Target={lane_center}, Error={lane_center - img_center}'
                )
            
            return lane_center, debug_img
        else:
            self.no_lane_counter += 1
            self.get_logger().warn(f'✗ No lane detected! ({self.no_lane_counter})')
            return width // 2, debug_img
    
    def control_robot(self, lane_center, image_width):
        cmd = Twist()
        
        image_center = image_width // 2
        error = lane_center - image_center
        
        # PID 게인 대폭 증가
        Kp = 0.015  # 1.5배 증가
        Ki = 0.0003
        Kd = 0.008  # 1.6배 증가
        
        self.integral += error
        self.integral = max(-200, min(200, self.integral))
        
        derivative = error - self.prev_error
        
        angular_z = -(Kp * error + Ki * self.integral + Kd * derivative)
        
        # 회전 속도 제한
        angular_z = max(-1.0, min(1.0, angular_z))
        
        if self.no_lane_counter > 10:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            self.get_logger().error('🛑 Lost lane! STOPPING.')
        else:
            cmd.linear.x = 0.12  # 속도 약간 줄임 (안정성)
            cmd.angular.z = angular_z
            
            self.get_logger().info(
                f'🚗 Control: Error={error:4d}, Angular={angular_z:+.3f}, Speed={cmd.linear.x:.2f}',
                throttle_duration_sec=0.3
            )
        
        self.cmd_vel_pub.publish(cmd)
        self.prev_error = error

def main(args=None):
    rclpy.init(args=args)
    node = LaneFollower()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()