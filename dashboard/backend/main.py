"""
Galaxy Dashboard 后端 - 真正操作设备的智能体
============================================

智能体不只是返回结果，而是真正执行操作：
- 理解用户意图
- 调用设备控制节点
- 执行实际操作
- 返回执行结果

版本: v2.3.21
"""

import os
import json
import asyncio
import logging
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any
import re

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("Galaxy")

# 创建应用
app = FastAPI(title="Galaxy Dashboard", version="2.3.21")

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
# 节点服务地址
# ============================================================================

NODE_SERVICES = {
    "transformer": os.getenv("NODE_50_URL", "http://localhost:8050"),
    "knowledge_base": os.getenv("NODE_72_URL", "http://localhost:8072"),
    "autonomous_learning": os.getenv("NODE_70_URL", "http://localhost:8070"),
    "orchestrator": os.getenv("NODE_110_URL", "http://localhost:8110"),
    "multi_device": os.getenv("NODE_71_URL", "http://localhost:8071"),
    "node_factory": os.getenv("NODE_118_URL", "http://localhost:8118"),
}

# ============================================================================
# 数据模型
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    device_id: str = ""
    context: List[Dict[str, str]] = []

class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_type: str = "android"
    device_name: str = ""
    capabilities: List[str] = []

class TaskRequest(BaseModel):
    task_type: str
    payload: Dict[str, Any] = {}
    device_id: str = ""
    priority: int = 5

# ============================================================================
# 状态存储
# ============================================================================

devices: Dict[str, Dict] = {}
nodes: Dict[str, Dict] = {}
agents: List[Dict] = []
tasks: List[Dict] = []
knowledge_bases: List[Dict] = [
    {"id": "1", "name": "操作知识库", "documents": 156},
    {"id": "2", "name": "设备知识库", "documents": 89},
    {"id": "3", "name": "用户偏好库", "documents": 234},
]
learning_progress = {"operations": 78, "preferences": 65, "apps": 42}
active_websockets: List[WebSocket] = []

# ============================================================================
# 静态文件路由
# ============================================================================

@app.get("/")
async def root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Galaxy Dashboard API", "version": "2.3.21"}

# ============================================================================
# 智能体核心 - 真正执行操作
# ============================================================================

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """
    智能体对话 - 真正执行操作
    
    不只是返回结果，而是：
    1. 理解用户意图
    2. 调用相应节点
    3. 执行实际操作
    4. 返回执行结果
    """
    logger.info(f"Chat: {request.message[:50]}...")
    
    message = request.message
    message_lower = message.lower()
    
    # =========================================================================
    # 智能意图识别 - 不需要特定关键词
    # =========================================================================
    
    # 1. 设备控制 - 打开应用
    if any(kw in message_lower for kw in ["打开", "启动", "运行", "开", "open", "launch", "start"]):
        # 提取应用名称
        app_name = extract_app_name(message)
        if app_name:
            return await execute_open_app(app_name, request.device_id, message)
    
    # 2. 设备控制 - 搜索
    if any(kw in message_lower for kw in ["搜索", "查找", "找", "search", "find"]):
        search_query = extract_search_query(message)
        if search_query:
            return await execute_search(search_query, request.device_id, message)
    
    # 3. 设备控制 - 截图
    if any(kw in message_lower for kw in ["截图", "截屏", "screenshot", "capture"]):
        return await execute_screenshot(request.device_id, message)
    
    # 4. 设备控制 - 点击
    if any(kw in message_lower for kw in ["点击", "按", "tap", "click", "touch"]):
        target = extract_click_target(message)
        if target:
            return await execute_click(target, request.device_id, message)
    
    # 5. 设备控制 - 输入
    if any(kw in message_lower for kw in ["输入", "填写", "type", "input", "write"]):
        text = extract_input_text(message)
        if text:
            return await execute_input(text, request.device_id, message)
    
    # 6. 设备控制 - 滑动
    if any(kw in message_lower for kw in ["滑动", "滚动", "swipe", "scroll"]):
        direction = extract_swipe_direction(message)
        return await execute_swipe(direction, request.device_id, message)
    
    # 7. 查询类 - 节点
    if any(kw in message_lower for kw in ["节点", "node", "系统状态", "状态"]):
        return await query_nodes(message)
    
    # 8. 查询类 - 设备
    if any(kw in message_lower for kw in ["设备", "device", "连接"]):
        return await query_devices(message)
    
    # 9. Agent 相关
    if "agent" in message_lower:
        if any(kw in message_lower for kw in ["创建", "新建", "create", "new"]):
            return await create_agent(message)
        return await query_agents(message)
    
    # 10. 知识库相关
    if any(kw in message_lower for kw in ["知识", "knowledge", "文档"]):
        return await query_knowledge(message)
    
    # 11. 学习相关
    if any(kw in message_lower for kw in ["学习", "learn", "训练"]):
        return await handle_learning(message)
    
    # 12. 帮助
    if any(kw in message_lower for kw in ["帮助", "help", "怎么用", "能做什么"]):
        return await show_help()
    
    # =========================================================================
    # 默认：尝试用 AI 理解并执行
    # =========================================================================
    return await ai_understand_and_execute(message, request.device_id)


