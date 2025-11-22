# AutoRace Missions Package

AutoRace 대회를 위한 미션별 알고리즘 패키지

## 📦 패키지 구조

```
autorace_workspace/
└── src/
    ├── autorace_missions/      # 미션 관리 패키지
    │   ├── autorace_missions/
    │   │   ├── mission_manager.py    # 미션 상태 관리
    │   │   ├── lane_following.py     # 차선 추적
    │   │   ├── traffic_light.py      # 신호등
    │   │   ├── stop_line.py          # 정지선
    │   │   └── crosswalk.py          # 횡단보도
    │   ├── config/
    │   │   └── missions.yaml         # 파라미터 설정
    │   └── launch/
    │       ├── full_autorace.launch.py     # 전체 미션
    │       └── single_mission.launch.py    # 단일 미션 테스트
    │
    ├── autorace_vision/        # 비전 유틸리티
    │   └── autorace_vision/
    │       ├── color_filter.py       # 색상 필터
    │       └── line_detector.py      # 라인 검출
    │
    ├── autorace_control/       # 제어 패키지 (기존)
    └── ros2_razor_imu/         # IMU 센서 (기존)
```

## 🚀 빠른 시작

### 1. 빌드

```bash
cd ~/autorace_workspace
colcon build --packages-select autorace_missions autorace_vision
source install/setup.bash
```

### 2. 전체 미션 실행

```bash
# 모든 미션 노드 동시 실행
ros2 launch autorace_missions full_autorace.launch.py

# 디버그 모드 끄고 실행
ros2 launch autorace_missions full_autorace.launch.py debug_mode:=false
```

### 3. 단일 미션 테스트

```bash
# 차선 추적만 테스트
ros2 launch autorace_missions single_mission.launch.py mission:=lane_following

# 신호등만 테스트
ros2 launch autorace_missions single_mission.launch.py mission:=traffic_light

# 교차로만 테스트
ros2 launch autorace_missions single_mission.launch.py mission:=intersection

# 정지선 미션만 테스트
ros2 launch autorace_missions single_mission.launch.py mission:=stop_line

# 횡단보도만 테스트
ros2 launch autorace_missions single_mission.launch.py mission:=crosswalk

# 주차만 테스트
ros2 launch autorace_missions single_mission.launch.py mission:=parking

# 터널만 테스트
ros2 launch autorace_missions single_mission.launch.py mission:=tunnel
```

## 📊 미션 순서

미션 매니저가 다음 순서로 미션을 자동 전환합니다:

1. **LANE_FOLLOWING** - 차선 추적 (기본 주행) ✅
2. **TRAFFIC_LIGHT** - 신호등 인식 ✅
3. **INTERSECTION** - 교차로 (좌/우회전/직진) ✅
4. **STOP_LINE** - 정지선 ✅
5. **CROSSWALK** - 횡단보도 ✅
6. **PARKING** - 주차 (후진 주차) ✅
7. **TUNNEL** - 터널 (어두운 환경) ✅
8. **FINISHED** - 완주

## 🎮 주요 토픽

### Published Topics

| 토픽 | 타입 | 설명 |
|------|------|------|
| `/mission/current` | `std_msgs/String` | 현재 활성 미션 이름 |
| `/mission/state` | `std_msgs/Int32` | 현재 미션 상태 (enum) |
| `/cmd_vel` | `geometry_msgs/Twist` | 속도 명령 |
| `/vision/lane_debug` | `sensor_msgs/Image` | 차선 디버그 이미지 |
| `/vision/traffic_light_debug` | `sensor_msgs/Image` | 신호등 디버그 이미지 |
| `/vision/intersection_debug` | `sensor_msgs/Image` | 교차로 디버그 이미지 |
| `/vision/stop_line_debug` | `sensor_msgs/Image` | 정지선 디버그 이미지 |
| `/vision/crosswalk_debug` | `sensor_msgs/Image` | 횡단보도 디버그 이미지 |
| `/vision/parking_debug` | `sensor_msgs/Image` | 주차 디버그 이미지 |
| `/vision/tunnel_debug` | `sensor_msgs/Image` | 터널 디버그 이미지 |

### Subscribed Topics

| 토픽 | 타입 | 설명 |
|------|------|------|
| `/camera/image_raw` | `sensor_msgs/Image` | 카메라 영상 |
| `/mission/complete` | `std_msgs/String` | 미션 완료 신호 |

## ⚙️ 파라미터 설정

`config/missions.yaml` 파일에서 미션별 파라미터 조정:

