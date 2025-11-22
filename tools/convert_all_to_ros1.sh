#!/bin/bash
# ROS2 → ROS1 전체 워크스페이스 변환 마스터 스크립트

set -e

echo "================================"
echo "🔄 ROS2 → ROS1 Conversion Script"
echo "================================"
echo ""

# 현재 디렉토리 확인
if [ ! -f "src/autorace_missions/setup.py" ]; then
    echo "❌ Run this script from workspace root!"
    echo "   cd /home/junwon/autorace_workspace"
    exit 1
fi

# 브랜치 확인
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "ros1-noetic" ]; then
    echo "⚠️  Current branch: $CURRENT_BRANCH"
    read -p "Switch to ros1-noetic branch? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout -b ros1-noetic 2>/dev/null || git checkout ros1-noetic
    fi
fi

echo "✅ On branch: $(git branch --show-current)"
echo ""

# Step 1: 패키지 구조 변환
echo "📦 Step 1/5: Converting package structure..."
chmod +x tools/convert_package_to_ros1.sh tools/ros2_to_ros1_converter.py

./tools/convert_package_to_ros1.sh autorace_missions
./tools/convert_package_to_ros1.sh autorace_vision

echo "✅ Package structure converted"
echo ""

# Step 2: Python 노드 변환
echo "🐍 Step 2/5: Converting Python nodes..."

MISSIONS=(
    "mission_manager"
    "colored_lane"
    "crosswalk"
    "obstacle_avoidance"
    "lane_change"
    "roundabout"
    "tunnel"
    "barrier"
    "parking"
)

for mission in "${MISSIONS[@]}"; do
    if [ -f "src/autorace_missions/autorace_missions/${mission}.py" ]; then
        echo "  Converting: ${mission}.py"
        python3 tools/ros2_to_ros1_converter.py \
            "src/autorace_missions/autorace_missions/${mission}.py" \
            "src/autorace_missions/nodes/${mission}.py"
        chmod +x "src/autorace_missions/nodes/${mission}.py"
    fi
done

# Vision utilities
if [ -f "src/autorace_vision/autorace_vision/color_filter.py" ]; then
    echo "  Converting: color_filter.py"
    python3 tools/ros2_to_ros1_converter.py \
        "src/autorace_vision/autorace_vision/color_filter.py" \
        "src/autorace_vision/src/color_filter.py"
fi

if [ -f "src/autorace_vision/autorace_vision/line_detector.py" ]; then
    echo "  Converting: line_detector.py"
    python3 tools/ros2_to_ros1_converter.py \
        "src/autorace_vision/autorace_vision/line_detector.py" \
        "src/autorace_vision/src/line_detector.py"
fi

echo "✅ Python nodes converted"
echo ""

# Step 3: Launch 파일 변환
echo "🚀 Step 3/5: Creating ROS1 launch files..."

# full_autorace.launch
cat > "src/autorace_missions/launch/full_autorace.launch" << 'LAUNCHEOF'
<?xml version="1.0"?>
<launch>
  <arg name="debug_mode" default="true"/>
  
  <!-- Mission Manager -->
  <node pkg="autorace_missions" type="mission_manager.py" name="mission_manager" output="screen">
    <param name="initial_mission" value="COLORED_LANE"/>
  </node>
  
  <!-- Mission 1: Colored Lane -->
  <node pkg="autorace_missions" type="colored_lane.py" name="colored_lane" output="screen">
    <param name="debug_mode" value="$(arg debug_mode)"/>
    <param name="slow_speed" value="0.08"/>
    <param name="normal_speed" value="0.15"/>
    <param name="fast_speed" value="0.22"/>
    <param name="angular_gain" value="0.01"/>
  </node>
  
  <!-- Mission 2: Crosswalk -->
  <node pkg="autorace_missions" type="crosswalk.py" name="crosswalk" output="screen">
    <param name="debug_mode" value="$(arg debug_mode)"/>
    <param name="normal_speed" value="0.15"/>
    <param name="stripe_threshold" value="3"/>
  </node>
  
  <!-- Mission 3: Obstacle Avoidance -->
  <node pkg="autorace_missions" type="obstacle_avoidance.py" name="obstacle_avoidance" output="screen">
    <param name="debug_mode" value="$(arg debug_mode)"/>
    <param name="normal_speed" value="0.15"/>
    <param name="obstacle_distance" value="0.4"/>
    <param name="safe_distance" value="0.6"/>
    <param name="angular_speed" value="0.5"/>
  </node>
  
  <!-- Mission 4: Lane Change -->
  <node pkg="autorace_missions" type="lane_change.py" name="lane_change" output="screen">
    <param name="debug_mode" value="$(arg debug_mode)"/>
    <param name="normal_speed" value="0.15"/>
    <param name="lane_change_speed" value="0.1"/>
    <param name="angular_speed" value="0.6"/>
    <param name="marker_area_threshold" value="3000"/>
  </node>
  
  <!-- Mission 5: Roundabout -->
  <node pkg="autorace_missions" type="roundabout.py" name="roundabout" output="screen">
    <param name="debug_mode" value="$(arg debug_mode)"/>
    <param name="normal_speed" value="0.12"/>
    <param name="slow_speed" value="0.06"/>
    <param name="angular_gain" value="0.012"/>
    <param name="safe_distance" value="0.5"/>
    <param name="roundabout_duration" value="150"/>
  </node>
  
  <!-- Mission 6: Tunnel -->
  <node pkg="autorace_missions" type="tunnel.py" name="tunnel" output="screen">
    <param name="debug_mode" value="$(arg debug_mode)"/>
    <param name="tunnel_speed" value="0.12"/>
    <param name="angular_gain" value="0.015"/>
    <param name="brightness_threshold" value="80"/>
  </node>
  
  <!-- Mission 7: Barrier -->
  <node pkg="autorace_missions" type="barrier.py" name="barrier" output="screen">
    <param name="debug_mode" value="$(arg debug_mode)"/>
    <param name="normal_speed" value="0.15"/>
    <param name="approach_speed" value="0.08"/>
    <param name="barrier_area_threshold" value="5000"/>
    <param name="open_angle_threshold" value="60"/>
  </node>
  
  <!-- Mission 8: Parking -->
  <node pkg="autorace_missions" type="parking.py" name="parking" output="screen">
    <param name="debug_mode" value="$(arg debug_mode)"/>
    <param name="parking_speed" value="0.08"/>
    <param name="reverse_speed" value="-0.08"/>
  </node>
