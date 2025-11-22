# 🚗 실차 적용 빠른 가이드

## 📋 핵심 변경사항 요약

### ✅ 이미 준비된 것
- ✅ 미션 알고리즘 (`autorace_missions`)
- ✅ 비전 검출 로직
- ✅ 미션 상태 관리

### ⚠️ 실차 적용 시 필요한 것

#### 1. **카메라 토픽 확인**
```bash
# 실차의 카메라 토픽 확인
ros2 topic list | grep camera

# 토픽이 다르다면 코드 수정
# 예: /usb_cam/image_raw, /camera/color/image_raw 등
```

**수정 방법**: 각 미션 노드에서
```python
# 기존
self.create_subscription(Image, '/camera/image_raw', ...)

# 실차에 맞게 변경
self.create_subscription(Image, '/usb_cam/image_raw', ...)
```

---

#### 2. **모터 제어 토픽 확인**
```bash
# 실차의 모터 제어 토픽 확인
ros2 topic list | grep cmd
ros2 topic list | grep motor
```

**토픽이 `/cmd_vel`이 아니라면**:
- 각 미션 노드의 `self.cmd_vel_pub` 수정 필요
- 또는 topic remapping 사용

```bash
# Launch 파일에서 remapping
ros2 run autorace_missions lane_following \
  --ros-args -r /cmd_vel:=/webot/cmd_vel
```

---

#### 3. **속도 파라미터 조정**

실차는 시뮬레이션보다 느리게!

**수정 파일**: `src/autorace_missions/config/missions.yaml`

```yaml
/lane_following:
  ros__parameters:
    linear_speed: 0.10      # 0.15 → 0.10 (느리게)
    angular_gain: 0.005     # 0.01 → 0.005 (부드럽게)

/stop_line:
  ros__parameters:
    stop_duration: 3.0
    detection_threshold: 0.4  # 0.3 → 0.4 (확실하게)

/crosswalk:
  ros__parameters:
    slow_speed: 0.04        # 0.05 → 0.04
    normal_speed: 0.10      # 0.15 → 0.10

/parking:
  ros__parameters:
    parking_speed: 0.05     # 0.08 → 0.05
    reverse_speed: -0.05    # -0.08 → -0.05

/tunnel:
  ros__parameters:
    tunnel_speed: 0.08      # 0.12 → 0.08
    brightness_threshold: 60  # 80 → 60 (실내 조명)

/intersection:
  ros__parameters:
    turn_speed: 0.06        # 0.10 → 0.06
    turn_duration: 3.0      # 2.0 → 3.0 (여유있게)
```

---

#### 4. **카메라 위치/각도 조정**

실차 카메라 마운트에 맞게 **ROI (Region of Interest) 조정**

**예시 - stop_line.py**:
```python
# 기존
roi_top = int(height * 0.7)  # 하단 30%

# 카메라가 더 낮게 설치되었다면
roi_top = int(height * 0.6)  # 하단 40%

# 카메라가 더 높게 설치되었다면
roi_top = int(height * 0.8)  # 하단 20%
```

---

#### 5. **조명 환경 재조정**

실제 환경의 조명에 맞게 **색상 검출 범위 조정**

**예시 - traffic_light.py**:
```python
# 현재 HSV 범위가 안 맞으면 rqt_image_view로 확인 후 조정
lower_red1 = np.array([0, 100, 100])   # 조정 필요 시
upper_red1 = np.array([10, 255, 255])

lower_green = np.array([40, 100, 100])  # 조정 필요 시
upper_green = np.array([80, 255, 255])
```

---

## 🚀 실차 테스트 절차

### 1단계: 하드웨어 연결 확인
```bash
# 카메라
ls /dev/video*

# 시리얼 포트 (모터 컨트롤러, IMU 등)
ls /dev/ttyUSB* /dev/ttyACM*
```

### 2단계: 토픽 확인
```bash
# 모든 토픽 목록
ros2 topic list

# 카메라 토픽 확인
ros2 topic hz /camera/image_raw

# 카메라 영상 확인
rqt_image_view
```

### 3단계: 단일 미션 테스트
```bash
# 차선 추적만 먼저 테스트
ros2 launch autorace_missions single_mission.launch.py \
  mission:=lane_following debug_mode:=true

# 다른 터미널에서 디버그 이미지 확인
rqt_image_view
# 토픽 선택: /vision/lane_debug
```

