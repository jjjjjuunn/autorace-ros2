#!/usr/bin/env python
"""
미션 3: 라바콘 회피 (LiDAR 사용)
- LiDAR로 전방 장애물 감지
- 왼쪽 공간 있으면 좌회전
- 오른쪽 공간 있으면 우회전
"""

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
import numpy as np


class ObstacleAvoidanceMission:
    def __init__(self):
        rospy.init_node('obstacle_avoidance_mission', anonymous=False)
        
        # 파라미터
        
        self.debug_mode = rospy.get_param('~debug_mode', 0.1)
        self.normal_speed = rospy.get_param('~normal_speed', 0.1)
        self.slow_speed = rospy.get_param('~slow_speed', 0.1)
        self.turn_speed = rospy.get_param('~turn_speed', 0.1)
        self.obstacle_distance = rospy.get_param('~obstacle_distance', 0.1)
        self.safe_distance = rospy.get_param('~safe_distance', 0.1)
        self.angular_speed = rospy.get_param('~angular_speed', 0.1)
        
        # 상태
        self.mission_active = False
        self.avoiding = False
        self.avoidance_direction = None  # 'LEFT' or 'RIGHT'
        self.obstacles_passed = 0
        self.required_obstacles = 3  # 미션 완료 조건: 3개 라바콘 회피
        
        # Subscriber
        rospy.Subscriber('/mission/current', String, self.mission_callback, queue_size=10)
        rospy.Subscriber('/scan', LaserScan, self.lidar_callback, queue_size=10)
        
        # Publisher
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.mission_complete_pub = rospy.Publisher('/mission/complete', String, queue_size=10)
        
        rospy.loginfo('라바콘 회피 미션 노드 준비됨')
    
    def mission_callback(self, msg):
        """현재 미션이 OBSTACLE_AVOIDANCE인지 확인"""
        if msg.data == 'OBSTACLE_AVOIDANCE':
            if not self.mission_active:
                rospy.loginfo('🚧 라바콘 회피 미션 시작!')
                self.mission_active = True
                self.obstacles_passed = 0
                self.avoiding = False
        else:
            if self.mission_active and self.obstacles_passed >= self.required_obstacles:
                complete_msg = String()
                complete_msg.data = 'OBSTACLE_AVOIDANCE'
                self.mission_complete_pub.publish(complete_msg)
            self.mission_active = False
    
    def lidar_callback(self, msg):
        """LiDAR 데이터 처리 및 장애물 회피"""
        if not self.mission_active:
            return
        
        try:
            # LiDAR 데이터를 섹터별로 분석
            ranges = np.array(msg.ranges)
            ranges[np.isinf(ranges)] = msg.range_max
            ranges[np.isnan(ranges)] = msg.range_max
            
            # 전방, 좌측, 우측 섹터 정의
            num_points = len(ranges)
            
            # 전방: -15도 ~ +15도
            front_indices = list(range(0, num_points // 12)) + \
                          list(range(num_points - num_points // 12, num_points))
            front_distances = ranges[front_indices]
            
            # 좌측: 45도 ~ 90도
            left_start = num_points // 8
            left_end = num_points // 4
            left_distances = ranges[left_start:left_end]
            
            # 우측: 270도 ~ 315도
            right_start = 3 * num_points // 4
            right_end = 7 * num_points // 8
            right_distances = ranges[right_start:right_end]
            
            # 최소 거리 계산
            front_min = np.min(front_distances) if len(front_distances) > 0 else msg.range_max
            left_min = np.min(left_distances) if len(left_distances) > 0 else msg.range_max
            right_min = np.min(right_distances) if len(right_distances) > 0 else msg.range_max
            
            if self.debug_mode:
                rospy.loginfo(
                    f'LiDAR - 전방: {front_min:.2f}m, 좌: {left_min:.2f}m, 우: {right_min:.2f}m'
                )
            
            # 장애물 회피 로직
            if front_min < self.obstacle_distance:
                if not self.avoiding:
                    self.start_avoidance(left_min, right_min)
            elif front_min > self.safe_distance and self.avoiding:
                self.complete_avoidance()
            
            # 차량 제어
            self.control_vehicle(front_min, left_min, right_min)
            
        except Exception as e:
            rospy.logerr(f'LiDAR 처리 실패: {str(e)}')
    
    def start_avoidance(self, left_distance, right_distance):
        """장애물 회피 시작"""
        self.avoiding = True
        
        # 더 넓은 쪽으로 회피
        if left_distance > right_distance:
            self.avoidance_direction = 'LEFT'
            rospy.loginfo('⬅️ 좌측으로 회피!')
        else:
            self.avoidance_direction = 'RIGHT'
            rospy.loginfo('➡️ 우측으로 회피!')
    
    def complete_avoidance(self):
        """장애물 회피 완료"""
        self.avoiding = False
        self.obstacles_passed += 1
        rospy.loginfo(f'✅ 라바콘 {self.obstacles_passed}개 회피 완료!')
        
        # 미션 완료 확인
        if self.obstacles_passed >= self.required_obstacles:
            rospy.loginfo('🎉 라바콘 회피 미션 완료!')
            complete_msg = String()
            complete_msg.data = 'OBSTACLE_AVOIDANCE'
            self.mission_complete_pub.publish(complete_msg)
            self.mission_active = False
    
    def control_vehicle(self, front_distance, left_distance, right_distance):
        """차량 제어"""
        cmd = Twist()
        
        if not self.avoiding:
            # 정상 주행
            cmd.linear.x = self.normal_speed
            cmd.angular.z = 0.0
        else:
            # 회피 중
            if self.avoidance_direction == 'LEFT':
                cmd.linear.x = self.turn_speed
                cmd.angular.z = self.angular_speed  # 좌회전 (양수)
            else:  # RIGHT
                cmd.linear.x = self.turn_speed
                cmd.angular.z = -self.angular_speed  # 우회전 (음수)
            
            # 전방 장애물이 너무 가까우면 정지
            if front_distance < self.obstacle_distance * 0.5:
                cmd.linear.x = 0.0
                rospy.logwarn('⚠️ 긴급 정지!')
        
        self.cmd_vel_pub.publish(cmd)


def main():
    try:
        node = ObstacleAvoidanceMission()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass

if __name__ == '__main__':
    main()