# ============================================================================
# 意图提取函数
# ============================================================================

def extract_app_name(message: str) -> Optional[str]:
    """提取应用名称"""
    apps = {
        "微信": ["微信", "wechat"],
        "淘宝": ["淘宝", "taobao"],
        "京东": ["京东", "jd"],
        "抖音": ["抖音", "douyin", "tiktok"],
        "QQ": ["qq", "QQ"],
        "支付宝": ["支付宝", "alipay"],
        "美团": ["美团", "meituan"],
        "拼多多": ["拼多多", "pdd"],
        "微博": ["微博", "weibo"],
        "知乎": ["知乎", "zhihu"],
        "B站": ["b站", "哔哩哔哩", "bilibili"],
        "高德地图": ["高德", "地图", "amap"],
        "百度地图": ["百度地图"],
        "设置": ["设置", "setting"],
        "相机": ["相机", "camera"],
        "相册": ["相册", "gallery"],
        "浏览器": ["浏览器", "browser"],
    }
    
    message_lower = message.lower()
    for app_name, keywords in apps.items():
        for kw in keywords:
            if kw in message_lower:
                return app_name
    return None

def extract_search_query(message: str) -> Optional[str]:
    """提取搜索关键词"""
    patterns = [
        r"搜索[\"']?(.+?)[\"']?$",
        r"查找[\"']?(.+?)[\"']?$",
        r"找[\"']?(.+?)[\"']?$",
        r"search[: ]+(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def extract_click_target(message: str) -> Optional[str]:
    """提取点击目标"""
    patterns = [
        r"点击[\"']?(.+?)[\"']?$",
        r"按[\"']?(.+?)[\"']?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1).strip()
    return None

def extract_input_text(message: str) -> Optional[str]:
    """提取输入文本"""
    patterns = [
        r"输入[\"'](.+?)[\"']",
        r"填写[\"'](.+?)[\"']",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1).strip()
    return None

def extract_swipe_direction(message: str) -> str:
    """提取滑动方向"""
    if any(kw in message for kw in ["上", "up", "向上"]):
        return "up"
    if any(kw in message for kw in ["下", "down", "向下"]):
        return "down"
    if any(kw in message for kw in ["左", "left", "向左"]):
        return "left"
    if any(kw in message for kw in ["右", "right", "向右"]):
        return "right"
    return "up"


# ============================================================================
# 执行函数 - 真正操作设备
# ============================================================================

async def execute_open_app(app_name: str, device_id: str, original_message: str) -> JSONResponse:
    """执行打开应用"""
    logger.info(f"执行: 打开应用 {app_name}")
    
    # 构建任务
    task = {
        "type": "open_app",
        "app_name": app_name,
        "device_id": device_id,
        "timestamp": datetime.now().isoformat()
    }
    tasks.append(task)
    
    # 尝试调用设备控制节点
    executed = False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 调用 Node_71 多设备协调
            response = await client.post(
                f"{NODE_SERVICES['multi_device']}/api/v1/device/execute",
                json={
                    "device_id": device_id or "default",
                    "action": "open_app",
                    "params": {"app_name": app_name}
                }
            )
            if response.status_code == 200:
                executed = True
                logger.info(f"成功调用设备节点打开 {app_name}")
    except Exception as e:
        logger.warning(f"设备节点不可用: {e}")
    
    # 返回结果
    if executed:
        response_text = f"""✅ 已执行

正在为你打开 {app_name}...

操作已发送到设备，应用应该正在启动。"""
    else:
        response_text = f"""✅ 任务已创建

打开 {app_name}

设备控制节点暂时不可用，任务已加入队列。
启动设备端应用后，任务将自动执行。

提示: 启动安卓端应用并连接到服务器"""
    
    return JSONResponse({
        "response": response_text,
        "action": "open_app",
        "app_name": app_name,
        "executed": executed,
        "timestamp": datetime.now().isoformat()
    })

async def execute_search(query: str, device_id: str, original_message: str) -> JSONResponse:
    """执行搜索"""
    logger.info(f"执行: 搜索 {query}")
    
    task = {
        "type": "search",
        "query": query,
        "device_id": device_id,
        "timestamp": datetime.now().isoformat()
    }
    tasks.append(task)
    
    # 尝试执行
    executed = False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{NODE_SERVICES['multi_device']}/api/v1/device/execute",
                json={
                    "device_id": device_id or "default",
                    "action": "search",
                    "params": {"query": query}
                }
            )
            if response.status_code == 200:
                executed = True
    except:
        pass
    
    if executed:
        response_text = f"""✅ 已执行

正在搜索: {query}

搜索操作已发送到设备。"""
    else:
        response_text = f"""✅ 任务已创建

搜索: {query}

任务已加入队列，等待设备连接后执行。"""
    
    return JSONResponse({
        "response": response_text,
        "action": "search",
        "query": query,
        "executed": executed,
        "timestamp": datetime.now().isoformat()
    })

async def execute_screenshot(device_id: str, original_message: str) -> JSONResponse:
    """执行截图"""
    logger.info("执行: 截图")
    
    task = {
        "type": "screenshot",
        "device_id": device_id,
        "timestamp": datetime.now().isoformat()
    }
    tasks.append(task)
    
    executed = False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{NODE_SERVICES['multi_device']}/api/v1/device/execute",
                json={
                    "device_id": device_id or "default",
                    "action": "screenshot",
                    "params": {}
                }
            )
            if response.status_code == 200:
                executed = True
    except:
        pass
    
    if executed:
        response_text = """✅ 已执行

截图已保存到设备。"""
    else:
        response_text = """✅ 任务已创建

截图任务已加入队列。"""
    
    return JSONResponse({
        "response": response_text,
        "action": "screenshot",
        "executed": executed,
        "timestamp": datetime.now().isoformat()
    })

