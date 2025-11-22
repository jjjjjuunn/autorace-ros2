#!/usr/bin/env python3
"""
ROS2 Python Node → ROS1 Python Node 자동 변환 스크립트

사용법:
    python3 ros2_to_ros1_converter.py <input_ros2_file.py> <output_ros1_file.py>
"""

import sys
import re


def convert_ros2_to_ros1(ros2_code):
    """ROS2 코드를 ROS1으로 변환"""
    
    ros1_code = ros2_code
    
    # 1. Shebang 변경
    ros1_code = ros1_code.replace('#!/usr/bin/env python3', '#!/usr/bin/env python')
    
    # 2. Import 변경
    ros1_code = ros1_code.replace('import rclpy', 'import rospy')
    ros1_code = ros1_code.replace('from rclpy.node import Node', '')
    
    # 3. 클래스 정의 변경 (Node 상속 제거)
    ros1_code = re.sub(
        r'class (\w+)\(Node\):',
        r'class \1:',
        ros1_code
    )
    
    # 4. __init__ 내부 변경
    # super().__init__('node_name') → rospy.init_node('node_name')
    ros1_code = re.sub(
        r"super\(\).__init__\('(\w+)'\)",
        r"rospy.init_node('\1', anonymous=False)",
        ros1_code
    )
    
    # 5. 파라미터 변경
    # self.declare_parameter('param', default) 제거
    ros1_code = re.sub(
        r"self\.declare_parameter\('(\w+)',\s*([^)]+)\)\s*\n",
        r"",
        ros1_code
    )
    
    # self.get_parameter('param').value → rospy.get_param('~param', default)
    ros1_code = re.sub(
        r"self\.get_parameter\('(\w+)'\)\.value",
        r"rospy.get_param('~\1', self.\1_default)",
        ros1_code
    )
    
    # 6. Publisher 변경
    # self.create_publisher(Type, 'topic', 10) → rospy.Publisher('topic', Type, queue_size=10)
    ros1_code = re.sub(
        r"self\.create_publisher\((\w+),\s*'([^']+)',\s*(\d+)\)",
        r"rospy.Publisher('\2', \1, queue_size=\3)",
        ros1_code
    )
    
    # 7. Subscriber 변경
    # self.create_subscription(Type, 'topic', callback, 10)
    # → rospy.Subscriber('topic', Type, callback)
    ros1_code = re.sub(
        r"self\.create_subscription\((\w+),\s*'([^']+)',\s*\n?\s*self\.(\w+),\s*\d+\)",
        r"rospy.Subscriber('\2', \1, self.\3)",
        ros1_code
    )
    
    # 8. Timer 변경
    # self.create_timer(duration, callback) → rospy.Timer(rospy.Duration(duration), callback)
    ros1_code = re.sub(
        r"self\.create_timer\(([^,]+),\s*self\.(\w+)\)",
        r"rospy.Timer(rospy.Duration(\1), self.\2)",
        ros1_code
    )
    
    # 9. Logger 변경
    ros1_code = ros1_code.replace('self.get_logger().info(', 'rospy.loginfo(')
    ros1_code = ros1_code.replace('self.get_logger().warn(', 'rospy.logwarn(')
    ros1_code = ros1_code.replace('self.get_logger().error(', 'rospy.logerr(')
    
    # f-string을 % formatting으로 변경
    ros1_code = re.sub(
        r"rospy\.log(\w+)\(f'([^{]+)\{([^}]+)\}([^']+)'\)",
        r"rospy.log\1('\2%s\4' % \3)",
        ros1_code
    )
    
    # 10. Main 함수 변경
    old_main = r"""def main\(args=None\):
    rclpy\.init\(args=args\)
    node = (\w+)\(\)
    
    try:
        rclpy\.spin\(node\)
    except KeyboardInterrupt:
        pass
    finally:
        node\.destroy_node\(\)
        rclpy\.shutdown\(\)"""
    
    new_main = r"""def main():
    try:
        node = \1()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass"""
    
    ros1_code = re.sub(old_main, new_main, ros1_code, flags=re.MULTILINE | re.DOTALL)
    
    return ros1_code


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 ros2_to_ros1_converter.py <input_ros2.py> <output_ros1.py>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # ROS2 파일 읽기
    with open(input_file, 'r') as f:
        ros2_code = f.read()
    
    # 변환
    ros1_code = convert_ros2_to_ros1(ros2_code)
    
    # ROS1 파일 쓰기
    with open(output_file, 'w') as f:
        f.write(ros1_code)
    
    print(f"✅ Converted: {input_file} → {output_file}")
    print("⚠️  수동 검토 필요:")
    print("   - 파라미터 기본값 확인")
    print("   - Timer callback 시그니처 (event 인자 추가)")
    print("   - f-string 복잡한 경우 수동 수정")


if __name__ == '__main__':
    main()
