# 🚗 실차(Webot) 적용 가이드

## 📋 시뮬레이션 vs 실차 차이점

### 1. **하드웨어 토픽 차이**

| 구분 | 시뮬레이션 | 실차 (Webot) |
|------|-----------|--------------|
| 카메라 | Gazebo/RViz 가상 | USB/CSI 실제 카메라 |
| 모터 제어 | `/cmd_vel` (직접) | 모터 드라이버 필요 |
| 센서 | 완벽한 데이터 | 노이즈 존재 |
| 지연시간 | 없음 | 통신 지연 존재 |

---

## 🔧 필수 수정사항

### 1️⃣ **카메라 설정**

#### A. USB 카메라 연결 확인
```bash
# 카메라 장치 확인
ls -l /dev/video*

# 테스트
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

#### B. 카메라 노드 실행
```bash
# 실차용 카메라 노드
ros2 run autorace_control camera_node

# 이미지 확인
ros2 topic echo /camera/image_raw --once
rqt_image_view
```

---

### 2️⃣ **모터 제어 시스템**

#### A. 하드웨어 드라이버 확인
- Webot 차량의 모터 드라이버 확인
- 제조사 제공 ROS 2 패키지 설치

#### B. 토픽 매핑
```bash
# 실차 모터 토픽 확인
ros2 topic list | grep motor

# 예시:
# /motor/left
# /motor/right
# 또는
# /motor_cmd
```

#### C. motor_controller.py 수정
실차 하드웨어에 맞게 `publish_motor_commands()` 함수 수정:

```python
# 예시 1: 개별 모터 제어
self.left_motor_pub.publish(left_pwm)
self.right_motor_pub.publish(right_pwm)

# 예시 2: 통합 모터 명령 (하드웨어 드라이버에 따라)
# from webot_msgs.msg import MotorCommand
# motor_cmd = MotorCommand()
# motor_cmd.left = left_speed
# motor_cmd.right = right_speed
# self.motor_pub.publish(motor_cmd)
```

---

### 3️⃣ **속도 파라미터 조정**

시뮬레이션보다 **느리게, 부드럽게**:

```yaml
# config/real_robot.yaml
/lane_following:
  linear_speed: 0.12        # 0.15 → 0.12
  angular_gain: 0.008       # 0.01 → 0.008

/parking:
  parking_speed: 0.06       # 0.08 → 0.06
```

**이유**:
- 실차는 관성, 마찰 존재
- 급격한 방향 전환 시 미끄러짐
- 안전을 위해 천천히

---

### 4️⃣ **카메라 캘리브레이션**

#### A. 캘리브레이션 실행
```bash
# ROS 2 카메라 캘리브레이션 패키지
sudo apt install ros-humble-camera-calibration

# 체스보드 패턴 준비 (9x6)
ros2 run camera_calibration cameracalibrator \
  --size 8x6 --square 0.024 \
  --ros-args -r image:=/camera/image_raw
```

#### B. 캘리브레이션 파일 저장
```bash
# 저장된 파일 위치 확인
~/.ros/camera_info/

# 이동
cp ~/.ros/camera_info/camera.yaml \
  ~/autorace_workspace/src/autorace_control/config/camera_calibration.yaml
```

#### C. 캘리브레이션 적용
```python
# camera_node.py에서 자동 로드
self.load_calibration('config/camera_calibration.yaml')
```

---

### 5️⃣ **센서 노이즈 필터링**

실차는 센서 노이즈가 많아서 추가 필터링 필요:

```python
# 예시: 이동 평균 필터
class MovingAverageFilter:
    def __init__(self, window_size=5):
        self.window = []
        self.window_size = window_size
    
    def update(self, value):
        self.window.append(value)
        if len(self.window) > self.window_size:
            self.window.pop(0)
        return sum(self.window) / len(self.window)

# 각 미션 노드에 적용
self.error_filter = MovingAverageFilter(window_size=5)
filtered_error = self.error_filter.update(error)
```

---

### 6️⃣ **안전 기능 추가**

#### A. 긴급 정지
```python
# motor_controller.py에 추가
self.create_subscription(Bool, '/emergency_stop', 
                        self.emergency_stop_callback, 10)

def emergency_stop_callback(self, msg):
    if msg.data:
        self.publish_motor_commands(0.0, 0.0)
        self.get_logger().warn('긴급 정지!')
