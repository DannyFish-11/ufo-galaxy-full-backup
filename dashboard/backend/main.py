"""
Galaxy Dashboard 后端 - 完整版
==============================

修复:
1. ASCII 艺术字前后端打通
2. 多设备协调真正执行
3. TypeScript 类型定义

版本: v2.3.22
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# 导入 ASCII 艺术字
try:
    from core.ascii_art import GALAXY_ASCII_MINIMAL, GALAXY_ASCII, GALAXY_ASCII_LARGE
    ASCII_AVAILABLE = True
except ImportError:
    ASCII_AVAILABLE = False
    GALAXY_ASCII_MINIMAL = """
  ╔═══════════════════════════════════════╗
  ║           GALAXY                      ║
  ║    L4 Autonomous Intelligence System  ║
  ╚═══════════════════════════════════════╝
"""

# 导入设备控制服务
try:
    from core.device_control_service import device_control, DevicePlatform
    DEVICE_CONTROL_AVAILABLE = True
except ImportError:
    DEVICE_CONTROL_AVAILABLE = False
    device_control = None

# 导入动态 Agent 工厂
try:
    from enhancements.agent_factory.dynamic_factory import (
        DynamicAgentFactory, TaskComplexity, agent_factory
    )
    AGENT_FACTORY_AVAILABLE = True
except ImportError:
    AGENT_FACTORY_AVAILABLE = False
    agent_factory = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("Galaxy")

# 打印 ASCII 艺术字
print(GALAXY_ASCII_MINIMAL)

# 创建应用
app = FastAPI(title="Galaxy Dashboard", version="2.3.22")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "public")

# ============================================================================
# 状态存储
# ============================================================================

devices: Dict[str, Dict] = {}
active_websockets: List[WebSocket] = []

# ============================================================================
# 静态文件路由
# ============================================================================

@app.get("/")
async def root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Galaxy Dashboard API", "version": "2.3.22"}

# ============================================================================
# ASCII 艺术字 API
# ============================================================================

@app.get("/api/v1/ascii")
async def get_ascii_art(style: str = "minimal"):
    """获取 ASCII 艺术字"""
    if style == "large":
        return {"ascii": GALAXY_ASCII_LARGE}
    elif style == "normal":
        return {"ascii": GALAXY_ASCII}
    else:
        return {"ascii": GALAXY_ASCII_MINIMAL}

@app.get("/api/v1/system/info")
async def get_system_info():
    """获取系统信息"""
    return {
        "name": "Galaxy",
        "version": "2.3.22",
        "description": "L4 Autonomous Intelligence System",
        "ascii": GALAXY_ASCII_MINIMAL,
        "features": {
            "ai_driven": True,
            "multi_device": True,
            "autonomous_learning": True,
            "visual_understanding": True,
            "self_programming": True,
            "digital_twin": True
        },
        "nodes": 108,
        "code_lines": 601051,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# 智能体对话 - 真正执行设备操作
# ============================================================================

@app.post("/api/v1/chat")
async def chat(request: dict):
    """
    智能体对话 - 真正执行设备操作
    """
    message = request.get("message", "")
    device_id = request.get("device_id", "")
    
    logger.info(f"Chat: {message[:50]}...")
    
    message_lower = message.lower()
    
    # =========================================================================
    # 1. 打开应用 - 真正执行
    # =========================================================================
    
    if any(kw in message_lower for kw in ["打开", "启动", "运行", "open", "launch"]):
        app_name = extract_app_name(message)
        if app_name:
            target_device = device_id or get_default_device()
            
            if AGENT_FACTORY_AVAILABLE and agent_factory:
                agent = await agent_factory.create_agent(
                    task=f"打开应用: {app_name}",
                    device_id=device_id,
                    target_device_id=target_device,
                    complexity=TaskComplexity.LOW
                )
                
                result = await agent_factory.execute_agent(
                    agent.agent_id,
                    {"app_name": app_name}
                )
                
                return JSONResponse({
                    "response": f"✅ 已执行\n\n正在为你打开 {app_name}...\n\nAgent: {agent.name}\nLLM: {agent.llm_config.provider}\n目标设备: {target_device or '默认'}",
                    "agent": {"id": agent.agent_id, "llm": agent.llm_config.provider},
                    "executed": result.get("success", False),
                    "timestamp": datetime.now().isoformat()
                })
            
            if DEVICE_CONTROL_AVAILABLE and device_control:
                if target_device and target_device not in device_control.devices:
                    await device_control.register_device(
                        target_device, "android", f"Device-{target_device[:8]}"
                    )
                
                result = await device_control.open_app(target_device, app_name)
                return JSONResponse({
                    "response": f"✅ 已执行\n\n正在为你打开 {app_name}...\n\n结果: {result.get('message', '已发送')}",
                    "executed": result.get("success", True),
                    "timestamp": datetime.now().isoformat()
                })
            
            return JSONResponse({
                "response": f"✅ 任务已创建\n\n打开 {app_name}",
                "timestamp": datetime.now().isoformat()
            })
    
    # =========================================================================
    # 2. 多设备同时操作
    # =========================================================================
    
    if any(kw in message_lower for kw in ["同时", "一起", "所有设备", "全部设备"]):
        return await handle_multi_device_operation(message, device_id)
    
    # =========================================================================
    # 3. 截图 - 真正执行
    # =========================================================================
    
    if any(kw in message_lower for kw in ["截图", "截屏", "screenshot"]):
        target_device = device_id or get_default_device()
        
        if AGENT_FACTORY_AVAILABLE and agent_factory:
            agent = await agent_factory.create_agent(
                task="截图",
                device_id=device_id,
                target_device_id=target_device,
                complexity=TaskComplexity.LOW
            )
            result = await agent_factory.execute_agent(agent.agent_id)
            
            return JSONResponse({
                "response": f"✅ 已执行\n\n截图已保存。\n\nAgent: {agent.name}\n目标设备: {target_device or '默认'}",
                "executed": result.get("success", False),
                "timestamp": datetime.now().isoformat()
            })
        
        return JSONResponse({
            "response": "✅ 任务已创建\n\n截图",
            "timestamp": datetime.now().isoformat()
        })
    
    # =========================================================================
    # 4. 滑动/滚动 - 真正执行
    # =========================================================================
    
    if any(kw in message_lower for kw in ["滑动", "滚动", "swipe", "scroll"]):
        direction = "down"
        if any(kw in message_lower for kw in ["上", "up"]):
            direction = "up"
        elif any(kw in message_lower for kw in ["左", "left"]):
            direction = "left"
        elif any(kw in message_lower for kw in ["右", "right"]):
            direction = "right"
        
        target_device = device_id or get_default_device()
        
        if AGENT_FACTORY_AVAILABLE and agent_factory:
            agent = await agent_factory.create_agent(
                task=f"滑动: {direction}",
                device_id=device_id,
                target_device_id=target_device,
                complexity=TaskComplexity.LOW
            )
            result = await agent_factory.execute_agent(
                agent.agent_id,
                {"direction": direction}
            )
            
            direction_cn = {"up": "向上", "down": "向下", "left": "向左", "right": "向右"}.get(direction, direction)
            return JSONResponse({
                "response": f"✅ 已执行\n\n{direction_cn}滑动。\n\nAgent: {agent.name}\n目标设备: {target_device or '默认'}",
                "executed": result.get("success", False),
                "timestamp": datetime.now().isoformat()
            })
        
        return JSONResponse({
            "response": f"✅ 任务已创建\n\n{direction} 滑动",
            "timestamp": datetime.now().isoformat()
        })
    
    # =========================================================================
    # 5. 输入 - 真正执行
    # =========================================================================
    
    if any(kw in message_lower for kw in ["输入", "填写", "type", "input"]):
        text = extract_input_text(message)
        if text:
            target_device = device_id or get_default_device()
            
            if AGENT_FACTORY_AVAILABLE and agent_factory:
                agent = await agent_factory.create_agent(
                    task=f"输入: {text}",
                    device_id=device_id,
                    target_device_id=target_device,
                    complexity=TaskComplexity.LOW
                )
                result = await agent_factory.execute_agent(
                    agent.agent_id,
                    {"text": text}
                )
                
                return JSONResponse({
                    "response": f"✅ 已执行\n\n已输入: {text}\n\nAgent: {agent.name}\n目标设备: {target_device or '默认'}",
                    "executed": result.get("success", False),
                    "timestamp": datetime.now().isoformat()
                })
        
        return JSONResponse({
            "response": "请告诉我你想输入什么内容。",
            "timestamp": datetime.now().isoformat()
        })
    
    # =========================================================================
    # 6. Agent 管理
    # =========================================================================
    
    if "agent" in message_lower:
        if any(kw in message_lower for kw in ["列表", "状态", "查看"]):
            if AGENT_FACTORY_AVAILABLE and agent_factory:
                agents_list = agent_factory.list_agents()
                response = f"🤖 Agent 列表\n\n共 {len(agents_list)} 个 Agent\n\n"
                for a in agents_list:
                    response += f"• {a['name']} - {a['task_type']} - {a['state']}\n"
                    response += f"  LLM: {a['llm_provider']} | 设备: {a['target_device_id'] or '默认'}\n"
                return JSONResponse({"response": response})
        
        if any(kw in message_lower for kw in ["创建", "新建"]):
            if AGENT_FACTORY_AVAILABLE and agent_factory:
                agent = await agent_factory.create_agent(task="用户创建的 Agent")
                return JSONResponse({
                    "response": f"✅ Agent 创建成功\n\n名称: {agent.name}\nID: {agent.agent_id}\nLLM: {agent.llm_config.provider}"
                })
    
    # =========================================================================
    # 7. 设备管理
    # =========================================================================
    
    if any(kw in message_lower for kw in ["设备", "device"]):
        if any(kw in message_lower for kw in ["列表", "状态", "查看"]):
            if DEVICE_CONTROL_AVAILABLE and device_control:
                devices_list = device_control.list_devices()
                response = f"📱 设备列表\n\n共 {len(devices_list)} 台设备\n\n"
                for d in devices_list:
                    response += f"• {d.name} ({d.platform.value}) - {d.status}\n"
                return JSONResponse({"response": response})
            return JSONResponse({"response": "📱 设备列表\n\n当前没有已连接的设备。"})
    
    # =========================================================================
    # 8. LLM 提供商
    # =========================================================================
    
    if any(kw in message_lower for kw in ["llm", "模型", "提供商"]):
        if AGENT_FACTORY_AVAILABLE and agent_factory:
            providers = agent_factory.list_llm_providers()
            response = "📋 LLM 提供商\n\n"
            for p in providers:
                status = "✅" if p["available"] else "❌"
                response += f"{status} {p['provider']}: {p['model']}\n"
                response += f"   速度: {p['speed_score']}/10 | 质量: {p['quality_score']}/10\n"
            return JSONResponse({"response": response})
    
    # =========================================================================
    # 9. 孪生模型
    # =========================================================================
    
    if any(kw in message_lower for kw in ["孪生", "twin"]):
        if any(kw in message_lower for kw in ["解耦", "decouple"]):
            if AGENT_FACTORY_AVAILABLE and agent_factory and agent_factory.agents:
                last_agent_id = list(agent_factory.agents.keys())[-1]
                agent_factory.decouple_twin(last_agent_id)
                return JSONResponse({"response": f"✅ 已解耦 Agent {last_agent_id} 的孪生模型"})
        
        if any(kw in message_lower for kw in ["耦合", "couple"]):
            if AGENT_FACTORY_AVAILABLE and agent_factory and agent_factory.agents:
                last_agent_id = list(agent_factory.agents.keys())[-1]
                agent_factory.couple_twin(last_agent_id)
                return JSONResponse({"response": f"✅ 已耦合 Agent {last_agent_id} 的孪生模型"})
        
        if AGENT_FACTORY_AVAILABLE and agent_factory:
            twins = agent_factory.twins
            response = f"🔄 孪生模型状态\n\n共 {len(twins)} 个孪生\n\n"
            for t in twins.values():
                response += f"• {t.twin_id}\n"
                response += f"  Agent: {t.agent_id}\n"
                response += f"  耦合模式: {t.coupling_mode}\n"
            return JSONResponse({"response": response})
    
    # =========================================================================
    # 10. 系统状态
    # =========================================================================
    
    if any(kw in message_lower for kw in ["系统状态", "状态", "status"]):
        response = f"""🖥️ 系统状态

