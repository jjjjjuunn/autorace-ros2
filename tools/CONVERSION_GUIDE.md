# ROS2 → ROS1 변환 가이드

## 📋 변환 절차

### Step 1: 브랜치 준비

```bash
cd /home/junwon/autorace_workspace

# ros2-humble 브랜치에서 모든 작업 커밋 확인
git checkout ros2-humble
git status
git add .
git commit -m "Final ROS2 Humble implementation"
git push origin ros2-humble

# ros1-noetic 브랜치 생성
git checkout -b ros1-noetic

# 초기 상태 커밋
git add .
git commit -m "Start ROS1 Noetic conversion"
```

---

### Step 2: 빌드 시스템 변경

#### 2.1 워크스페이스 루트

```bash
cd /home/junwon/autorace_workspace

# colcon → catkin 변환
# 기존 build/, install/, log/ 제거
rm -rf build/ install/ log/

# catkin 워크스페이스 초기화
catkin init
# 또는
mkdir -p build devel
```

---

### Step 3: 패키지별 변환

#### 3.1 autorace_missions 변환

```bash
cd /home/junwon/autorace_workspace

# 패키지 구조 변환
chmod +x tools/convert_package_to_ros1.sh
./tools/convert_package_to_ros1.sh autorace_missions

# 각 Python 노드 변환
chmod +x tools/ros2_to_ros1_converter.py

# 미션 매니저
python3 tools/ros2_to_ros1_converter.py \
  src/autorace_missions/autorace_missions/mission_manager.py \
  src/autorace_missions/nodes/mission_manager.py

# 미션 1: 색깔 차로
python3 tools/ros2_to_ros1_converter.py \
  src/autorace_missions/autorace_missions/colored_lane.py \
  src/autorace_missions/nodes/colored_lane.py

# 미션 2: 횡단보도
python3 tools/ros2_to_ros1_converter.py \
  src/autorace_missions/autorace_missions/crosswalk.py \
  src/autorace_missions/nodes/crosswalk.py

# 미션 3: 라바콘 회피
python3 tools/ros2_to_ros1_converter.py \
  src/autorace_missions/autorace_missions/obstacle_avoidance.py \
  src/autorace_missions/nodes/obstacle_avoidance.py

# 미션 4: 차선 변경
python3 tools/ros2_to_ros1_converter.py \
  src/autorace_missions/autorace_missions/lane_change.py \
  src/autorace_missions/nodes/lane_change.py

# 미션 5: 회전 교차로
python3 tools/ros2_to_ros1_converter.py \
  src/autorace_missions/autorace_missions/roundabout.py \
  src/autorace_missions/nodes/roundabout.py

# 미션 6: 터널
python3 tools/ros2_to_ros1_converter.py \
  src/autorace_missions/autorace_missions/tunnel.py \
  src/autorace_missions/nodes/tunnel.py

# 미션 7: 차단기
python3 tools/ros2_to_ros1_converter.py \
  src/autorace_missions/autorace_missions/barrier.py \
  src/autorace_missions/nodes/barrier.py

# 미션 8: 주차
python3 tools/ros2_to_ros1_converter.py \
  src/autorace_missions/autorace_missions/parking.py \
  src/autorace_missions/nodes/parking.py
```

#### 3.2 autorace_vision 변환

```bash
./tools/convert_package_to_ros1.sh autorace_vision

python3 tools/ros2_to_ros1_converter.py \
  src/autorace_vision/autorace_vision/color_filter.py \
  src/autorace_vision/src/color_filter.py

python3 tools/ros2_to_ros1_converter.py \
  src/autorace_vision/autorace_vision/line_detector.py \
  src/autorace_vision/src/line_detector.py
```

---

### Step 4: Launch 파일 변환

ROS2 Python launch → ROS1 XML launch

#### 예시: full_autorace.launch 변환

**ROS2 (full_autorace.launch.py):**
```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package='autorace_missions', executable='mission_manager', ...)
    ])
```

**ROS1 (full_autorace.launch):**
```xml
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
  </node>
  
  <!-- Mission 2-8... -->
</launch>
```

```bash
# 수동으로 XML launch 파일 생성
nano src/autorace_missions/launch/full_autorace.launch
```

---

### Step 5: 파라미터 파일 변환

**ROS2 YAML (그대로 유지 가능!):**
```yaml
/colored_lane:
  ros__parameters:
    debug_mode: true
```

**ROS1 YAML (약간 수정):**
```yaml
colored_lane:
  debug_mode: true
  slow_speed: 0.08
```

```bash
# ROS1용 파라미터 파일 생성
cp src/autorace_missions/config/missions.yaml \
   src/autorace_missions/config/missions_ros1.yaml

# ros__parameters 제거
sed -i 's/ros__parameters://g' src/autorace_missions/config/missions_ros1.yaml
```

---

### Step 6: CMakeLists.txt 작성

```bash
nano src/autorace_missions/CMakeLists.txt
```