### 4단계: 파라미터 튜닝
```bash
# missions.yaml 수정
nano ~/autorace_workspace/src/autorace_missions/config/missions.yaml

# 재빌드 (Python이라 안 해도 되지만 launch 파일 변경 시)
cd ~/autorace_workspace
colcon build --packages-select autorace_missions
source install/setup.bash
```

### 5단계: 전체 시스템 실행
```bash
ros2 launch autorace_missions full_autorace.launch.py
```

---

## 🔧 자주 하는 수정

### A. 카메라 토픽 변경 (전체 미션)

**방법 1: 각 파일 수정**
```bash
# 모든 미션 파일 일괄 수정
cd ~/autorace_workspace/src/autorace_missions/autorace_missions
sed -i "s|'/camera/image_raw'|'/usb_cam/image_raw'|g" *.py
```

**방법 2: Topic Remapping (권장)**
```python
# launch/full_autorace.launch.py 수정
Node(
    package='autorace_missions',
    executable='lane_following',
    remappings=[
        ('/camera/image_raw', '/usb_cam/image_raw')
    ]
)
```

### B. 속도 제한 추가

각 미션 노드에 최대/최소 속도 제한:
```python
def limit_speed(self, speed, max_speed=0.15):
    return max(-max_speed, min(max_speed, speed))

# 사용
cmd.linear.x = self.limit_speed(desired_speed, max_speed=0.15)
```

### C. 안전 정지 기능

긴급 정지 버튼/신호 추가:
```python
# 각 미션 노드에 추가
self.create_subscription(Bool, '/emergency_stop', 
                        self.emergency_callback, 10)

def emergency_callback(self, msg):
    if msg.data:
        stop_cmd = Twist()
        stop_cmd.linear.x = 0.0
        stop_cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(stop_cmd)
        self.get_logger().warn('긴급 정지!')
```

---

## 📝 실차 체크리스트

### 하드웨어
- [ ] 카메라 연결 및 작동 확인
- [ ] 모터 드라이버 연결 확인
- [ ] IMU 센서 연결 (선택)
- [ ] 배터리 충전 상태 확인

### 소프트웨어
- [ ] 카메라 토픽 확인 및 수정
- [ ] 모터 토픽 확인 및 수정
- [ ] 속도 파라미터 실차용으로 조정
- [ ] 조명 환경에 맞게 HSV 재조정
- [ ] ROI 영역 카메라 각도에 맞게 조정

### 테스트
- [ ] 카메라 영상 정상 수신 확인
- [ ] 차선 추적 단독 테스트
- [ ] 정지선 검출 테스트
- [ ] 모든 미션 개별 테스트
- [ ] 전체 미션 통합 테스트

### 안전
- [ ] 긴급 정지 기능 테스트
- [ ] 최대 속도 제한 설정
- [ ] 테스트 공간 확보 (장애물 제거)
- [ ] 낙하 방지 (테이블 위 테스트 시)

---

## 🐛 문제 해결

### Q: 카메라 영상이 안 보여요
```bash
# 카메라 장치 확인
v4l2-ctl --list-devices

# 권한 문제
sudo chmod 666 /dev/video0

# 다른 프로그램이 사용 중인지 확인
lsof /dev/video0
```

### Q: 검출이 시뮬레이션보다 안 돼요
1. 조명 환경 확인 (밝기, 그림자)
2. 카메라 초점 맞춤 (1-2m 앞)
3. HSV 범위 재조정
4. 검출 임계값 낮춤 (`detection_threshold` 감소)

### Q: 차량이 너무 빨라요
- `missions.yaml`에서 모든 속도 값 0.7배로 줄이기
- `max_linear_speed` 파라미터 추가

### Q: 차량이 직진을 못 해요
- 좌우 모터 PWM 보정 필요 (하드웨어 문제)
- 또는 `angular_gain` 감소

---

## 📞 추가 도움

실차 적용 중 문제가 생기면:

1. **디버그 이미지 확인**: `rqt_image_view`로 검출 상태 확인
2. **로그 확인**: 터미널 출력 메시지 확인
3. **파라미터 조정**: 한 번에 하나씩 변경
4. **단계별 테스트**: 복잡한 거 말고 간단한 것부터

---

**안전 제일! 천천히 테스트하세요!** 🚗💨
