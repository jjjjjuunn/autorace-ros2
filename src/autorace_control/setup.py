from setuptools import setup
from glob import glob
import os

package_name = 'autorace_control'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*')),
        (os.path.join('share', package_name, 'meshes'), glob('meshes/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='AutoRace Team',
    maintainer_email='qownsdnjs@gmail.com',
    description='AutoRace 자율주행 제어 시스템',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            # 시뮬레이션
            'turtlebot_simulator = autorace_control.turtlebot_simulator:main',
            'camera_simulator = autorace_control.camera_simulator:main',
            'lane_detector = autorace_control.lane_detector:main',
            'simple_drive = autorace_control.simple_drive:main',
            'lane_follower = autorace_control.lane_follower:main',
            'mission1_lane_speed = autorace_control.missions.mission1_lane_speed:main',
            'test_mission1 = autorace_control.utils.test_mission1:main',
            # 실차
            'camera_node = autorace_control.camera_node:main',
            'motor_controller = autorace_control.motor_controller:main',
        ],
    },
)
