# 🏁 AutoRace Missions Package (2025 국민대 WeBOT 대회)

2025 국민대 WeBOT 자율주행 대회를 위한 미션 관리 패키지입니다.

## 📋 대회 미션 구성

### 미션 1: 색깔 차로 감/가속 🎨
- **빨강 차로**: 감속 (0.08 m/s)
- **초록 차로**: 정상 속도 (0.15 m/s)
- **파랑 차로**: 가속 (0.22 m/s)
- HSV 색상 검출로 차로 색깔 인식

### 미션 2: 횡단보도 정지 후 출발 🚶
- 횡단보도 감지 시 **완전 정지**
- 3초 대기 후 재출발
- Hough 라인 검출로 횡단보도 줄무늬 인식

### 미션 3: 라바콘 회피 (LiDAR) 🚧
- **LiDAR 센서** 사용 (비전 X)
- 전방 장애물 감지 (0.4m 이내)
- 좌우 공간 비교해서 넓은 쪽으로 회피
- 3개 라바콘 통과 시 완료

### 미션 4: 차선 변경 (마커 감지) 🔄
- 파란색 화살표 마커 검출
- 좌/우 화살표 방향으로 차선 변경
- 3단계 기동: 대각이동 → 복귀 → 직진

### 미션 5: 회전 교차로 🔁
- 원형 차로 추적 (반시계방향)
- LiDAR로 동적 장애물 감지 및 회피
- 타이머 기반 탈출 (약 5초)

### 미션 6: 터널 암실 주행 🕳️
- 어두운 환경 감지 (brightness < 80)
- CLAHE 알고리즘으로 명암 대비 강화
- 저속 안전 주행 (0.12 m/s)

### 미션 7: 차단기 🚧
- 빨강/주황색 차단기 검출
- 각도 측정 (MinAreaRect)
- 60도 이상 열릴 때까지 대기
- 열리면 통과

### 미션 8: 주차 🅿️
- 빈 주차 공간 탐색
- 5단계 주차: 탐색 → 정렬 → 후진 → 주차 → 출차
- 수직 라인 검출로 주차선 인식

## 🚀 실행 방법

### 전체 미션 실행
```bash
ros2 launch autorace_missions full_autorace.launch.py
```

### 개별 미션 테스트
```bash
# 미션 매니저
ros2 run autorace_missions mission_manager

# 미션 1: 색깔 차로
ros2 run autorace_missions colored_lane

# 미션 2: 횡단보도
ros2 run autorace_missions crosswalk

# 미션 3: 라바콘 회피
ros2 run autorace_missions obstacle_avoidance

# 미션 4: 차선 변경
ros2 run autorace_missions lane_change

# 미션 5: 회전 교차로
ros2 run autorace_missions roundabout

# 미션 6: 터널
ros2 run autorace_missions tunnel

# 미션 7: 차단기
ros2 run autorace_missions barrier

# 미션 8: 주차
ros2 run autorace_missions parking
```

## 📡 토픽 구조

### Subscribe
- `/camera/image_raw` (sensor_msgs/Image): 카메라 영상
- `/scan` (sensor_msgs/LaserScan): LiDAR 데이터 (미션 3, 5)
- `/mission/current` (std_msgs/String): 현재 활성 미션

### Publish
- `/cmd_vel` (geometry_msgs/Twist): 차량 제어 명령
- `/mission/complete` (std_msgs/String): 미션 완료 신호
- `/vision/*_debug` (sensor_msgs/Image): 디버그 영상

## ⚙️ 설정 파일

`config/missions.yaml` 파일에서 각 미션의 파라미터를 조정할 수 있습니다:

```yaml
/colored_lane:
  ros__parameters:
    slow_speed: 0.08       # 빨강 차로 속도
    normal_speed: 0.15     # 초록 차로 속도
    fast_speed: 0.22       # 파랑 차로 속도

/obstacle_avoidance:
  ros__parameters:
    obstacle_distance: 0.4  # 장애물 감지 거리 (m)
    angular_speed: 0.5      # 회피 회전 속도

/barrier:
  ros__parameters:
    open_angle_threshold: 60  # 차단기 열림 각도 (도)
```

## 🎯 미션 진행 순서

```
COLORED_LANE (1)
    ↓
CROSSWALK (2)
    ↓
OBSTACLE_AVOIDANCE (3)
    ↓
LANE_CHANGE (4)
    ↓
ROUNDABOUT (5)
    ↓
TUNNEL (6)
    ↓
BARRIER (7)
    ↓
PARKING (8)
    ↓
FINISHED
```

## 🛠️ 센서 요구사항

- **카메라**: USB/CSI 카메라 (640x480 이상)
- **LiDAR**: 360도 스캔 (미션 3, 5에 필수)
- **IMU**: 선택사항 (회전 교차로에서 유용)

## 📊 디버그 모드

`debug_mode: true` 설정 시:
- 검출된 특징점 시각화
- 처리 상태 로그 출력
- `/vision/*_debug` 토픽으로 디버그 영상 발행

## ⚡ 실차 적용 시 주의사항

1. **속도 조정**: 시뮬레이션 대비 30-50% 감속 권장
2. **카메라 캘리브레이션**: `autorace_control/config/camera_calibration.yaml` 설정
3. **LiDAR 토픽 확인**: `/scan` 토픽 이름 일치 여부 확인
4. **모터 제어**: PWM 값 범위 튜닝 필요

자세한 실차 적용 가이드는 [`REAL_ROBOT_GUIDE.md`](../../REAL_ROBOT_GUIDE.md)를 참고하세요.

## 📝 라이선스

Apache-2.0

## 👨‍💻 Maintainer

- **junwon** (qownsdnjs@gmail.com)
- **2025 국민대 WeBOT 자율주행 대회**