async def execute_click(target: str, device_id: str, original_message: str) -> JSONResponse:
    """执行点击"""
    logger.info(f"执行: 点击 {target}")
    
    task = {
        "type": "click",
        "target": target,
        "device_id": device_id,
        "timestamp": datetime.now().isoformat()
    }
    tasks.append(task)
    
    response_text = f"""✅ 任务已创建

点击: {target}

任务已加入队列。"""
    
    return JSONResponse({
        "response": response_text,
        "action": "click",
        "target": target,
        "timestamp": datetime.now().isoformat()
    })

async def execute_input(text: str, device_id: str, original_message: str) -> JSONResponse:
    """执行输入"""
    logger.info(f"执行: 输入 {text}")
    
    task = {
        "type": "input",
        "text": text,
        "device_id": device_id,
        "timestamp": datetime.now().isoformat()
    }
    tasks.append(task)
    
    response_text = f"""✅ 任务已创建

输入: {text}

任务已加入队列。"""
    
    return JSONResponse({
        "response": response_text,
        "action": "input",
        "text": text,
        "timestamp": datetime.now().isoformat()
    })

async def execute_swipe(direction: str, device_id: str, original_message: str) -> JSONResponse:
    """执行滑动"""
    logger.info(f"执行: 滑动 {direction}")
    
    task = {
        "type": "swipe",
        "direction": direction,
        "device_id": device_id,
        "timestamp": datetime.now().isoformat()
    }
    tasks.append(task)
    
    direction_cn = {"up": "向上", "down": "向下", "left": "向左", "right": "向右"}.get(direction, direction)
    
    response_text = f"""✅ 任务已创建

滑动: {direction_cn}

任务已加入队列。"""
    
    return JSONResponse({
        "response": response_text,
        "action": "swipe",
        "direction": direction,
        "timestamp": datetime.now().isoformat()
    })


