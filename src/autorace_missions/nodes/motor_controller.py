#!/usr/bin/env python
"""
WeGo 차량용 모터 제어 노드
Twist → Ackermann 변환
"""

import rospy
from geometry_msgs.msg import Twist
from ackermann_msgs.msg import AckermannDriveStamped
import math


class MotorController:
    def __init__(self):
        rospy.init_node('motor_controller', anonymous=False)
        
        # 파라미터
        self.wheel_base = rospy.get_param('~wheel_base', 0.25)  # 축간거리 (m)
        self.max_speed = rospy.get_param('~max_speed', 1.0)  # 최대 속도 (m/s)
        self.max_steering_angle = rospy.get_param('~max_steering_angle', 0.34)  # 최대 조향각 (rad)
        
        # Subscriber: cmd_vel (Twist)
        rospy.Subscriber('/cmd_vel', Twist, self.cmd_vel_callback, queue_size=1)
        
        # Publisher: Ackermann 명령
        self.ackermann_pub = rospy.Publisher(
            '/ackermann_cmd_mux/input/navigation',
            AckermannDriveStamped,
            queue_size=1
        )
        
        rospy.loginfo('Motor Controller (Twist → Ackermann) 시작')
        rospy.loginfo(f'  wheel_base: {self.wheel_base}m')
        rospy.loginfo(f'  max_speed: {self.max_speed}m/s')
        rospy.loginfo(f'  max_steering_angle: {self.max_steering_angle}rad')
    
    def cmd_vel_callback(self, msg):
        """Twist → Ackermann 변환"""
        linear_speed = msg.linear.x
        angular_velocity = msg.angular.z
        
        # 속도 제한
        linear_speed = self.limit(linear_speed, -self.max_speed, self.max_speed)
        
        # Ackermann 조향각 계산
        # steering_angle = atan(angular_velocity * wheelbase / linear_speed)
        if abs(linear_speed) < 0.01:  # 정지 시
            steering_angle = 0.0
        else:
            steering_angle = math.atan2(angular_velocity * self.wheel_base, linear_speed)
        
        # 조향각 제한
        steering_angle = self.limit(steering_angle, -self.max_steering_angle, self.max_steering_angle)
        
        # Ackermann 메시지 생성
        ackermann_msg = AckermannDriveStamped()
        ackermann_msg.header.stamp = rospy.Time.now()
        ackermann_msg.header.frame_id = 'base_link'
        ackermann_msg.drive.speed = linear_speed
        ackermann_msg.drive.steering_angle = steering_angle
        
        # 발행
        self.ackermann_pub.publish(ackermann_msg)
    
    def limit(self, value, min_val, max_val):
        """값 제한"""
        return max(min_val, min(max_val, value))
    
    def run(self):
        """노드 실행"""
        rospy.spin()


def main():
    try:
        controller = MotorController()
        controller.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
