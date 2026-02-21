#!/usr/bin/env python3
"""
Galaxy Windows 客户端启动器
==========================

启动方式:
    python run_ui.py

功能:
    - F12 唤醒/隐藏
    - 书法卷轴式展开动画
    - 与 AI 智能体对话
    - 显示节点和工具状态

版本: v2.3.26
"""

import sys
import os

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

def check_dependencies():
    """检查依赖"""
    required = ['tkinter', 'keyboard', 'httpx']
    missing = []
    
    for pkg in required:
        if pkg == 'tkinter':
            try:
                import tkinter
            except ImportError:
                missing.append(pkg)
        else:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
    
    if missing:
        print(f"缺少依赖: {missing}")
        print("正在安装...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing, check=True)

def main():
    """主函数"""
    print("=" * 60)
    print("Galaxy Windows 客户端 v2.3.26")
    print("=" * 60)
    print()
    print("使用方式:")
    print("  F12 - 唤醒/隐藏面板")
    print("  ESC - 隐藏面板")
    print()
    print("功能:")
    print("  • 对话 - 与 AI 智能体对话")
    print("  • 模型 - 查看已配置的 LLM")
    print("  • 工具 - 查看工具 API")
    print("  • 节点 - 查看节点状态")
    print()
    print("=" * 60)
    
    check_dependencies()
    
    # 使用完整版客户端
    from galaxy_client import GalaxyClient
    
    # 从环境变量获取服务器地址
    server_url = os.environ.get('GALAXY_SERVER', 'http://localhost:8080')
    
    app = GalaxyClient(server_url=server_url)
    app.run()

if __name__ == "__main__":
    main()
