# 🏁 AutoRace 2025 — 자율주행 스케일카 (Team WayFinder)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![ROS2](https://img.shields.io/badge/ROS2-Humble-blue) ![ROS1](https://img.shields.io/badge/ROS1-Noetic-blue)

2025 국민대학교 **AutoRace 자율주행 1/10 스케일카 경진대회** 출전 프로젝트.
ROS 기반 **인지·제어·미션 자율주행 스택**을 구현하고 실차(WeGo Ackermann)에 통합했습니다.

> *Autonomous 1/10-scale car for the 2025 Kookmin Univ. AutoRace. ROS2/ROS1, OpenCV & LiDAR perception, Ackermann (VESC) control, and an 8-mission autonomy pipeline.*

---

## 👥 팀 / 역할
- **팀 WayFinder** (5인) · 국민대학교 자동차융합대학
- **배준원(본인)**: 시스템 통합(Integration) · 자율주행 SW(ROS2) 풀스택 구현 · ROS2→ROS1 포팅

## 🛠️ 기술 스택
`ROS2 Humble` · `ROS1 Noetic` · `Python` · `OpenCV` · `LiDAR` · `Ackermann/VESC` · `Git`

## 🚗 플랫폼

| 구분 | 개발 환경 | 실차 |
|---|---|---|
| 미들웨어 | ROS2 Humble | ROS1 Noetic |
| 차량 모델 | 차동구동 mock | **WeGo Ackermann 조향** 1/10 카 |
| 구동 | `/cmd_vel` (Twist) | `/ackermann_cmd` → VESC |
| 센서 | mock 이미지 | `/usb_cam`, rplidar `/scan`, `/vesc/odom` |

## 🎯 미션 (8개, 순차 진행)

`색깔차로 → 횡단보도 → 라바콘 회피 → 갈림길 → 회전교차로 → 터널 → 차단기 → 주차`

| # | 미션 | 핵심 기법 | 센서 |
|---|---|---|---|
| 1 | 색깔 차로 감/가속 | HSV 색 검출 + 차선추적 | 카메라 |
| 2 | 횡단보도 정지 | 횡단보도 검출 → 정지/재출발 | 카메라 |
| 3 | 라바콘 회피 | LiDAR 섹터 분석 → 회피 | LiDAR |
| 4 | 갈림길(차선변경) | 화살표 마커 검출 → 좌/우 | 카메라 |
| 5 | 회전 교차로 | 동적 차량 회피 | 카메라+LiDAR |
| 6 | 터널 암실 | CLAHE 대비보정 + 저속 | 카메라 |
| 7 | 차단기 | 차단기 각도 검출 → 개방 시 통과 | 카메라 |
| 8 | 주차 | 표지판 인식 → 주차 | 카메라 |

## 🧩 아키텍처

```
mission_manager ──/mission/current──▶ [8개 미션 노드 동시 상주]
       ▲                                      │ (활성 미션만 동작)
       │                                      ▼
   /mission/complete ◀──────────────  /cmd_vel (Twist)
                                              │
                                       motor_controller
                                              ▼
                                   /ackermann_cmd → VESC
```
`mission_manager`가 미션 순서를 관리하고, 각 미션 노드가 자체 차선추적 + 미션 로직을 수행하는 **모듈식 독립 노드 구조**.

## 📊 결과 & 배운 점

- 실차에서 8개 미션 중 **4개(색깔차로·횡단보도·터널·차단기)를 통과**, 전체 시스템 통합은 시간 내 완성하지 못함.
- 사후 분석으로 얻은 핵심 교훈:
  1. **dev-on-target** — 알고리즘 정교화보다 *실차 타깃 스택에서 1일차부터 통합·검증*하는 것이 우선.
  2. **closed-loop 제어** — 프레임/시간 기반 open-loop 대신 오도메트리/IMU 피드백(pure pursuit 등).
  3. **통합-우선 + 현장 캘리브레이션** — 점진적 통합, 안전장치(estop/watchdog), 조명별 재캘리브레이션.
- 📄 자세한 개요: **[docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md)**

## 📂 저장소 구조

| 브랜치 | 내용 |
|---|---|
| `main` | 프로젝트 쇼케이스 (이 README + 개요 문서) |
| `ros1-noetic` | **실차 대회 최종 코드** (ROS1 Noetic / WeGo Ackermann) · 태그 `v2025-competition` |
| `ros2-humble` | 개발 코드 (ROS2 Humble) |

> 자율주행 패키지: `autorace_missions`(미션·제어) · `autorace_vision`(인지) · `autorace_control`(시뮬). 코드는 `ros1-noetic`/`ros2-humble` 브랜치 참조.

## 📄 License
[MIT](LICENSE)
