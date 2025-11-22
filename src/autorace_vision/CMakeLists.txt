cmake_minimum_required(VERSION 3.0.2)
project(autorace_vision)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  geometry_msgs
  cv_bridge
)

catkin_package()

catkin_install_python(PROGRAMS
  nodes/lane_detector.py
  nodes/traffic_light_detector.py
  nodes/crosswalk_detector.py
  nodes/obstacle_detector.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)