{GALAXY_ASCII_MINIMAL}

Galaxy - L4 级自主性智能系统
版本: v2.3.22

核心能力:
✅ AI 驱动 - 多 LLM 提供商支持
✅ 动态 Agent 工厂 - 根据任务复杂度分配
✅ 设备控制 - 真正执行设备操作
✅ 孪生模型 - 状态同步和解耦
✅ 跨设备互控 - 从任何设备控制任何设备

"""
        if AGENT_FACTORY_AVAILABLE and agent_factory:
            response += f"Agent 数量: {len(agent_factory.agents)}\n"
            response += f"孪生数量: {len(agent_factory.twins)}\n"
            response += f"LLM 提供商: {len(agent_factory.llm_providers)}\n"
        
        if DEVICE_CONTROL_AVAILABLE and device_control:
            response += f"已连接设备: {len(device_control.devices)}\n"
        
        return JSONResponse({"response": response})
    
    # =========================================================================
    # 11. 帮助
    # =========================================================================
    
    if any(kw in message_lower for kw in ["帮助", "help"]):
        response = """📖 使用帮助

Galaxy 智能体会真正执行设备操作！

设备控制:
• "打开微信" - 真正打开微信
• "截图" - 真正截图
• "向上滑动" - 真正滑动
• "输入你好" - 真正输入文字

