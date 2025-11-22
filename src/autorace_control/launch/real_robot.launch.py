from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    """
    실차 전체 시스템 Launch 파일
    - 카메라 노드
    - 모터 제어 노드
    - IMU 노드
    - 미션 시스템
    """
    
    # 파라미터 파일 경로
    autorace_control_share = get_package_share_directory('autorace_control')
    autorace_missions_share = get_package_share_directory('autorace_missions')
    
    config_dir = os.path.join(autorace_control_share, 'config')
    missions_config = os.path.join(autorace_missions_share, 'config', 'missions.yaml')
    
    return LaunchDescription([
        # 디버그 모드 설정
        DeclareLaunchArgument(
            'debug_mode',
            default_value='true',
            description='Enable debug visualization'
        ),
        
        # 카메라 노드
        Node(
            package='autorace_control',
            executable='camera_node',
            name='camera_node',
            output='screen',
            parameters=[{
                'device_id': 0,  # /dev/video0
                'width': 640,
                'height': 480,
                'fps': 30,
                'publish_compressed': False,
                'calibration_file': os.path.join(config_dir, 'camera_calibration.yaml')
            }]
        ),
        
        # 모터 제어 노드
        Node(
            package='autorace_control',
            executable='motor_controller',
            name='motor_controller',
            output='screen',
            parameters=[{
                'max_linear_speed': 0.3,
                'max_angular_speed': 1.0,
                'wheel_base': 0.16,
                'wheel_radius': 0.033
            }]
        ),
        
        # IMU 노드 (ros2_razor_imu 패키지 사용)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(
                    get_package_share_directory('ros2_razor_imu'),
                    'launch',
                    'razor-pub.launch.py'
                )
            ])
        ),
        
        # 미션 시스템
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(
                    autorace_missions_share,
                    'launch',
                    'full_autorace.launch.py'
                )
            ]),
            launch_arguments={
                'debug_mode': LaunchConfiguration('debug_mode')
            }.items()
        ),
    ])
