#!/bin/bash
# AutoRace 빠른 테스트 스크립트

echo "🏁 AutoRace 미션 패키지 테스트"
echo "================================"

# 작업 디렉토리로 이동
cd ~/autorace_workspace

# 빌드
echo ""
echo "📦 패키지 빌드 중..."
colcon build --packages-select autorace_missions autorace_vision
if [ $? -ne 0 ]; then
    echo "❌ 빌드 실패!"
    exit 1
fi

# 소스
source install/setup.bash

echo ""
echo "✅ 빌드 완료!"
echo ""
echo "🎯 사용 가능한 명령어:"
echo ""
echo "1. 전체 미션 실행:"
echo "   ros2 launch autorace_missions full_autorace.launch.py"
echo ""
echo "2. 단일 미션 테스트:"
echo "   ros2 launch autorace_missions single_mission.launch.py mission:=stop_line"
echo ""
echo "3. 개별 노드 실행:"
echo "   ros2 run autorace_missions mission_manager"
echo "   ros2 run autorace_missions lane_following"
echo "   ros2 run autorace_missions traffic_light"
echo "   ros2 run autorace_missions intersection"
echo "   ros2 run autorace_missions stop_line"
echo "   ros2 run autorace_missions crosswalk"
echo "   ros2 run autorace_missions parking"
echo "   ros2 run autorace_missions tunnel"
echo ""
echo "4. 디버그 이미지 확인:"
echo "   ros2 run rqt_image_view rqt_image_view"
echo ""
echo "================================"