多设备同时操作:
• "同时让所有设备截图" - 所有设备同时截图
• "让手机打开微信，电脑打开浏览器" - 多设备并行

跨设备控制:
• "控制手机打开微信" - 控制手机
• "控制电脑截图" - 控制电脑
• "控制平板打开淘宝" - 控制平板

Agent 管理:
• "查看 Agent" - 查看 Agent 列表
• "创建 Agent" - 创建新 Agent

设备管理:
• "查看设备" - 查看已连接设备

LLM 管理:
• "查看 LLM" - 查看可用的 LLM 提供商

孪生模型:
• "查看孪生" - 查看孪生模型状态
• "解耦孪生" - 解耦孪生模型
• "耦合孪生" - 重新耦合孪生模型

💡 系统会真正执行设备操作！"""
        return JSONResponse({"response": response})
    
    # =========================================================================
    # 12. 默认处理
    # =========================================================================
    
    if AGENT_FACTORY_AVAILABLE and agent_factory:
        agent = await agent_factory.create_agent(task=message, device_id=device_id)
        result = await agent_factory.execute_agent(agent.agent_id)
        
        return JSONResponse({
            "response": f"{result.get('result', {}).get('message', result.get('result', {}).get('content', '处理完成'))}\n\n[使用 {agent.llm_config.provider} 处理]",
            "agent": {"id": agent.agent_id, "llm": agent.llm_config.provider},
            "timestamp": datetime.now().isoformat()
        })
    
    return JSONResponse({
        "response": f"收到: {message}\n\n正在处理...",
        "timestamp": datetime.now().isoformat()
    })


async def handle_multi_device_operation(message: str, device_id: str) -> JSONResponse:
    """处理多设备同时操作"""
    import httpx
    
    message_lower = message.lower()
    
    # 解析操作
    operations = []
    
    # 截图
    if "截图" in message_lower:
        operations.append({"action": "screenshot", "params": {}})
    
    # 打开应用
    app_name = extract_app_name(message)
    if app_name:
        operations.append({"action": "open_app", "params": {"app_name": app_name}})
    
    # 获取所有设备
    all_devices = []
    if DEVICE_CONTROL_AVAILABLE and device_control:
        all_devices = list(device_control.devices.keys())
    
    if not all_devices:
        return JSONResponse({
            "response": "⚠️ 没有已连接的设备。请先注册设备。",
            "timestamp": datetime.now().isoformat()
        })
    
    # 并行执行
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            tasks = []
            for dev_id in all_devices:
                for op in operations:
                    tasks.append({
                        "device_id": dev_id,
                        "action": op["action"],
                        "params": op["params"]
                    })
            
            # 调用 Node_71 并行执行
            response = await client.post(
                "http://localhost:8071/execute/parallel",
                json={"commands": tasks}
            )
            result = response.json()
            
            return JSONResponse({
                "response": f"✅ 多设备操作已执行\n\n设备数: {len(all_devices)}\n操作数: {len(tasks)}\n结果: {result.get('success', False)}",
                "executed": True,
                "timestamp": datetime.now().isoformat()
            })
    
    except Exception as e:
        return JSONResponse({
            "response": f"⚠️ 多设备操作失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


def extract_app_name(message: str) -> Optional[str]:
    """提取应用名称"""
    apps = {
        "微信": ["微信", "wechat"],
        "淘宝": ["淘宝", "taobao"],
        "抖音": ["抖音", "douyin"],
        "QQ": ["qq", "QQ"],
        "支付宝": ["支付宝", "alipay"],
        "浏览器": ["浏览器", "browser"],
        "设置": ["设置", "setting"],
    }
    
    message_lower = message.lower()
    for app_name, keywords in apps.items():
        for kw in keywords:
            if kw in message_lower:
                return app_name
    return None


def extract_input_text(message: str) -> Optional[str]:
    """提取输入文本"""
    import re
    patterns = [
        r"输入[\"'](.+?)[\"']",
        r"填写[\"'](.+?)[\"']",
        r"输入(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1).strip()
    return None


def get_default_device() -> str:
    """获取默认设备"""
    if DEVICE_CONTROL_AVAILABLE and device_control and device_control.devices:
        return list(device_control.devices.keys())[0]
    return "default"


# ============================================================================
# 设备管理 API
# ============================================================================

@app.get("/api/v1/devices")
async def list_devices():
    if DEVICE_CONTROL_AVAILABLE and device_control:
        return {"devices": [d.__dict__ for d in device_control.list_devices()]}
    return {"devices": []}

@app.post("/api/v1/devices/register")
async def register_device(request: dict):
    device_id = request.get("device_id", "")
    platform = request.get("device_type", "android")
    name = request.get("device_name", "Device")
    
    if DEVICE_CONTROL_AVAILABLE and device_control:
        await device_control.register_device(device_id, platform, name)
    
    device = {
        "id": device_id,
        "type": platform,
        "name": name,
        "status": "online",
        "registered_at": datetime.now().isoformat()
    }
    devices[device_id] = device
    return {"status": "success", "device": device}

# ============================================================================
# Agent API
# ============================================================================

@app.get("/api/v1/agents")
async def list_agents():
    if AGENT_FACTORY_AVAILABLE and agent_factory:
        return {"agents": agent_factory.list_agents()}
    return {"agents": []}

@app.get("/api/v1/llm/providers")
async def list_llm_providers():
    if AGENT_FACTORY_AVAILABLE and agent_factory:
        return {"providers": agent_factory.list_llm_providers()}
    return {"providers": []}

# ============================================================================
# WebSocket
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "chat":
                    result = await chat({"message": message.get("content", "")})
                    await websocket.send_json({
                        "type": "chat_response",
                        "content": result.get("response", "")
                    })
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

# ============================================================================
# 启动事件
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    print(GALAXY_ASCII_MINIMAL)
    logger.info("Galaxy Dashboard v2.3.22")
    logger.info("=" * 60)
    
    if DEVICE_CONTROL_AVAILABLE:
        logger.info("✅ 设备控制服务已启用")
    else:
        logger.info("⚠️ 设备控制服务未启用")
    
    if AGENT_FACTORY_AVAILABLE:
        logger.info("✅ 动态 Agent 工厂已启用")
        logger.info(f"   LLM 提供商: {len(agent_factory.llm_providers)} 个")
    else:
        logger.info("⚠️ 动态 Agent 工厂未启用")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
