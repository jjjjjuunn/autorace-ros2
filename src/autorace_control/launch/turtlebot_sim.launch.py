from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_dir = get_package_share_directory('autorace_control')
    
    track_urdf_path = os.path.join(pkg_dir, 'urdf', 'track.urdf')
    turtlebot_urdf_path = os.path.join(pkg_dir, 'urdf', 'turtlebot.urdf')
    
    with open(track_urdf_path, 'r') as f:
        track_urdf = f.read()
    
    with open(turtlebot_urdf_path, 'r') as f:
        turtlebot_urdf = f.read()
    
    return LaunchDescription([
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0', '0', '0', '0', '0', '0', 'world', 'odom'],
            output='screen'
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='track_state_publisher',
            namespace='track',
            parameters=[{'robot_description': track_urdf, 'use_tf_static': True}],
            output='screen'
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='turtlebot_state_publisher',
            parameters=[{'robot_description': turtlebot_urdf}],
            output='screen'
        ),
        Node(
            package='autorace_control',
            executable='turtlebot_simulator',
            output='screen'
        ),
        Node(
            package='autorace_control',
            executable='camera_simulator',
            output='screen'
        ),
        Node(
            package='autorace_control',
            executable='lane_follower',
            output='screen'
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            output='screen'
        )
    ])