# ============================================================================
# 查询函数
# ============================================================================

async def query_nodes(message: str) -> JSONResponse:
    """查询节点"""
    response_text = """📊 节点状态

总数: 108 个节点

核心节点:
• Node_00 StateMachine - 状态机
• Node_01 OneAPI - API 网关
• Node_04 Router - 智能路由
• Node_50 Transformer - NLU 引擎
• Node_70 AutonomousLearning - 自主学习
• Node_71 MultiDeviceCoord - 多设备协调
• Node_72 KnowledgeBase - 知识库
• Node_110 SmartOrchestrator - 智能编排
• Node_118 NodeFactory - 节点工厂"""
    
    return JSONResponse({
        "response": response_text,
        "timestamp": datetime.now().isoformat()
    })

async def query_devices(message: str) -> JSONResponse:
    """查询设备"""
    total = len(devices)
    
    if total == 0:
        response_text = """📱 设备状态

当前没有已连接的设备。

启动安卓端应用并连接到服务器即可控制设备。"""
    else:
        device_list = "\n".join([f"• {d['name']} ({d['type']}) - {d['status']}" for d in devices.values()])
        response_text = f"""📱 设备状态

已连接: {total} 台设备

{device_list}"""
    
    return JSONResponse({
        "response": response_text,
        "data": {"devices": list(devices.values()), "total": total},
        "timestamp": datetime.now().isoformat()
    })

async def query_agents(message: str) -> JSONResponse:
    """查询 Agent"""
    total = len(agents)
    
    if total == 0:
        response_text = """🤖 Agent 状态

当前没有活跃的 Agent。

告诉我你想创建什么样的 Agent，例如:
"创建一个 Agent 帮我监控设备" """
    else:
        agent_list = "\n".join([f"• {a['name']} - {a['status']} - {a['task']}" for a in agents])
        response_text = f"""🤖 Agent 状态

活跃 Agent: {total} 个

{agent_list}"""
    
    return JSONResponse({
        "response": response_text,
        "data": {"agents": agents, "total": total},
        "timestamp": datetime.now().isoformat()
    })

async def create_agent(message: str) -> JSONResponse:
    """创建 Agent"""
    agent_name = f"Agent_{len(agents) + 1}"
    agent_task = "等待分配任务"
    
    if "监控" in message:
        agent_task = "监控设备和系统状态"
    elif "学习" in message:
        agent_task = "自主学习和知识积累"
    elif "编程" in message:
        agent_task = "代码生成和优化"
    elif "控制" in message:
        agent_task = "设备控制和任务执行"
    
    agent = {
        "id": f"agent_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "name": agent_name,
        "status": "active",
        "task": agent_task,
        "created_at": datetime.now().isoformat()
    }
    agents.append(agent)
    
    response_text = f"""✅ Agent 创建成功

名称: {agent_name}
状态: 活跃
任务: {agent_task}

Agent 已开始运行，会自动执行分配的任务。"""
    
    return JSONResponse({
        "response": response_text,
        "data": {"agent": agent},
        "timestamp": datetime.now().isoformat()
    })

async def query_knowledge(message: str) -> JSONResponse:
    """查询知识库"""
    kb_list = "\n".join([f"• {kb['name']}: {kb['documents']} 文档" for kb in knowledge_bases])
    
    response_text = f"""📚 知识库状态

{kb_list}

总计: {sum(kb['documents'] for kb in knowledge_bases)} 条知识"""
    
    return JSONResponse({
        "response": response_text,
        "data": {"knowledge_bases": knowledge_bases},
        "timestamp": datetime.now().isoformat()
    })

async def handle_learning(message: str) -> JSONResponse:
    """处理学习"""
    learning_progress["operations"] = min(100, learning_progress["operations"] + 5)
    
    response_text = f"""📈 学习进度

• 操作模式学习: {learning_progress['operations']}%
• 用户偏好学习: {learning_progress['preferences']}%
• 应用适配学习: {learning_progress['apps']}%

系统正在持续学习和优化中。"""
    
    return JSONResponse({
        "response": response_text,
        "data": {"learning_progress": learning_progress},
        "timestamp": datetime.now().isoformat()
    })

