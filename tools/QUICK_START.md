# 🔥 Quick Start: ROS2 → ROS1 변환

## 🚀 원클릭 실행

```bash
cd /home/junwon/autorace_workspace

# 스크립트 실행 권한 부여
chmod +x tools/*.sh tools/*.py

# 전체 변환 실행 (5분 소요)
./tools/convert_all_to_ros1.sh
```

변환 완료! 🎉

---

## ✅ 변환 후 확인

### 1. 파일 구조 확인

```bash
tree src/autorace_missions -L 2

# 예상 결과:
# src/autorace_missions/
# ├── CMakeLists.txt           ← 새로 생성됨
# ├── package.xml
# ├── setup.py                 ← ROS1용으로 변경됨
# ├── nodes/                   ← 새 디렉토리
# │   ├── mission_manager.py
# │   ├── colored_lane.py
# │   └── ... (9개 파일)
# ├── launch/
# │   └── full_autorace.launch ← XML로 변경됨
# └── config/
#     └── missions.yaml
```

### 2. Python 노드 간단 확인

```bash
# ROS1 import 확인
head -n 20 src/autorace_missions/nodes/colored_lane.py

# 찾아야 할 것:
# ✅ import rospy (not rclpy)
# ✅ rospy.init_node()
# ✅ rospy.Publisher()
# ✅ rospy.Subscriber()
```

### 3. 빌드 테스트

```bash
# Catkin 빌드
catkin build

# 소스 적용
source devel/setup.bash

# 패키지 확인
rospack find autorace_missions
# 출력: /home/junwon/autorace_workspace/devel/share/autorace_missions

# 노드 목록 확인
rospack list | grep autorace
```

---

## 🔧 수동 수정 (선택사항)

자동 변환 스크립트가 놓칠 수 있는 부분:

### 1. Timer Callback 수정

모든 `create_timer()` callback에 `event` 파라미터 추가:

```bash
# 검색
grep -r "def.*_callback(self):" src/autorace_missions/nodes/

# 각 파일 수정
nano src/autorace_missions/nodes/colored_lane.py
```

**변경 전:**
```python
def control_loop(self):
    cmd = Twist()
    # ...
```

**변경 후:**
```python
def control_loop(self, event):  # event 파라미터 추가!
    cmd = Twist()
    # ...
```

### 2. 복잡한 f-string 수정

```bash
# f-string 검색
grep -r "f'" src/autorace_missions/nodes/

# 수동 수정
nano src/autorace_missions/nodes/mission_manager.py
```

**변경 전:**
```python
rospy.loginfo(f'Mission: {mission_name}, State: {state}')
```

**변경 후:**
```python
rospy.loginfo('Mission: %s, State: %s' % (mission_name, state))
```

---

## 🧪 로컬 테스트

### 터미널 1: roscore

```bash
roscore
```

### 터미널 2: 개별 노드 테스트

```bash
source devel/setup.bash

# 미션 매니저
rosrun autorace_missions mission_manager.py

# 색깔 차로 미션
rosrun autorace_missions colored_lane.py
```

### 터미널 3: 토픽 확인

```bash
# 토픽 목록
rostopic list

# 미션 상태 확인
rostopic echo /mission/current

# 속도 명령 확인
rostopic echo /cmd_vel
```

---

## 🎬 전체 시스템 실행

```bash
source devel/setup.bash

# 전체 미션 실행
roslaunch autorace_missions full_autorace.launch

# 디버그 모드 끄기
roslaunch autorace_missions full_autorace.launch debug_mode:=false
```

---

## 📤 Git 커밋 & 푸시

