#!/bin/bash
# ROS2 패키지를 ROS1으로 변환하는 스크립트

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <package_name>"
    echo "Example: $0 autorace_missions"
    exit 1
fi

PACKAGE_NAME=$1
PACKAGE_DIR="src/${PACKAGE_NAME}"

if [ ! -d "$PACKAGE_DIR" ]; then
    echo "❌ Package not found: $PACKAGE_DIR"
    exit 1
fi

echo "🔄 Converting $PACKAGE_NAME to ROS1..."

# 1. setup.py → CMakeLists.txt + package.xml 변환
echo "📝 Creating CMakeLists.txt..."
cat > "${PACKAGE_DIR}/CMakeLists.txt" << 'EOF'
cmake_minimum_required(VERSION 3.0.2)
project(PACKAGE_NAME_PLACEHOLDER)

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

install(PROGRAMS
  # Python nodes will be listed here
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)

install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
)
EOF

sed -i "s/PACKAGE_NAME_PLACEHOLDER/${PACKAGE_NAME}/g" "${PACKAGE_DIR}/CMakeLists.txt"

# 2. setup.py에서 executables 추출하고 CMakeLists.txt에 추가
echo "📝 Extracting executable list from setup.py..."
if [ -f "${PACKAGE_DIR}/setup.py" ]; then
    # executables 추출
    EXECUTABLES=$(grep -A 20 "entry_points" "${PACKAGE_DIR}/setup.py" | \
                  grep -oP "'\K[^']+(?= =)" | \
                  sed 's/^/  nodes\//' | sed 's/$/.py/')
    
    # CMakeLists.txt에 추가
    sed -i "/# Python nodes will be listed here/a\\${EXECUTABLES}" "${PACKAGE_DIR}/CMakeLists.txt"
fi

# 3. package.xml 변경 (format 3 → format 2)
echo "📝 Converting package.xml to format 2..."
if [ -f "${PACKAGE_DIR}/package.xml" ]; then
    sed -i 's/format="3"/format="2"/' "${PACKAGE_DIR}/package.xml"
    sed -i 's/<depend>/<build_depend>/' "${PACKAGE_DIR}/package.xml"
    sed -i 's/<\/depend>/<\/build_depend>/' "${PACKAGE_DIR}/package.xml"
    
    # exec_depend 추가
    sed -i '/<build_depend>rospy<\/build_depend>/a\  <exec_depend>rospy<\/exec_depend>' "${PACKAGE_DIR}/package.xml"
fi

# 4. Python 노드들을 nodes/ 디렉토리로 이동
echo "📂 Reorganizing Python nodes..."
mkdir -p "${PACKAGE_DIR}/nodes"

# autorace_missions/*.py → nodes/*.py
if [ -d "${PACKAGE_DIR}/${PACKAGE_NAME}" ]; then
    for pyfile in "${PACKAGE_DIR}/${PACKAGE_NAME}"/*.py; do
        if [ -f "$pyfile" ] && [ "$(basename $pyfile)" != "__init__.py" ]; then
            cp "$pyfile" "${PACKAGE_DIR}/nodes/$(basename $pyfile)"
            chmod +x "${PACKAGE_DIR}/nodes/$(basename $pyfile)"
            echo "  Copied: $(basename $pyfile)"
        fi
    done
fi

# 5. Launch 파일 변환 (.launch.py → .launch XML)
echo "🚀 Converting launch files..."
if [ -d "${PACKAGE_DIR}/launch" ]; then
    for launch_py in "${PACKAGE_DIR}/launch"/*.launch.py; do
        if [ -f "$launch_py" ]; then
            base_name=$(basename "$launch_py" .launch.py)
            echo "  Converting: $base_name.launch.py → $base_name.launch"
            echo "  ⚠️  Manual conversion required for launch files!"
        fi
    done
fi

# 6. setup.py 백업 및 변환
if [ -f "${PACKAGE_DIR}/setup.py" ]; then
    mv "${PACKAGE_DIR}/setup.py" "${PACKAGE_DIR}/setup.py.ros2_backup"
    
    # ROS1용 setup.py 생성
    cat > "${PACKAGE_DIR}/setup.py" << EOF
#!/usr/bin/env python

from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=['${PACKAGE_NAME}'],
    package_dir={'': 'src'}
)

setup(**d)
EOF
fi

echo ""
echo "✅ Package structure converted!"
echo ""
echo "📋 Next steps:"
echo "   1. Review and edit CMakeLists.txt"
echo "   2. Manually convert Python nodes (use ros2_to_ros1_converter.py)"
echo "   3. Convert launch files to XML format"
echo "   4. Test build: catkin build ${PACKAGE_NAME}"
echo ""
echo "⚠️  Files to manually convert:"
ls -1 "${PACKAGE_DIR}/nodes/"
