#!/usr/bin/env python3
"""
UFO Galaxy - 统一启动脚本
========================

启动方式:
    python start_galaxy.py              # 启动 Dashboard (WebUI)
    python start_galaxy.py --desktop    # 启动桌面端 UI
    python start_galaxy.py --all        # 同时启动两者

功能:
    - 自动检测依赖
    - 自动加载配置
    - 自动启动服务
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

# 设置项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("Galaxy")


def check_dependencies():
    """检查依赖"""
    required = ['fastapi', 'uvicorn', 'httpx', 'pydantic']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        logger.error(f"缺少依赖: {missing}")
        logger.info("请运行: pip install " + " ".join(missing))
        return False
    
    return True


def init_system():
    """初始化系统"""
    logger.info("初始化系统...")
    
    # 加载配置
    from core.unified_config import config
    logger.info(f"配置加载完成: {len(config.get_all())} 项")
    
    # 初始化设备注册
    from core.device_registry import device_registry
    logger.info("设备注册管理器就绪")
    
    # 初始化通信管理
    from core.device_communication import device_comm
    logger.info("设备通信管理器就绪")
    
    # 初始化系统集成
    from core.system_integration import system
    asyncio.run(system.initialize())
    logger.info("系统集成层就绪")
    
    return True


def start_dashboard():
    """启动 Dashboard (WebUI)"""
    import uvicorn
    
    logger.info("启动 Dashboard...")
    
    # 使用 dashboard 的 main.py
    from dashboard.backend.main import app
    
    # 获取端口
    from core.unified_config import config
    port = config.get("web_ui_port", 8080)
    
    logger.info(f"Dashboard 地址: http://localhost:{port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


def start_desktop():
    """启动桌面端 UI"""
    logger.info("启动桌面端 UI...")
    
    # 检查平台
    if sys.platform != "win32":
        logger.warning("桌面端 UI 目前仅支持 Windows")
        return
    
    # 启动桌面端
    os.system(f"python {PROJECT_ROOT}/enhancements/clients/windows_client/run_ui.py")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='UFO Galaxy 启动器')
    parser.add_argument('--desktop', action='store_true', help='启动桌面端 UI')
    parser.add_argument('--all', action='store_true', help='同时启动 Dashboard 和桌面端')
    parser.add_argument('--port', type=int, default=8080, help='Dashboard 端口')
    args = parser.parse_args()
    
    print("=" * 60)
    print("UFO Galaxy - L4 级自主性智能系统")
    print("=" * 60)
    print()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 初始化系统
    if not init_system():
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("系统就绪")
    print("=" * 60)
    print()
    
    # 启动服务
    if args.all:
        # 同时启动（需要多进程）
        import multiprocessing
        p1 = multiprocessing.Process(target=start_dashboard)
        p2 = multiprocessing.Process(target=start_desktop)
        p1.start()
        p2.start()
        p1.join()
        p2.join()
    elif args.desktop:
        start_desktop()
    else:
        start_dashboard()


if __name__ == "__main__":
    main()
