#!/usr/bin/env python3
"""
실차용 모터 제어 노드
- 실제 하드웨어 모터 제어
- PWM 신호 변환
- 안전 제한 적용
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32


class MotorController(Node):
    def __init__(self):
        super().__init__('motor_controller')
        
        # 파라미터
        self.declare_parameter('max_linear_speed', 0.3)
        self.declare_parameter('max_angular_speed', 1.0)
        self.declare_parameter('wheel_base', 0.16)  # 차축 간격 (m)
        self.declare_parameter('wheel_radius', 0.033)  # 바퀴 반지름 (m)
        
        self.max_linear = self.get_parameter('max_linear_speed').value
        self.max_angular = self.get_parameter('max_angular_speed').value
        self.wheel_base = self.get_parameter('wheel_base').value
        self.wheel_radius = self.get_parameter('wheel_radius').value
        
        # Subscriber: cmd_vel 수신
        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        
        # Publisher: 실제 모터 명령 (예: PWM)
        self.left_motor_pub = self.create_publisher(Float32, '/motor/left', 10)
        self.right_motor_pub = self.create_publisher(Float32, '/motor/right', 10)
        
        # 또는 하드웨어 드라이버가 제공하는 토픽 사용
        # self.motor_pub = self.create_publisher(MotorCommand, '/motor_cmd', 10)
        
        self.get_logger().info('실차용 모터 제어 노드 시작')
    
    def cmd_vel_callback(self, msg):
        """Twist 메시지를 모터 속도로 변환"""
        # 속도 제한
        linear = self.limit_speed(msg.linear.x, -self.max_linear, self.max_linear)
        angular = self.limit_speed(msg.angular.z, -self.max_angular, self.max_angular)
        
        # 차동 구동 모델: 좌/우 바퀴 속도 계산
        left_speed, right_speed = self.differential_drive(linear, angular)
        
        # 모터 명령 발행
        self.publish_motor_commands(left_speed, right_speed)
    
    def differential_drive(self, linear, angular):
        """차동 구동 모델"""
        # v_left = linear - (angular * wheel_base / 2)
        # v_right = linear + (angular * wheel_base / 2)
        
        left_speed = linear - (angular * self.wheel_base / 2.0)
        right_speed = linear + (angular * self.wheel_base / 2.0)
        
        return left_speed, right_speed
    
    def publish_motor_commands(self, left_speed, right_speed):
        """모터 명령 발행"""
        # 바퀴 속도 → 각속도 변환
        left_angular_vel = left_speed / self.wheel_radius
        right_angular_vel = right_speed / self.wheel_radius
        
        # PWM 값으로 변환 (-255 ~ 255 또는 -100 ~ 100)
        left_pwm = self.velocity_to_pwm(left_angular_vel)
        right_pwm = self.velocity_to_pwm(right_angular_vel)
        
        # 발행
        left_msg = Float32()
        left_msg.data = left_pwm
        self.left_motor_pub.publish(left_msg)
        
        right_msg = Float32()
        right_msg.data = right_pwm
        self.right_motor_pub.publish(right_msg)
    
    def velocity_to_pwm(self, angular_velocity):
        """각속도를 PWM 값으로 변환"""
        # 하드웨어에 맞게 조정 필요
        # 예: -30 rad/s ~ 30 rad/s → -255 ~ 255 PWM
        max_angular_vel = 30.0  # rad/s (실제 모터 사양에 맞게)
        max_pwm = 255.0
        
        pwm = (angular_velocity / max_angular_vel) * max_pwm
        return self.limit_speed(pwm, -max_pwm, max_pwm)
    
    def limit_speed(self, value, min_val, max_val):
        """속도 제한"""
        return max(min_val, min(max_val, value))


def main(args=None):
    rclpy.init(args=args)
    node = MotorController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # 정지 명령 발행
        stop_left = Float32()
        stop_left.data = 0.0
        node.left_motor_pub.publish(stop_left)
        
        stop_right = Float32()
        stop_right.data = 0.0
        node.right_motor_pub.publish(stop_right)
        
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