```

#### B. 타임아웃 (통신 끊김 대비)
```python
# 마지막 cmd_vel 수신 시간 체크
self.last_cmd_time = self.get_clock().now()

def cmd_vel_callback(self, msg):
    self.last_cmd_time = self.get_clock().now()
    # ...

# 타이머로 체크
def check_timeout(self):
    time_diff = (self.get_clock().now() - self.last_cmd_time).nanoseconds / 1e9
    if time_diff > 1.0:  # 1초 이상 수신 없으면
        self.publish_motor_commands(0.0, 0.0)
        self.get_logger().warn('cmd_vel 타임아웃! 정지')
```

---

## 🚀 실차 실행 순서

### 1. **하드웨어 연결 확인**
```bash
# 카메라
ls /dev/video*

# 모터 컨트롤러 (USB 시리얼)
ls /dev/ttyUSB* /dev/ttyACM*

# IMU
ls /dev/ttyUSB*
```

### 2. **권한 설정**
```bash
# 사용자를 dialout 그룹에 추가 (시리얼 통신)
sudo usermod -a -G dialout $USER
sudo reboot  # 재부팅 필요
```

### 3. **패키지 빌드**
```bash
cd ~/autorace_workspace
colcon build --packages-select autorace_control autorace_missions
source install/setup.bash
```

### 4. **단계별 테스트**

#### Step 1: 카메라만 실행
```bash
ros2 run autorace_control camera_node
# 다른 터미널에서 확인
rqt_image_view
```

#### Step 2: 모터 제어 테스트
```bash
# 모터 제어 노드 실행
ros2 run autorace_control motor_controller

# 다른 터미널에서 수동 제어
ros2 topic pub /cmd_vel geometry_msgs/Twist \
  "{linear: {x: 0.1}, angular: {z: 0.0}}" --once
```

#### Step 3: 단일 미션 테스트
```bash
# 차선 추적만
ros2 launch autorace_missions single_mission.launch.py mission:=lane_following
```

#### Step 4: 전체 시스템 실행
```bash
ros2 launch autorace_control real_robot.launch.py
```

---

## ⚙️ 실차 튜닝 체크리스트

### 카메라
- [ ] 초점 맞춤 (1-2m 앞)
- [ ] 각도 조정 (하향 15-30도)
- [ ] 조명 보정 (자동 노출 ON)
- [ ] 캘리브레이션 완료

### 모터
- [ ] PWM 범위 확인
- [ ] 최대 속도 테스트
- [ ] 좌우 균형 확인 (직진 테스트)
- [ ] 긴급 정지 동작 확인

### 미션 파라미터
- [ ] 속도 파라미터 실차용 조정
- [ ] 검출 임계값 재조정
- [ ] ROI 영역 실차 카메라에 맞게
- [ ] 각 미션별 개별 테스트 완료

### 안전
- [ ] 긴급 정지 버튼 테스트
- [ ] 통신 끊김 시 자동 정지 확인
- [ ] 최대 속도 제한 설정
- [ ] 장애물 충돌 방지 (선택)

---

## 🐛 실차 문제 해결

### Q1: 카메라 영상이 안 나와요
```bash
# 권한 확인
ls -l /dev/video0

# 테스트
cheese  # GUI 카메라 앱
ffplay /dev/video0
```

### Q2: 모터가 안 움직여요
```bash
# 시리얼 권한 확인
sudo chmod 666 /dev/ttyUSB0

# 모터 드라이버 상태 확인
ros2 topic echo /motor/left
```

### Q3: 차량이 직진을 못 해요
- 좌우 모터 PWM 보정 필요
- `motor_controller.py`에 캘리브레이션 계수 추가

### Q4: 검출이 시뮬레이션보다 안 돼요
- 조명 환경 다름 → HSV 범위 재조정
- 카메라 위치/각도 재조정
- 검출 임계값 낮춤 (더 민감하게)

---

## 📚 추가 참고사항

### 하드웨어 사양 확인 필요
1. **모터 드라이버 타입**: PWM? Serial? CAN?
2. **카메라 인터페이스**: USB? CSI?
3. **통신 프로토콜**: UART? I2C? SPI?
4. **전원**: 배터리 전압, 용량

### 제조사 문서 확인
- Webot 차량 매뉴얼
- 모터 드라이버 사양서
- ROS 2 패키지 (제공되는 경우)

---

**실차 테스트는 안전하게!** 🚗💨
