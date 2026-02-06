# 统一融合入口文件 - Node_90_MultimodalVision
# 通过 VisionPipeline 统一调用 OCR 和 GUI 理解
import importlib
import logging
import asyncio
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 添加项目根目录
project_root = os.path.join(current_dir, '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger("Node_90")


class FusionNode:
    """
    Node_90 融合入口

    通过 VisionPipeline 将 OCR 和 GUI 理解融合为统一的视觉理解引擎。
    一次截图调用同时获取：OCR 文本 + GUI 元素树 + 场景语义 + 动作建议。
    """

    def __init__(self):
        self.node_id = "Node_90"
        self.instance = None
        self.vision_pipeline = None
        self._load_original_logic()
        self._init_vision_pipeline()

    def _load_original_logic(self):
        try:
            module = importlib.import_module("main")
            if hasattr(module, "get_instance"):
                self.instance = module.get_instance()
            elif hasattr(module, "Node"):
                self.instance = module.Node()
            else:
                self.instance = module
            logger.info(f"✅ {self.node_id} logic loaded successfully")
        except Exception as e:
            logger.error(f"❌ {self.node_id} failed to load logic: {e}")

    def _init_vision_pipeline(self):
        """初始化融合视觉管线"""
        try:
            from core.vision_pipeline import get_vision_pipeline
            self.vision_pipeline = get_vision_pipeline()
            logger.info(f"✅ {self.node_id} VisionPipeline 已接入")
        except Exception as e:
            logger.warning(f"⚠️ {self.node_id} VisionPipeline 未接入: {e}")

    async def execute(self, command, **params):
        """
        统一执行入口

        支持的命令：
        - understand: 完整视觉理解（OCR + GUI + 场景）
        - find_element: 查找特定 UI 元素
        - extract_text: 提取文本
        - analyze_for_action: 分析并生成动作建议
        - ocr: 纯 OCR（向后兼容）
        - analyze_screen: 屏幕分析（向后兼容）
        - capture_screen: 截图（向后兼容）
        """
        # 优先使用 VisionPipeline 融合模式
        if self.vision_pipeline:
            fusion_commands = {
                "understand": self._cmd_understand,
                "find_element": self._cmd_find_element,
                "extract_text": self._cmd_extract_text,
                "analyze_for_action": self._cmd_analyze_for_action,
                # 向后兼容映射
                "ocr": self._cmd_extract_text,
                "analyze_screen": self._cmd_understand,
            }

            handler = fusion_commands.get(command)
            if handler:
                return await handler(**params)

        # 降级到原始逻辑
        if not self.instance:
            return {"success": False, "error": "Logic not loaded"}
        try:
            method = None
            for m in ["process", "execute", "run", "handle"]:
                if hasattr(self.instance, m):
                    method = getattr(self.instance, m)
                    break
            if method:
                if asyncio.iscoroutinefunction(method):
                    result = await method(command, **params)
                else:
                    result = method(command, **params)
            else:
                if callable(self.instance):
                    result = self.instance(command, **params)
                else:
                    return {"success": False, "error": "No executable method found"}
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"❌ {self.node_id} execution error: {e}")
            return {"success": False, "error": str(e)}

    async def _cmd_understand(self, **params):
        """完整视觉理解"""
        result = await self.vision_pipeline.understand(
            image_base64=params.get("image_base64"),
            image_path=params.get("image_path"),
            mode="full",
            task_context=params.get("task_context", ""),
        )
        return {"success": result.success, "data": result.to_dict()}

    async def _cmd_find_element(self, **params):
        """查找 UI 元素"""
        description = params.get("description", "")
        element = await self.vision_pipeline.find_element(
            description=description,
            image_base64=params.get("image_base64"),
            image_path=params.get("image_path"),
        )
        if element:
            return {
                "success": True,
                "found": True,
                "element": element.to_dict(),
                "click_position": {
                    "x": element.bbox.center[0],
                    "y": element.bbox.center[1],
                },
            }
        return {"success": True, "found": False, "reason": f"未找到 '{description}'"}

    async def _cmd_extract_text(self, **params):
        """提取文本"""
        text = await self.vision_pipeline.extract_text(
            image_base64=params.get("image_base64"),
            image_path=params.get("image_path"),
        )
        return {"success": True, "text": text}

    async def _cmd_analyze_for_action(self, **params):
        """分析并生成动作建议"""
        task = params.get("task", "")
        result = await self.vision_pipeline.understand(
            image_base64=params.get("image_base64"),
            image_path=params.get("image_path"),
            mode="full",
            task_context=f"I need to: {task}. What should I do next?",
        )
        if not result.success:
            return {"success": False, "error": result.error}

        next_action = None
        if result.action_hints:
            next_action = max(result.action_hints, key=lambda a: a.priority).to_dict()

        return {
            "success": True,
            "scene": result.scene.to_dict(),
            "suggested_actions": [a.to_dict() for a in result.action_hints],
            "next_action": next_action,
            "interactable_elements": [e.to_dict() for e in result.interactable_elements],
        }

    def get_stats(self):
        """获取统计"""
        if self.vision_pipeline:
            return self.vision_pipeline.get_stats()
        return {}


def get_node_instance():
    return FusionNode()
