cmake_minimum_required(VERSION 3.0.2)
project(autorace_missions)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  geometry_msgs
  ackermann_msgs
)

catkin_package()

catkin_install_python(PROGRAMS
  nodes/motor_controller.py
  nodes/mission_manager.py
  nodes/colored_lane.py
  nodes/crosswalk.py
  nodes/obstacle_avoidance.py
  nodes/lane_change.py
  nodes/roundabout.py
  nodes/tunnel.py
  nodes/barrier.py
  nodes/parking.py
  nodes/intersection.py
  nodes/lane_following.py
  nodes/stop_line.py
  nodes/traffic_light.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)
