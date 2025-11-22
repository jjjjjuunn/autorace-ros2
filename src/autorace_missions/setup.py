from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'autorace_missions'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launch 파일
        (os.path.join('share', package_name, 'launch'), 
         glob('launch/*.launch.py')),
        # Config 파일
        (os.path.join('share', package_name, 'config'), 
         glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='junwon',
    maintainer_email='qownsdnjs@gmail.com',
    description='AutoRace mission management package',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'mission_manager = autorace_missions.mission_manager:main',
            'colored_lane = autorace_missions.colored_lane:main',
            'crosswalk = autorace_missions.crosswalk:main',
            'obstacle_avoidance = autorace_missions.obstacle_avoidance:main',
            'lane_change = autorace_missions.lane_change:main',
            'roundabout = autorace_missions.roundabout:main',
            'tunnel = autorace_missions.tunnel:main',
            'barrier = autorace_missions.barrier:main',
            'parking = autorace_missions.parking:main',
        ],
    },
)