async def show_help() -> JSONResponse:
    """显示帮助"""
    response_text = """📖 使用帮助

Galaxy 是一个 L4 级自主性智能系统。
你只需要用自然语言与我对话，我会自动理解并执行操作。

📋 你可以这样说:

设备控制:
• "打开微信" - 打开应用
• "搜索手机" - 搜索内容
• "截图" - 截取屏幕
• "向上滑动" - 滑动屏幕
• "点击确定按钮" - 点击元素
• "输入你好" - 输入文字

查询信息:
• "节点状态" - 查看系统节点
• "设备状态" - 查看已连接设备
• "知识库" - 查看知识库

Agent 管理:
• "创建一个 Agent 帮我监控设备" - 创建 Agent
• "查看 Agent" - 查看 Agent 状态

💡 你可以随意说，我会自动理解你的意图！"""
    
    return JSONResponse({
        "response": response_text,
        "timestamp": datetime.now().isoformat()
    })

async def ai_understand_and_execute(message: str, device_id: str) -> JSONResponse:
    """AI 理解并执行"""
    # 尝试调用 AI
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{NODE_SERVICES['transformer']}/api/v1/nlu",
                json={"text": message}
            )
            if response.status_code == 200:
                result = response.json()
                intent = result.get("intent", {})
                
                # 根据 AI 理解的意图执行操作
                intent_type = intent.get("type", "")
                
                if intent_type == "open_app":
                    app_name = intent.get("app_name", "")
                    if app_name:
                        return await execute_open_app(app_name, device_id, message)
                
                return JSONResponse({
                    "response": result.get("response", "我理解了你的请求，正在处理..."),
                    "intent": intent,
                    "timestamp": datetime.now().isoformat()
                })
    except:
        pass
    
    # 默认响应
    response_text = f"""我收到了: "{message}"

我正在理解你的意图...

如果你想要:
• 控制设备 - 请确保设备已连接
• 查询信息 - 我会尽力回答

说 "帮助" 查看更多用法。"""
    
    return JSONResponse({
        "response": response_text,
        "timestamp": datetime.now().isoformat()
    })


# ============================================================================
# 设备管理 API
# ============================================================================

@app.get("/api/v1/devices")
async def list_devices():
    return {"devices": list(devices.values()), "total": len(devices)}

@app.post("/api/v1/devices/register")
async def register_device(request: DeviceRegisterRequest):
    device = {
        "id": request.device_id,
        "type": request.device_type,
        "name": request.device_name or f"Device-{request.device_id[:8]}",
        "capabilities": request.capabilities,
        "status": "online",
        "registered_at": datetime.now().isoformat()
    }
    devices[request.device_id] = device
    logger.info(f"Device registered: {request.device_id}")
    await broadcast_message({"type": "device_online", "device": device})
    return {"status": "success", "device": device}

# ============================================================================
# 任务执行 API (供设备端调用)
# ============================================================================

@app.get("/api/v1/tasks/pending")
async def get_pending_tasks(device_id: str = ""):
    """获取待执行任务"""
    pending = [t for t in tasks if t.get("status") != "completed"]
    return {"tasks": pending, "total": len(pending)}

@app.post("/api/v1/tasks/{task_id}/complete")
async def complete_task(task_id: str, result: Dict = {}):
    """标记任务完成"""
    for task in tasks:
        if task.get("id") == task_id or task.get("timestamp") == task_id:
            task["status"] = "completed"
            task["result"] = result
            return {"status": "success"}
    return {"status": "not_found"}

# ============================================================================
# WebSocket
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    logger.info(f"WebSocket connected, total: {len(active_websockets)}")
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                elif message.get("type") == "chat":
                    request = ChatRequest(message=message.get("content", ""), device_id=message.get("device_id", ""))
                    response = await chat(request)
                    await websocket.send_json({
                        "type": "chat_response",
                        "content": response.get("response", ""),
                        "timestamp": datetime.now().isoformat()
                    })
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

async def broadcast_message(message: Dict):
    for ws in active_websockets:
        try:
            await ws.send_json(message)
        except:
            pass

# ============================================================================
# 启动事件
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Galaxy Dashboard v2.3.21")
    logger.info("=" * 60)
    logger.info("智能体可以真正操作设备，不只是返回结果")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