</launch>
LAUNCHEOF

echo "✅ Launch files created"
echo ""

# Step 4: CMakeLists.txt 생성
echo "🔨 Step 4/5: Creating CMakeLists.txt..."

# autorace_missions/CMakeLists.txt
cat > "src/autorace_missions/CMakeLists.txt" << 'CMAKEEOF'
cmake_minimum_required(VERSION 3.0.2)
project(autorace_missions)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  geometry_msgs
  cv_bridge
)

catkin_python_setup()

catkin_package(
  CATKIN_DEPENDS rospy std_msgs sensor_msgs geometry_msgs cv_bridge
)

install(PROGRAMS
  nodes/mission_manager.py
  nodes/colored_lane.py
  nodes/crosswalk.py
  nodes/obstacle_avoidance.py
  nodes/lane_change.py
  nodes/roundabout.py
  nodes/tunnel.py
  nodes/barrier.py
  nodes/parking.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
  FILES_MATCHING PATTERN "*.launch"
)

install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
  FILES_MATCHING PATTERN "*.yaml"
)
CMAKEEOF

# autorace_vision/CMakeLists.txt
cat > "src/autorace_vision/CMakeLists.txt" << 'CMAKEEOF'
cmake_minimum_required(VERSION 3.0.2)
project(autorace_vision)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  cv_bridge
)

catkin_python_setup()

catkin_package(
  CATKIN_DEPENDS rospy std_msgs sensor_msgs cv_bridge
)
CMAKEEOF

echo "✅ CMakeLists.txt created"
echo ""

# Step 5: 정리
echo "🧹 Step 5/5: Cleanup..."

# ROS2 빌드 파일 제거
rm -rf build/ install/ log/

# ROS2 setup.py 백업
mv src/autorace_missions/setup.py src/autorace_missions/setup.py.ros2_backup 2>/dev/null || true
mv src/autorace_vision/setup.py src/autorace_vision/setup.py.ros2_backup 2>/dev/null || true

# ROS1용 setup.py 생성
cat > "src/autorace_missions/setup.py" << 'SETUPEOF'
#!/usr/bin/env python
from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=['autorace_missions'],
    package_dir={'': 'src'}
)

setup(**d)
SETUPEOF

cat > "src/autorace_vision/setup.py" << 'SETUPEOF'
#!/usr/bin/env python
from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=['autorace_vision'],
    package_dir={'': 'src'}
)

setup(**d)
SETUPEOF

echo "✅ Cleanup complete"
echo ""

# 완료
echo "================================"
echo "✅ Conversion Complete!"
echo "================================"
echo ""
echo "📋 Next steps:"
echo "   1. Review converted files:"
echo "      - src/autorace_missions/nodes/*.py"
echo "      - src/autorace_missions/launch/*.launch"
echo "      - src/autorace_missions/CMakeLists.txt"
echo ""
echo "   2. Test build:"
echo "      catkin build"
echo "      source devel/setup.bash"
echo ""
echo "   3. Test run:"
echo "      roslaunch autorace_missions full_autorace.launch"
echo ""
echo "   4. Commit changes:"
echo "      git add ."
echo "      git commit -m 'Complete ROS1 Noetic conversion'"
echo "      git push origin ros1-noetic"
echo ""
echo "⚠️  Manual review required for:"
echo "   - Timer callbacks (add 'event' parameter)"
echo "   - Complex f-strings"
echo "   - Custom logic"
echo ""
