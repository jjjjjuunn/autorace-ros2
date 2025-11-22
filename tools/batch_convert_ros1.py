#!/usr/bin/env python3
"""
ROS2→ROS1 일괄 변환 스크립트 (개선 버전)
들여쓰기 문제 없이 완벽하게 변환
"""

import os
import re
import sys


def convert_file(filepath):
    """파일 하나를 ROS1으로 변환"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Shebang
    content = content.replace('#!/usr/bin/env python3', '#!/usr/bin/env python')
    
    # 2. Import
    content = content.replace('import rclpy', 'import rospy')
    content = re.sub(r'from rclpy\.node import Node\n?', '', content)
    
    # 3. Class inheritance
    content = re.sub(r'class (\w+)\(Node\):', r'class \1:', content)
    
    # 4. super().__init__()
    content = re.sub(
        r"super\(\).__init__\('(\w+)'\)",
        r"rospy.init_node('\1', anonymous=False)",
        content
    )
    
    # 5. declare_parameter 라인 전체 삭제 (들여쓰기 유지)
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if 'declare_parameter' not in line:
            new_lines.append(line)
    content = '\n'.join(new_lines)
    
    # 6. get_parameter().value → rospy.get_param()
    # 기본값 추론: 변수명에서 추출
    def replace_get_param(match):
        param_name = match.group(1)
        var_name = match.group(2)
        # 기본값을 0.1로 설정 (나중에 수동 조정)
        return f"{var_name} = rospy.get_param('~{param_name}', 0.1)"
    
    content = re.sub(
        r"(\w+) = self\.get_parameter\('(\w+)'\)\.value",
        replace_get_param,
        content
    )
    
    # 7. Publisher
    content = re.sub(
        r"self\.create_publisher\((\w+),\s*'([^']+)',\s*(\d+)\)",
        r"rospy.Publisher('\2', \1, queue_size=\3)",
        content
    )
    
    # 8. Subscriber
    content = re.sub(
        r"self\.create_subscription\((\w+),\s*'([^']+)',\s*self\.(\w+),\s*(\d+)\)",
        r"rospy.Subscriber('\2', \1, self.\3, queue_size=\4)",
        content
    )
    
    # 9. Timer
    content = re.sub(
        r"self\.create_timer\(([^,]+),\s*self\.(\w+)\)",
        r"rospy.Timer(rospy.Duration(\1), self.\2)",
        content
    )
    
    # 10. Logger
    content = content.replace('self.get_logger().info(', 'rospy.loginfo(')
    content = content.replace('self.get_logger().warn(', 'rospy.logwarn(')
    content = content.replace('self.get_logger().error(', 'rospy.logerr(')
    
    # 11. Clock
    content = content.replace('self.get_clock().now().to_msg()', 'rospy.Time.now()')
    
    # 12. spin
    content = re.sub(
        r'rclpy\.spin\((\w+)\)',
        r'\1.run()',
        content
    )
    
    # 13. main 함수 수정
    content = re.sub(
        r'def main\(args=None\):.*?rclpy\.init\(args=args\)',
        'def main():\n    try:',
        content,
        flags=re.DOTALL
    )
    
    # 14. shutdown
    content = content.replace('rclpy.shutdown()', 'pass')
    content = content.replace('node.destroy_node()', '')
    
    # 15. ROSInterruptException
    content = re.sub(
        r'except KeyboardInterrupt:\s*pass',
        'except rospy.ROSInterruptException:\n        pass',
        content
    )
    
    return content


def main():
    workspace = '/home/junwon/autorace_workspace'
    
    # autorace_missions 노드들
    missions_dir = f'{workspace}/src/autorace_missions/autorace_missions'
    for filename in os.listdir(missions_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(missions_dir, filename)
            print(f'Converting {filepath}...')
            converted = convert_file(filepath)
            
            # nodes/ 디렉토리에 저장
            os.makedirs(f'{workspace}/src/autorace_missions/nodes', exist_ok=True)
            output_path = f'{workspace}/src/autorace_missions/nodes/{filename}'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(converted)
            os.chmod(output_path, 0o755)
            print(f'  → {output_path}')
    
    # autorace_vision 노드들
    vision_dir = f'{workspace}/src/autorace_vision/autorace_vision'
    for filename in os.listdir(vision_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(vision_dir, filename)
            print(f'Converting {filepath}...')
            converted = convert_file(filepath)
            
            # nodes/ 디렉토리에 저장
            os.makedirs(f'{workspace}/src/autorace_vision/nodes', exist_ok=True)
            output_path = f'{workspace}/src/autorace_vision/nodes/{filename}'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(converted)
            os.chmod(output_path, 0o755)
            print(f'  → {output_path}')
    
    print('\n✅ 변환 완료!')


if __name__ == '__main__':
    main()
