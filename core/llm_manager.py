import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel
from datetime import datetime

# 假设使用 OpenAI SDK 兼容接口
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

logger = logging.getLogger("llm_manager")

class ModelConfig(BaseModel):
    provider: str  # openai, deepseek, anthropic, google, etc.
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    max_tokens: int = 4096
    temperature: float = 0.7

class TokenUsage(BaseModel):
    model: str
    input_tokens: int
    output_tokens: int
    total_cost: float
    timestamp: str

class LLMManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.models: Dict[str, ModelConfig] = {}
        self.clients: Dict[str, Any] = {}
        self.usage_log: List[TokenUsage] = []
        self.default_model = "gpt-4o"
        self._load_config()

    def _load_config(self):
        """加载多模型配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    llm_configs = config.get("llm_models", {})
                    
                    for name, cfg in llm_configs.items():
                        self.models[name] = ModelConfig(**cfg)
                        
                        # 初始化客户端 (目前仅支持 OpenAI 兼容接口)
                        if AsyncOpenAI:
                            self.clients[name] = AsyncOpenAI(
                                api_key=cfg["api_key"],
                                base_url=cfg.get("base_url")
                            )
                    
                    self.default_model = config.get("default_llm_model", "gpt-4o")
                    logger.info(f"已加载 {len(self.models)} 个 LLM 模型配置")
            except Exception as e:
                logger.error(f"加载 LLM 配置失败: {e}")

    def get_client(self, model_alias: str = None) -> Any:
        """获取指定模型的客户端"""
        model_alias = model_alias or self.default_model
        if model_alias not in self.clients:
            # Fallback to default if alias not found
            if self.default_model in self.clients:
                logger.warning(f"模型 {model_alias} 未配置，回退到 {self.default_model}")
                return self.clients[self.default_model], self.models[self.default_model]
            else:
                raise ValueError(f"模型 {model_alias} 未配置且无默认模型可用")
        return self.clients[model_alias], self.models[model_alias]

    async def chat_completion(self, messages: List[Dict], tools: List[Dict] = None, model_alias: str = None, **kwargs) -> Any:
        """统一的 Chat Completion 接口，包含 Token 审计"""
        client, model_config = self.get_client(model_alias)
        
        try:
            start_time = datetime.now()
            response = await client.chat.completions.create(
                model=model_config.model_name,
                messages=messages,
                tools=tools,
                **kwargs
            )
            
            # Token 审计
            if response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = (input_tokens / 1000 * model_config.cost_per_1k_input) + \
                       (output_tokens / 1000 * model_config.cost_per_1k_output)
                
                usage_record = TokenUsage(
                    model=model_alias or self.default_model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_cost=cost,
                    timestamp=start_time.isoformat()
                )
                self.usage_log.append(usage_record)
                logger.info(f"LLM 调用完成: {model_alias}, Cost: ${cost:.4f}")
                
            return response
            
        except Exception as e:
            logger.error(f"LLM 调用失败 ({model_alias}): {e}")
            raise

    def get_usage_summary(self) -> Dict[str, Any]:
        """获取 Token 使用统计"""
        total_cost = sum(u.total_cost for u in self.usage_log)
        by_model = {}
        for u in self.usage_log:
            if u.model not in by_model:
                by_model[u.model] = {"input": 0, "output": 0, "cost": 0.0}
            by_model[u.model]["input"] += u.input_tokens
            by_model[u.model]["output"] += u.output_tokens
            by_model[u.model]["cost"] += u.total_cost
            
        return {
            "total_cost": total_cost,
            "by_model": by_model,
            "history_count": len(self.usage_log)
        }
