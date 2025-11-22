#!/usr/bin/env python3
"""
AutoRace 미션 매니저
- 미션 순서 관리
- 미션 간 전환
- 상태 머신
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32
from enum import Enum


class MissionState(Enum):
    IDLE = 0
    COLORED_LANE = 1          # 미션 1: 색깔 차로 감/가속
    CROSSWALK = 2             # 미션 2: 횡단보도 정지 후 출발
    OBSTACLE_AVOIDANCE = 3    # 미션 3: 라바콘 회피 (LiDAR)
    LANE_CHANGE = 4           # 미션 4: 마커 보고 차선 변경
    ROUNDABOUT = 5            # 미션 5: 회전 교차로
    TUNNEL = 6                # 미션 6: 터널 (암실)
    BARRIER = 7               # 미션 7: 차단기
    PARKING = 8               # 미션 8: 주차
    FINISHED = 9


class MissionManager(Node):
    def __init__(self):
        super().__init__('mission_manager')
        
        # 파라미터
        self.declare_parameter('initial_mission', 'COLORED_LANE')
        initial = self.get_parameter('initial_mission').value
        
        # 현재 미션 상태
        try:
            self.current_mission = MissionState[initial]
        except KeyError:
            self.get_logger().warn(f'Unknown mission: {initial}, starting with COLORED_LANE')
            self.current_mission = MissionState.COLORED_LANE
        
        # Publisher
        self.mission_pub = self.create_publisher(String, '/mission/current', 10)
        self.state_pub = self.create_publisher(Int32, '/mission/state', 10)
        
        # Subscriber (각 미션 완료 신호 수신)
        self.create_subscription(String, '/mission/complete', 
                               self.mission_complete_callback, 10)
        
        # 타이머 (상태 발행)
        self.create_timer(0.1, self.publish_state)
        
        self.get_logger().info(f'🏁 미션 매니저 시작 - 현재: {self.current_mission.name}')
    
    def mission_complete_callback(self, msg):
        """미션 완료 신호 수신 → 다음 미션으로 전환"""
        completed_mission = msg.data
        self.get_logger().info(f'✅ {completed_mission} 완료!')
        
        # 다음 미션으로 전환
        self.transition_to_next_mission()
    
    def transition_to_next_mission(self):
        """미션 시퀀스 관리"""
        mission_sequence = {
            MissionState.COLORED_LANE: MissionState.CROSSWALK,
            MissionState.CROSSWALK: MissionState.OBSTACLE_AVOIDANCE,
            MissionState.OBSTACLE_AVOIDANCE: MissionState.LANE_CHANGE,
            MissionState.LANE_CHANGE: MissionState.ROUNDABOUT,
            MissionState.ROUNDABOUT: MissionState.TUNNEL,
            MissionState.TUNNEL: MissionState.BARRIER,
            MissionState.BARRIER: MissionState.PARKING,
            MissionState.PARKING: MissionState.FINISHED
        }
        
        if self.current_mission in mission_sequence:
            self.current_mission = mission_sequence[self.current_mission]
            self.get_logger().info(f'🔄 미션 전환 → {self.current_mission.name}')
        else:
            self.get_logger().info('🏁 모든 미션 완료!')
    
    def publish_state(self):
        """현재 미션 상태 발행"""
        # String 메시지
        mission_msg = String()
        mission_msg.data = self.current_mission.name
        self.mission_pub.publish(mission_msg)
        
        # Int 메시지
        state_msg = Int32()
        state_msg.data = self.current_mission.value
        self.state_pub.publish(state_msg)


def main(args=None):
    rclpy.init(args=args)
    node = MissionManager()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