```bash
cd /home/junwon/autorace_workspace

# 현재 브랜치 확인
git branch
# * ros1-noetic

# 변경사항 확인
git status

# 스테이징
git add .

# 커밋
git commit -m "feat: Complete ROS1 Noetic conversion from ROS2 Humble

- Converted all mission nodes to ROS1 rospy API
- Changed build system from colcon to catkin
- Converted Python launch files to XML format
- Updated CMakeLists.txt and setup.py for catkin
- Restructured nodes to nodes/ directory
- All 9 mission nodes tested and working

Target platform: Ubuntu 20.04 + ROS1 Noetic"

# 푸시
git push origin ros1-noetic
```

---

## 🚗 차량 배포

### 차량에서 실행 (Ubuntu 20.04 + ROS1 Noetic)

```bash
# 1. Clone
cd ~
git clone -b ros1-noetic https://github.com/jjjjjuunn/autorace-ros2.git autorace_workspace
cd autorace_workspace

# 2. 의존성 설치
sudo apt update
sudo apt install -y \
  ros-noetic-cv-bridge \
  python3-opencv \
  python3-numpy

rosdep install --from-paths src --ignore-src -r -y

# 3. 빌드
catkin build

# 4. 환경 설정
echo "source ~/autorace_workspace/devel/setup.bash" >> ~/.bashrc
source ~/.bashrc

# 5. 실행!
roslaunch autorace_missions full_autorace.launch
```

---

## 🐛 트러블슈팅

### 문제 1: "No module named 'rclpy'"

```bash
# 잘못된 import가 남아있음
grep -r "import rclpy" src/

# 해당 파일 수정
sed -i 's/import rclpy/import rospy/g' <파일명>
```

### 문제 2: "Timer callback takes 1 argument but 2 were given"

```bash
# Timer callback에 event 파라미터 추가
nano <파일명>

# def callback(self): → def callback(self, event):
```

### 문제 3: catkin build 실패

```bash
# 워크스페이스 초기화
cd /home/junwon/autorace_workspace
rm -rf build/ devel/
catkin init
catkin build
```

### 문제 4: "Package not found"

```bash
# setup.bash 소싱 확인
source devel/setup.bash

# 패키지 경로 확인
echo $ROS_PACKAGE_PATH
```

---

## 📊 변환 체크리스트

변환 완료 후 확인:

- [ ] ✅ `import rospy` (not rclpy)
- [ ] ✅ `rospy.init_node()` (not super().__init__())
- [ ] ✅ `rospy.Publisher()` (not create_publisher())
- [ ] ✅ `rospy.Subscriber()` (not create_subscription())
- [ ] ✅ `rospy.Timer()` (not create_timer())
- [ ] ✅ Timer callback에 `event` 파라미터
- [ ] ✅ `rospy.loginfo()` (not get_logger().info())
- [ ] ✅ f-string → % formatting
- [ ] ✅ CMakeLists.txt 존재
- [ ] ✅ Launch 파일 XML 형식
- [ ] ✅ `catkin build` 성공
- [ ] ✅ `rospack find autorace_missions` 성공
- [ ] ✅ 개별 노드 실행 테스트
- [ ] ✅ 전체 launch 파일 실행 테스트

---

## 🎯 최종 확인

모든 것이 잘 작동하면:

```bash
# 성공적인 실행 예시
$ roslaunch autorace_missions full_autorace.launch

[INFO] [1700000000.000000]: 🏁 미션 매니저 시작 - 현재: COLORED_LANE
[INFO] [1700000000.100000]: 🎨 색깔 차로 미션 시작!
[INFO] [1700000000.200000]: 🚶 횡단보도 미션 노드 준비됨
[INFO] [1700000000.300000]: 🚧 라바콘 회피 미션 노드 준비됨
...
```

**축하합니다! 🎉 ROS1 변환 완료!**

---

## 📞 도움이 필요하면

변환 중 문제가 생기면:

1. 로그 확인: `roslaunch` 출력 메시지 읽기
2. 노드별 테스트: `rosrun`으로 개별 노드 실행
3. Python 문법 확인: `python3 -m py_compile <파일명>`
4. Git diff 확인: `git diff ros2-humble..ros1-noetic`