```cmake
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

# Python 노드 설치
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

# Launch 파일 설치
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
  FILES_MATCHING PATTERN "*.launch"
)

# Config 파일 설치
install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
  FILES_MATCHING PATTERN "*.yaml"
)
```

---

### Step 7: package.xml 수정

```xml
<?xml version="1.0"?>
<package format="2">
  <name>autorace_missions</name>
  <version>0.1.0</version>
  <description>AutoRace mission management package for ROS1 Noetic</description>
  <maintainer email="qownsdnjs@gmail.com">junwon</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>catkin</buildtool_depend>
  
  <build_depend>rospy</build_depend>
  <build_depend>std_msgs</build_depend>
  <build_depend>sensor_msgs</build_depend>
  <build_depend>geometry_msgs</build_depend>
  <build_depend>cv_bridge</build_depend>
  
  <exec_depend>rospy</exec_depend>
  <exec_depend>std_msgs</exec_depend>
  <exec_depend>sensor_msgs</exec_depend>
  <exec_depend>geometry_msgs</exec_depend>
  <exec_depend>cv_bridge</exec_depend>
  <exec_depend>python-opencv</exec_depend>
  <exec_depend>python-numpy</exec_depend>
</package>
```

---

### Step 8: 빌드 테스트

```bash
cd /home/junwon/autorace_workspace

# Catkin 빌드
catkin build autorace_missions autorace_vision

# 또는
catkin_make --only-pkg-with-deps autorace_missions

# 소스
source devel/setup.bash

# 테스트 실행
roscore &
rosrun autorace_missions mission_manager.py
```

---

## 🔍 수동 수정 체크리스트

### Python 노드

- [ ] `rclpy` → `rospy`
- [ ] `Node` 클래스 상속 제거
- [ ] `super().__init__('node_name')` → `rospy.init_node('node_name')`
- [ ] `self.create_publisher()` → `rospy.Publisher()`
- [ ] `self.create_subscription()` → `rospy.Subscriber()`
- [ ] `self.create_timer()` → `rospy.Timer()`
- [ ] `self.get_logger().info()` → `rospy.loginfo()`
- [ ] Timer callback에 `event` 인자 추가
- [ ] f-string → % formatting
- [ ] `rclpy.spin()` → `rospy.spin()`

### Launch 파일

- [ ] Python → XML 변환
- [ ] `<node>` 태그 사용
- [ ] `type` 속성에 `.py` 확장자 포함

### 파라미터 파일

- [ ] `ros__parameters:` 제거
- [ ] 노드명 기반 네임스페이스

---

## 📊 변환 진행 상황

```
autorace_missions/
├── mission_manager.py    [  ] 변환 전  [ ✓ ] 변환 완료
├── colored_lane.py       [  ] 변환 전  [ ✓ ] 변환 완료
├── crosswalk.py          [  ] 변환 전  [ ✓ ] 변환 완료
├── obstacle_avoidance.py [  ] 변환 전  [ ✓ ] 변환 완료
├── lane_change.py        [  ] 변환 전  [ ✓ ] 변환 완료
├── roundabout.py         [  ] 변환 전  [ ✓ ] 변환 완료
├── tunnel.py             [  ] 변환 전  [ ✓ ] 변환 완료
├── barrier.py            [  ] 변환 전  [ ✓ ] 변환 완료
└── parking.py            [  ] 변환 전  [ ✓ ] 변환 완료

launch/
├── full_autorace.launch  [  ] 변환 전  [ ✓ ] 변환 완료
└── single_mission.launch [  ] 변환 전  [ ✓ ] 변환 완료
```

---

## 🚀 차량 배포

변환 완료 후:

```bash
# ros1-noetic 브랜치 커밋
git add .
git commit -m "Complete ROS1 Noetic conversion"
git push origin ros1-noetic

# 차량에서 (Ubuntu 20.04 + ROS1 Noetic)
cd ~
git clone -b ros1-noetic https://github.com/your-repo/autorace_workspace.git
cd autorace_workspace

# 빌드
catkin build
source devel/setup.bash

# 실행
roslaunch autorace_missions full_autorace.launch
```

---

## ⚠️ 주의사항

1. **자동 변환 스크립트는 80% 정도만 완벽**
   - 복잡한 로직은 수동 검토 필수!

2. **Timer callback 시그니처 변경**
   ```python
   # ROS2
   def timer_callback(self):
       pass
   
   # ROS1
   def timer_callback(self, event):  # event 인자 추가!
       pass
   ```

3. **LaunchConfiguration 없음**
   - ROS1에서는 `<arg>` 태그 사용

4. **파라미터 접근 방식**
   ```python
   # ROS2
   self.get_parameter('param').value
   
   # ROS1
   rospy.get_param('~param', default_value)
   ```

---

## 🎯 다음 단계

1. ✅ 변환 스크립트 실행
2. ✅ 수동 검토 및 수정
3. ✅ 로컬 빌드 테스트
4. ✅ Git 커밋 & 푸시
5. ✅ 차량에서 Clone & 빌드
6. ✅ 실제 테스트!
