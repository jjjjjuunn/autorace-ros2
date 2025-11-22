# 🛠️ AutoRace ROS2 → ROS1 변환 도구

2025 국민대 WeBOT 자율주행 대회를 위한 ROS2 Humble → ROS1 Noetic 자동 변환 도구 모음

---

## 📂 파일 구조

```
tools/
├── README.md                      # 이 파일
├── QUICK_START.md                 # 빠른 시작 가이드 ⭐
├── CONVERSION_GUIDE.md            # 상세 변환 가이드
│
├── convert_all_to_ros1.sh         # 🔥 원클릭 전체 변환 스크립트
├── convert_package_to_ros1.sh     # 개별 패키지 변환
└── ros2_to_ros1_converter.py      # Python 노드 변환기
```

---

## 🚀 빠른 실행

**한 줄로 전체 변환:**

```bash
./tools/convert_all_to_ros1.sh
```

**끝!** 5분 안에 ROS1 Noetic 버전 완성! 🎉

---

## 📖 사용 가이드

### 1️⃣ 전체 변환 (추천!)

```bash
cd /home/junwon/autorace_workspace
./tools/convert_all_to_ros1.sh
```

**변환 내용:**
- ✅ Python 노드: `rclpy` → `rospy`
- ✅ 빌드 시스템: `colcon` → `catkin`
- ✅ Launch 파일: Python → XML
- ✅ 패키지 구조: ROS2 → ROS1
- ✅ CMakeLists.txt 자동 생성
- ✅ 9개 미션 노드 모두 변환

---

### 2️⃣ 개별 패키지 변환

```bash
# 특정 패키지만 변환
./tools/convert_package_to_ros1.sh autorace_missions
./tools/convert_package_to_ros1.sh autorace_vision
```

---

### 3️⃣ 개별 Python 파일 변환

```bash
# 단일 노드 변환
python3 tools/ros2_to_ros1_converter.py \
  src/autorace_missions/autorace_missions/colored_lane.py \
  src/autorace_missions/nodes/colored_lane.py
```

---

## 🎯 변환 후 작업

### ✅ 1. 빌드 테스트

```bash
catkin build
source devel/setup.bash
```

### ✅ 2. 노드 실행 테스트

```bash
rosrun autorace_missions mission_manager.py
```

### ✅ 3. Launch 파일 테스트

```bash
roslaunch autorace_missions full_autorace.launch
```

### ✅ 4. Git 커밋

```bash
git add .
git commit -m "feat: Complete ROS1 Noetic conversion"
git push origin ros1-noetic
```

---

## 📚 상세 문서

- **[QUICK_START.md](QUICK_START.md)** - 빠른 시작 가이드 (원클릭 실행)
- **[CONVERSION_GUIDE.md](CONVERSION_GUIDE.md)** - 단계별 상세 가이드

---

## 🔍 주요 변환 내용

### Python API 변환

| ROS2 Humble | ROS1 Noetic |
|-------------|-------------|
| `import rclpy` | `import rospy` |
| `rclpy.init()` | `rospy.init_node()` |
| `create_publisher()` | `rospy.Publisher()` |
| `create_subscription()` | `rospy.Subscriber()` |
| `create_timer()` | `rospy.Timer()` |
| `get_logger().info()` | `rospy.loginfo()` |
| `get_parameter()` | `rospy.get_param()` |

### 빌드 시스템 변환

| ROS2 | ROS1 |
|------|------|
| `colcon build` | `catkin build` |
| `setup.py` (ament) | `CMakeLists.txt` (catkin) |
| `package.xml` (format 3) | `package.xml` (format 2) |

### Launch 파일 변환

**ROS2 (Python):**
```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package='pkg', executable='node', name='name')
    ])
```

**ROS1 (XML):**
```xml
<launch>
  <node pkg="pkg" type="node.py" name="name"/>
</launch>
```

---

## ⚠️ 수동 확인 필요

자동 변환 후 확인해야 할 것들:

1. **Timer callback** - `event` 파라미터 추가
   ```python
   # Before
   def callback(self):
       pass
   
   # After
   def callback(self, event):
       pass
   ```

2. **복잡한 f-string** - % formatting으로 변경
   ```python
   # Before
   rospy.loginfo(f'Value: {val}, State: {state}')
   
   # After
   rospy.loginfo('Value: %s, State: %s' % (val, state))
   ```

3. **파라미터 기본값** - `rospy.get_param()` 두 번째 인자 확인

---

## 🐛 트러블슈팅

### 문제: "No module named 'rclpy'"

```bash
grep -r "import rclpy" src/
# 발견된 파일 수정
```

### 문제: catkin build 실패

```bash
rm -rf build/ devel/
catkin init
catkin build
```

### 문제: Timer callback 에러

```bash
# callback에 event 파라미터 추가
grep -r "def.*_callback(self):" src/
```

---

## 📊 변환 프로세스

```
[ROS2 Humble]
    ↓
┌───────────────────────────────┐
│ convert_all_to_ros1.sh        │ ← 원클릭 실행
└───────────────────────────────┘
    ↓
┌───────────────────────────────┐
│ 1. 패키지 구조 변환            │
│    - CMakeLists.txt 생성       │
│    - package.xml 수정          │
└───────────────────────────────┘
    ↓
┌───────────────────────────────┐
│ 2. Python 노드 변환            │
│    - rclpy → rospy            │
│    - API 변경                  │
└───────────────────────────────┘
    ↓
┌───────────────────────────────┐
│ 3. Launch 파일 변환            │
│    - Python → XML             │
└───────────────────────────────┘
    ↓
┌───────────────────────────────┐
│ 4. 수동 검토                   │
│    - Timer callback 확인       │
│    - f-string 확인             │
└───────────────────────────────┘
    ↓
[ROS1 Noetic] ✅
```

---

## 🎯 대상 플랫폼

- **개발 환경**: Ubuntu 22.04 + ROS2 Humble
- **배포 환경**: Ubuntu 20.04 + ROS1 Noetic

---

## 📞 문의

변환 중 문제가 발생하면:

1. [QUICK_START.md](QUICK_START.md) 트러블슈팅 섹션 확인
2. [CONVERSION_GUIDE.md](CONVERSION_GUIDE.md) 상세 가이드 참조
3. Git Issues에 문의

---

## 📝 라이센스

Apache-2.0

---

**Happy Converting! 🚀**
