# 🏗️ AutoRace 미션 아키텍처

## 📐 시스템 구조

### 미션 관리 방식: **독립적 미션 노드 구조**

각 미션 노드가 **자체적으로 차선 추적 + 미션 로직**을 포함하는 독립 실행 방식입니다.

```
┌─────────────────────────────────────────────────────┐
│              mission_manager.py                      │
│  (미션 순서 관리 및 상태 전환)                         │
│  /mission/current 발행                               │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ colored_lane│  │  crosswalk  │  │   tunnel    │
│             │  │             │  │             │
│ 차선추적 +  │  │ 차선추적 +  │  │ 차선추적 +  │
│ 색상인식 +  │  │ 횡단보도    │  │ CLAHE      │
│ 속도제어    │  │ 정지/출발   │  │ 저속주행    │
└─────────────┘  └─────────────┘  └─────────────┘
```

### 핵심 원리

#### 1️⃣ **미션 매니저 (mission_manager.py)**
- 현재 활성 미션을 `/mission/current` 토픽으로 발행
- 미션 완료 신호(`/mission/complete`)를 받으면 다음 미션으로 전환
- 순서: COLORED_LANE → CROSSWALK → ... → PARKING → FINISHED

#### 2️⃣ **각 미션 노드**
모든 미션 노드는 다음 패턴을 따릅니다:

```python
class SomeMission(Node):
    def __init__(self):
        # Subscribe
        self.create_subscription(String, '/mission/current', ...)
        self.create_subscription(Image, '/camera/image_raw', ...)
        
        # Publish
        self.cmd_vel_pub = ...
        self.mission_complete_pub = ...
    
    def mission_callback(self, msg):
        if msg.data == 'MY_MISSION_NAME':
            self.mission_active = True  # 활성화
        else:
            self.mission_active = False  # 비활성화
    
    def image_callback(self, msg):
        if not self.mission_active:
            return  # 내 미션이 아니면 무시
        
        # 1. 차선 추적 (기본)
        lane_error = self.track_lane(image)
        
        # 2. 미션별 특수 로직
        if self.detect_special_feature(image):
            self.handle_mission_logic()
        
        # 3. 차량 제어
        self.control_vehicle(lane_error)
```

### 🔑 **왜 이 구조를 선택했나?**

#### ✅ **장점**
1. **미션 간 독립성**: 한 미션의 버그가 다른 미션에 영향 없음
2. **유연한 제어**: 각 미션이 최적화된 주행 전략 사용 가능
   - `colored_lane`: 빠른 속도 + 공격적 추적
   - `tunnel`: 느린 속도 + 안전 추적
   - `parking`: 정밀 제어
3. **디버깅 용이**: 개별 미션 노드 단독 실행 가능
4. **병렬 실행**: 모든 노드가 동시 실행되지만, 자신의 미션일 때만 동작

#### ⚠️ **단점**
1. 코드 중복: 각 노드에 차선 추적 코드 존재
2. 메모리 사용: 9개 노드가 모두 상주

---

## 📂 파일 역할

### **실제 대회용 노드**
- `mission_manager.py` - 미션 순서 관리
- `colored_lane.py` - 미션 1: 색깔 차로
- `crosswalk.py` - 미션 2: 횡단보도
- `obstacle_avoidance.py` - 미션 3: 라바콘 (LiDAR)
- `lane_change.py` - 미션 4: 차선 변경
- `roundabout.py` - 미션 5: 회전 교차로
- `tunnel.py` - 미션 6: 터널
- `barrier.py` - 미션 7: 차단기
- `parking.py` - 미션 8: 주차

### **테스트/백업용 노드**
- `lane_following.py` - 순수 차선 추적 (미션 없음)
  - 카메라 테스트
  - 차선 검출 알고리즘 검증
  - 실차 파라미터 튜닝

### **불필요한 노드 (삭제 가능)**
- `traffic_light.py` - 대회에 없는 미션
- `stop_line.py` - 대회에 없는 미션
- `intersection.py` - roundabout으로 대체됨

---

## 🚀 실행 방법

### 전체 대회 미션 실행
```bash
ros2 launch autorace_missions full_autorace.launch.py
```
→ 9개 노드 모두 실행, mission_manager가 순서 제어

### 개별 미션 테스트
```bash
# 1. 미션 매니저 실행 (필수)
ros2 run autorace_missions mission_manager --ros-args -p initial_mission:=COLORED_LANE

# 2. 테스트할 미션 노드 실행
ros2 run autorace_missions colored_lane
```

### 순수 차선 추적 테스트
```bash
ros2 run autorace_missions lane_following
```
→ 미션 없이 차선만 추적 (카메라 검증용)

---

## 🔀 대안 구조 (향후 개선 시)

### **계층적 구조 (Layered Architecture)**
```
lane_following (Base Layer) - 항상 실행
    ↓ /cmd_vel 발행
    
mission_override (Override Layer) - 미션 활성화 시
    ↓ /cmd_vel_override 발행
    
cmd_vel_mux (Multiplexer)
    ↓ priority 기반 토픽 선택
    ↓ /cmd_vel_final 발행
    
motor_controller
```

**장점**: 코드 재사용, 명확한 책임 분리  
**단점**: 복잡도 증가, 우선순위 충돌 가능성

---

## 📊 토픽 흐름도

```
/camera/image_raw (sensor_msgs/Image)
    ↓ (9개 노드 모두 Subscribe)
    
각 미션 노드
    ↓ (내 미션일 때만 처리)
    ↓
/cmd_vel (geometry_msgs/Twist)
    ↓ (하나의 노드만 발행)
    
/mission/complete (std_msgs/String)
    ↓
mission_manager
    ↓
/mission/current (std_msgs/String)
    ↓ (미션 변경)
```

---

## ⚙️ 파라미터 튜닝 우선순위

실차 적용 시 조정해야 할 파라미터:

1. **속도**: `slow_speed`, `normal_speed`, `fast_speed`
2. **회전 민감도**: `angular_gain`, `angular_speed`
3. **검출 임계값**: `obstacle_distance`, `marker_area_threshold`
4. **타이밍**: `roundabout_duration`, `stop_duration`

파일 위치: `config/missions.yaml`

---

**작성일**: 2025-11-21  
**작성자**: junwon (qownsdnjs@gmail.com)  
**대회**: 2025 국민대 WeBOT 자율주행 대회
