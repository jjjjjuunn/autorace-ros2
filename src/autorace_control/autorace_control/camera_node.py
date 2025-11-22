#!/usr/bin/env python3
"""
실차용 카메라 노드
- 실제 USB 카메라 또는 CSI 카메라
- 캘리브레이션 적용
- 이미지 전처리
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np


class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')
        
        # 파라미터
        self.declare_parameter('device_id', 0)  # /dev/video0
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 30)
        self.declare_parameter('publish_compressed', False)
        self.declare_parameter('calibration_file', '')
        
        device_id = self.get_parameter('device_id').value
        width = self.get_parameter('width').value
        height = self.get_parameter('height').value
        fps = self.get_parameter('fps').value
        self.publish_compressed = self.get_parameter('publish_compressed').value
        calib_file = self.get_parameter('calibration_file').value
        
        # 카메라 초기화
        self.cap = cv2.VideoCapture(device_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        
        if not self.cap.isOpened():
            self.get_logger().error(f'카메라 {device_id} 열기 실패!')
            return
        
        # 캘리브레이션 로드
        self.camera_matrix = None
        self.dist_coeffs = None
        if calib_file:
            self.load_calibration(calib_file)
        
        self.bridge = CvBridge()
        
        # Publisher
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        
        if self.publish_compressed:
            self.compressed_pub = self.create_publisher(
                CompressedImage, '/camera/image_raw/compressed', 10)
        
        # 타이머로 이미지 캡처
        self.timer = self.create_timer(1.0 / fps, self.capture_and_publish)
        
        self.get_logger().info(f'카메라 노드 시작 (device={device_id}, {width}x{height}@{fps}fps)')
    
    def load_calibration(self, filename):
        """캘리브레이션 파일 로드"""
        try:
            import yaml
            with open(filename, 'r') as f:
                data = yaml.safe_load(f)
            
            self.camera_matrix = np.array(data['camera_matrix']['data']).reshape(3, 3)
            self.dist_coeffs = np.array(data['distortion_coefficients']['data'])
            self.get_logger().info('캘리브레이션 로드 성공')
        except Exception as e:
            self.get_logger().warn(f'캘리브레이션 로드 실패: {e}')
    
    def capture_and_publish(self):
        """이미지 캡처 및 발행"""
        ret, frame = self.cap.read()
        
        if not ret:
            self.get_logger().warn('프레임 읽기 실패')
            return
        
        # 왜곡 보정 (캘리브레이션 있을 경우)
        if self.camera_matrix is not None:
            frame = cv2.undistort(frame, self.camera_matrix, self.dist_coeffs)
        
        # 이미지 발행
        try:
            # Raw 이미지
            img_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            img_msg.header.stamp = self.get_clock().now().to_msg()
            img_msg.header.frame_id = 'camera_link'
            self.image_pub.publish(img_msg)
            
            # 압축 이미지 (선택)
            if self.publish_compressed:
                compressed_msg = CompressedImage()
                compressed_msg.header = img_msg.header
                compressed_msg.format = 'jpeg'
                compressed_msg.data = np.array(cv2.imencode('.jpg', frame)[1]).tobytes()
                self.compressed_pub.publish(compressed_msg)
                
        except Exception as e:
            self.get_logger().error(f'이미지 발행 실패: {e}')
    
    def destroy_node(self):
        """종료 시 카메라 해제"""
        if self.cap:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
