#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Galaxy - 主入口
===============

L4 级自主性智能系统

版本: v2.3.21
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# 设置项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("Galaxy")

# 导入 ASCII 艺术字
try:
    from core.ascii_art import print_galaxy
except ImportError:
    def print_galaxy(style="minimal"):
        print("GALAXY - L4 Autonomous Intelligence System")


def print_banner():
    """打印启动横幅"""
    print()
    print_galaxy("minimal")
    print()
    print("  启动中...")
    print()


def print_status():
    """打印系统状态"""
    print()
    print("  ═══════════════════════════════════════")
    print("  核心能力:")
    print("  ✅ AI 驱动 - 自然语言理解与生成")
    print("  ✅ 跨设备控制 - 控制手机、平板、电脑")
    print("  ✅ 自主学习 - 持续学习和知识积累")
    print("  ✅ 自主思考 - 元认知和目标分解")
    print("  ✅ 自主编程 - 代码生成和优化")
    print("  ✅ 知识库 - 知识存储和检索")
    print("  ✅ 数据库 - PostgreSQL, SQLite, Qdrant")
    print("  ═══════════════════════════════════════")
    print()
    print("  使用方式:")
    print("  • Dashboard: http://localhost:8080")
    print("  • Windows 客户端: python enhancements/clients/windows_client/run_ui.py")
    print("  • 按 F12 唤醒/隐藏客户端")
    print()
    print("  你可以随便说，我会自动理解并执行操作！")
    print()


def start_dashboard():
    """启动 Dashboard"""
    import uvicorn
    from dashboard.backend.main import app
    
    print_status()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )


def main():
    """主函数"""
    print_banner()
    
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  版本: v2.3.21")
    print()
    
    # 启动 Dashboard
    start_dashboard()


if __name__ == "__main__":
    main()
