"""
단일 미션 테스트용 Launch 파일
사용법: ros2 launch autorace_missions single_mission.launch.py mission:=stop_line
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        # 미션 선택
        DeclareLaunchArgument(
            'mission',
            default_value='lane_following',
            description='Mission to test (lane_following, stop_line, crosswalk, traffic_light)'
        ),
        
        DeclareLaunchArgument(
            'debug_mode',
            default_value='true',
            description='Enable debug visualization'
        ),
        
        # 선택된 미션만 실행
        Node(
            package='autorace_missions',
            executable=LaunchConfiguration('mission'),
            name=LaunchConfiguration('mission'),
            output='screen',
            parameters=[{
                'debug_mode': LaunchConfiguration('debug_mode')
            }]
        ),
    ])
