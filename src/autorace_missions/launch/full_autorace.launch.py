from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        # 파라미터
        DeclareLaunchArgument(
            'debug_mode',
            default_value='true',
            description='Enable debug visualization'
        ),
        
        # 미션 매니저
        Node(
            package='autorace_missions',
            executable='mission_manager',
            name='mission_manager',
            output='screen',
            parameters=[{
                'initial_mission': 'COLORED_LANE'
            }]
        ),
        
        # 미션 1: 색깔 차로
        Node(
            package='autorace_missions',
            executable='colored_lane',
            name='colored_lane',
            output='screen',
            parameters=[{
                'debug_mode': LaunchConfiguration('debug_mode'),
                'slow_speed': 0.08,
                'normal_speed': 0.15,
                'fast_speed': 0.22,
                'angular_gain': 0.01
            }]
        ),
        
        # 미션 2: 횡단보도
        Node(
            package='autorace_missions',
            executable='crosswalk',
            name='crosswalk',
            output='screen',
            parameters=[{
                'debug_mode': LaunchConfiguration('debug_mode'),
                'normal_speed': 0.15,
                'stripe_threshold': 3
            }]
        ),
        
        # 미션 3: 라바콘 회피
        Node(
            package='autorace_missions',
            executable='obstacle_avoidance',
            name='obstacle_avoidance',
            output='screen',
            parameters=[{
                'debug_mode': LaunchConfiguration('debug_mode'),
                'normal_speed': 0.15,
                'slow_speed': 0.08,
                'turn_speed': 0.05,
                'obstacle_distance': 0.4,
                'safe_distance': 0.6,
                'angular_speed': 0.5
            }]
        ),
        
        # 미션 4: 차선 변경
        Node(
            package='autorace_missions',
            executable='lane_change',
            name='lane_change',
            output='screen',
            parameters=[{
                'debug_mode': LaunchConfiguration('debug_mode'),
                'normal_speed': 0.15,
                'lane_change_speed': 0.1,
                'angular_speed': 0.6,
                'marker_area_threshold': 3000
            }]
        ),
        
        # 미션 5: 회전 교차로
        Node(
            package='autorace_missions',
            executable='roundabout',
            name='roundabout',
            output='screen',
            parameters=[{
                'debug_mode': LaunchConfiguration('debug_mode'),
                'normal_speed': 0.12,
                'slow_speed': 0.06,
                'angular_gain': 0.012,
                'safe_distance': 0.5,
                'roundabout_duration': 150
            }]
        ),
        
        # 미션 6: 터널
        Node(
            package='autorace_missions',
            executable='tunnel',
            name='tunnel',
            output='screen',
            parameters=[{
                'debug_mode': LaunchConfiguration('debug_mode'),
                'tunnel_speed': 0.12,
                'angular_gain': 0.015,
                'brightness_threshold': 80
            }]
        ),
        
        # 미션 7: 차단기
        Node(
            package='autorace_missions',
            executable='barrier',
            name='barrier',
            output='screen',
            parameters=[{
                'debug_mode': LaunchConfiguration('debug_mode'),
                'normal_speed': 0.15,
                'approach_speed': 0.08,
                'barrier_area_threshold': 5000,
                'open_angle_threshold': 60
            }]
        ),
        
        # 미션 8: 주차
        Node(
            package='autorace_missions',
            executable='parking',
            name='parking',
            output='screen',
            parameters=[{
                'debug_mode': LaunchConfiguration('debug_mode'),
                'parking_speed': 0.08,
                'reverse_speed': -0.08
            }]
        ),
    ])
