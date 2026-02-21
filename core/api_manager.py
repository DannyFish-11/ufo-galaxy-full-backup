"""
Galaxy API 管理器
=================

统一管理所有 API 配置
支持双并行策略: OneAPI 聚合器 + 其他单独模型

版本: v1.0
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("APIManager")


@dataclass
class ModelConfig:
    """模型配置"""
    provider: str
    model_id: str
    model_name: str
    api_key: str = ""
    base_url: str = ""
    enabled: bool = True


@dataclass
class NodeConfig:
    """节点配置"""
    node_id: str
    name: str
    port: int
    status: str = "configured"
    endpoint: str = ""


class APIManager:
    """
    API 管理器
    
    统一管理所有 API 配置
    支持双并行策略
    """
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config", "api_config.json"
            )
        
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.models: Dict[str, ModelConfig] = {}
        self.nodes: Dict[str, NodeConfig] = {}
        
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"已加载配置: {self.config_path}")
                self._parse_config()
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
                self._init_default_config()
        else:
            self._init_default_config()
    
    def _init_default_config(self):
        """初始化默认配置"""
        self.config = {
            "oneapi": {"enabled": True, "api_key": "", "base_url": "http://localhost:8001/v1"},
            "direct_models": {},
            "nodes": {}
        }
        logger.info("使用默认配置")
    
    def _parse_config(self):
        """解析配置"""
        # 解析 OneAPI 模型
        oneapi = self.config.get("oneapi", {})
        if oneapi.get("enabled"):
            for model in oneapi.get("models", []):
                key = f"oneapi:{model['id']}"
                self.models[key] = ModelConfig(
                    provider="oneapi",
                    model_id=model["id"],
                    model_name=model["name"],
                    api_key=oneapi.get("api_key", ""),
                    base_url=oneapi.get("base_url", ""),
                    enabled=True
                )
        
        # 解析直接模型
        direct_models = self.config.get("direct_models", {})
        for provider, config in direct_models.items():
            if config.get("enabled"):
                for model_id in config.get("models", []):
                    key = f"{provider}:{model_id}"
                    self.models[key] = ModelConfig(
                        provider=provider,
                        model_id=model_id,
                        model_name=model_id,
                        api_key=config.get("api_key", ""),
                        base_url=config.get("base_url", ""),
                        enabled=True
                    )
        
        # 解析节点
        nodes = self.config.get("nodes", {}).get("registry", {})
        base_url = self.config.get("nodes", {}).get("base_url", "http://localhost")
        
        for node_id, config in nodes.items():
            self.nodes[node_id] = NodeConfig(
                node_id=node_id,
                name=config.get("name", f"Node_{node_id}"),
                port=config.get("port", 8000),
                status=config.get("status", "configured"),
                endpoint=f"{base_url}:{config.get('port', 8000)}"
            )
        
        logger.info(f"已解析 {len(self.models)} 个模型, {len(self.nodes)} 个节点")
    
    # =========================================================================
    # 配置管理
    # =========================================================================
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            self.config = new_config
            self._parse_config()
            self._save_config()
            return True
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    # =========================================================================
    # API Key 管理
    # =========================================================================
    
    def set_api_key(self, provider: str, api_key: str) -> bool:
        """设置 API Key"""
        try:
            if provider == "oneapi":
                self.config.setdefault("oneapi", {})["api_key"] = api_key
            else:
                self.config.setdefault("direct_models", {}).setdefault(provider, {})["api_key"] = api_key
            
            self._save_config()
            self._parse_config()
            return True
        except Exception as e:
            logger.error(f"设置 API Key 失败: {e}")
            return False
    
    def get_api_key(self, provider: str) -> str:
        """获取 API Key"""
        if provider == "oneapi":
            return self.config.get("oneapi", {}).get("api_key", "")
        return self.config.get("direct_models", {}).get(provider, {}).get("api_key", "")
    
    # =========================================================================
    # 模型管理
    # =========================================================================
    
    def get_models(self) -> List[Dict[str, Any]]:
        """获取所有模型"""
        return [
            {
                "key": key,
                "provider": model.provider,
                "model_id": model.model_id,
                "model_name": model.model_name,
                "enabled": model.enabled,
                "configured": bool(model.api_key)
            }
            for key, model in self.models.items()
        ]
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取已配置的可用模型"""
        return [
            {
                "key": key,
                "provider": model.provider,
                "model_id": model.model_id,
                "model_name": model.model_name
            }
            for key, model in self.models.items()
            if model.enabled and model.api_key
        ]
    
    # =========================================================================
    # 节点管理
    # =========================================================================
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """获取所有节点"""
        return [
            {
                "node_id": node.node_id,
                "name": node.name,
                "port": node.port,
                "status": node.status,
                "endpoint": node.endpoint
            }
            for node in self.nodes.values()
        ]
    
    async def check_node_health(self, node_id: str) -> Dict[str, Any]:
        """检查节点健康状态"""
        node = self.nodes.get(node_id)
        if not node:
            return {"success": False, "error": "Node not found"}
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{node.endpoint}/health")
                if response.status_code == 200:
                    return {"success": True, "status": "healthy"}
                return {"success": False, "status": "unhealthy"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def check_all_nodes(self) -> Dict[str, Any]:
        """检查所有节点"""
        results = {}
        tasks = [self.check_node_health(node_id) for node_id in self.nodes.keys()]
        health_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for node_id, result in zip(self.nodes.keys(), health_results):
            if isinstance(result, Exception):
                results[node_id] = {"success": False, "error": str(result)}
            else:
                results[node_id] = result
        
        return results
    
    # =========================================================================
    # LLM 调用
    # =========================================================================
    
    async def call_llm(
        self,
        messages: List[Dict[str, str]],
        model: str = "auto",
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        调用 LLM
        
        按双并行策略:
        1. 优先使用 OneAPI
        2. 然后尝试直接模型
        """
        # 获取可用模型
        available = self.get_available_models()
        if not available:
            return {"success": False, "error": "No models configured"}
        
        # 按优先级排序 (OneAPI 优先)
        available.sort(key=lambda x: 0 if x["provider"] == "oneapi" else 1)
        
        # 尝试调用
        for model_info in available:
            result = await self._call_model(
                model_info,
                messages,
                max_tokens
            )
            if result.get("success"):
                return result
        
        return {"success": False, "error": "All models failed"}
    
    async def _call_model(
        self,
        model_info: Dict[str, Any],
        messages: List[Dict[str, str]],
        max_tokens: int
    ) -> Dict[str, Any]:
        """调用单个模型"""
        model_key = model_info["key"]
        model_config = self.models.get(model_key)
        
        if not model_config or not model_config.api_key:
            return {"success": False, "error": "Model not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{model_config.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {model_config.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_config.model_id,
                        "messages": messages,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "provider": model_config.provider,
                        "model": model_config.model_id,
                        "content": data["choices"][0]["message"]["content"],
                        "usage": data.get("usage", {})
                    }
                
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # 状态
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        available_models = self.get_available_models()
        
        return {
            "total_models": len(self.models),
            "configured_models": len(available_models),
            "total_nodes": len(self.nodes),
            "oneapi_enabled": self.config.get("oneapi", {}).get("enabled", False),
            "oneapi_configured": bool(self.config.get("oneapi", {}).get("api_key")),
            "direct_providers": len(self.config.get("direct_models", {})),
            "timestamp": datetime.now().isoformat()
        }


# 全局实例
api_manager = APIManager()