```yaml
/stop_line:
  ros__parameters:
    stop_duration: 3.0          # 정지 시간 (초)
    detection_threshold: 0.3    # 검출 민감도
    white_threshold: 200        # 흰색 이진화 임계값

/crosswalk:
  ros__parameters:
    slow_speed: 0.05           # 횡단보도 통과 속도
    normal_speed: 0.15         # 정상 주행 속도
    stripe_threshold: 3        # 최소 줄무늬 개수

/lane_following:
  ros__parameters:
    linear_speed: 0.15         # 직진 속도
    angular_gain: 0.01         # 조향 게인

/intersection:
  ros__parameters:
    turn_speed: 0.1            # 회전 속도
    turn_duration: 2.0         # 회전 지속 시간

/parking:
  ros__parameters:
    parking_speed: 0.08        # 주차 속도
    reverse_speed: -0.08       # 후진 속도

/tunnel:
  ros__parameters:
    tunnel_speed: 0.12         # 터널 내 속도
    brightness_threshold: 80   # 어두움 판단 임계값
```

파라미터 파일로 실행:

```bash
ros2 launch autorace_missions full_autorace.launch.py \
  --ros-args --params-file src/autorace_missions/config/missions.yaml
```

## 🐛 디버깅

### 1. 디버그 이미지 확인

```bash
# rqt_image_view 실행
ros2 run rqt_image_view rqt_image_view

# 또는 모든 토픽 보기
rqt
```

토픽 선택:
- `/vision/stop_line_debug` - 정지선 검출 시각화
- `/vision/crosswalk_debug` - 횡단보도 검출 시각화
- `/vision/lane_debug` - 차선 검출 시각화
- `/vision/traffic_light_debug` - 신호등 검출 시각화

### 2. 미션 상태 모니터링

```bash
# 현재 미션 확인
ros2 topic echo /mission/current

# 미션 완료 신호 확인
ros2 topic echo /mission/complete

# 속도 명령 확인
ros2 topic echo /cmd_vel
```

### 3. 수동 미션 전환 (테스트용)

```bash
# 특정 미션 완료 신호 발행
ros2 topic pub /mission/complete std_msgs/String "data: 'STOP_LINE'" --once
```

## 🔧 개발 가이드

### 새로운 미션 추가

1. **미션 노드 생성**

```python
# autorace_missions/new_mission.py
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class NewMission(Node):
    def __init__(self):
        super().__init__('new_mission')
        
        # 미션 활성화 체크
        self.create_subscription(String, '/mission/current', 
                               self.mission_callback, 10)
        
        # 미션 완료 발행
        self.complete_pub = self.create_publisher(String, '/mission/complete', 10)
    
    def mission_callback(self, msg):
        if msg.data == 'NEW_MISSION':
            self.execute_mission()
    
    def execute_mission(self):
        # 미션 로직
        pass
        
        # 완료 후
        complete_msg = String()
        complete_msg.data = 'NEW_MISSION'
        self.complete_pub.publish(complete_msg)

def main(args=None):
    rclpy.init(args=args)
    node = NewMission()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

2. **setup.py에 등록**

```python
entry_points={
    'console_scripts': [
        'new_mission = autorace_missions.new_mission:main',
    ],
}
```

3. **mission_manager.py에 추가**

```python
class MissionState(Enum):
    # ...
    NEW_MISSION = 9
```

## 📸 카메라 설정

카메라 토픽이 `/camera/image_raw`가 아닌 경우:

```bash
# 카메라 토픽 확인
ros2 topic list | grep image

# 코드에서 토픽 이름 변경
# 각 미션 파일의 self.create_subscription 부분 수정
```

## ✅ 체크리스트

실제 차량 테스트 전:

- [ ] 빌드 성공 확인
- [ ] 카메라 토픽 연결 확인 (`rostopic echo /camera/image_raw`)
- [ ] 단일 미션별로 테스트 (이미지 파일 또는 rosbag)
- [ ] 디버그 이미지로 검출 정확도 확인
- [ ] 파라미터 튜닝 (조명, 카메라 각도에 맞게)
- [ ] 제어 노드와 통합 테스트

## 🆘 문제 해결

### Q: 빌드 에러 - cv_bridge 못 찾음

```bash
sudo apt update
sudo apt install ros-humble-cv-bridge python3-opencv
```

### Q: 카메라 영상이 안 들어옴

```bash
# 카메라 노드 확인
ros2 node list

# 카메라 토픽 확인
ros2 topic list | grep camera

# 카메라 노드 재시작
```

### Q: 미션이 자동 전환이 안 됨

```bash
# mission_manager 노드 실행 여부 확인
ros2 node list | grep mission_manager

# 미션 완료 신호 확인
ros2 topic echo /mission/complete
```

## 📚 참고 자료

- [ROS 2 Humble 문서](https://docs.ros.org/en/humble/)
- [OpenCV Python 튜토리얼](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [TurtleBot3 AutoRace](https://emanual.robotis.com/docs/en/platform/turtlebot3/autonomous_driving/)

## 📝 라이센스

Apache-2.0

## 👥 개발자

- **junwon** - qownsdnjs@gmail.com

---

**Happy Racing! 🏁**
