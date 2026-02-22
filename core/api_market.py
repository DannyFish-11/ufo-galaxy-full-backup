"""
UFO Galaxy - 技能市场 API
========================

提供技能市场的 REST API

API 端点:
- GET  /api/v1/market/skills         - 列出市场技能
- GET  /api/v1/market/skills/{id}    - 获取技能详情
- GET  /api/v1/market/search         - 搜索技能
- POST /api/v1/market/publish        - 发布技能
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("UFO-Galaxy.MarketAPI")

router = APIRouter()


# ============================================================================
# 数据模型
# ============================================================================

class SkillPublishRequest(BaseModel):
    """技能发布请求"""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = []
    content: str = ""  # SKILL.md 内容


# ============================================================================
# 模拟市场数据 (实际应该连接数据库)
# ============================================================================

# 内置技能市场
BUILTIN_SKILLS = [
    {
        "id": "weather",
        "name": "Weather",
        "description": "Get current weather and forecasts",
        "version": "1.0.0",
        "author": "UFO Galaxy",
        "tags": ["weather", "api"],
        "downloads": 1000,
        "rating": 4.5,
    },
    {
        "id": "github",
        "name": "GitHub",
        "description": "GitHub operations via gh CLI",
        "version": "1.0.0",
        "author": "UFO Galaxy",
        "tags": ["github", "git", "cli"],
        "downloads": 800,
        "rating": 4.8,
    },
    {
        "id": "web_search",
        "name": "Web Search",
        "description": "Search the web using DuckDuckGo",
        "version": "1.0.0",
        "author": "UFO Galaxy",
        "tags": ["search", "web"],
        "downloads": 600,
        "rating": 4.2,
    },
    {
        "id": "file_operations",
        "name": "File Operations",
        "description": "Read, write, and manage files",
        "version": "1.0.0",
        "author": "UFO Galaxy",
        "tags": ["file", "io"],
        "downloads": 500,
        "rating": 4.0,
    },
    {
        "id": "email",
        "name": "Email",
        "description": "Send and manage emails",
        "version": "1.0.0",
        "author": "UFO Galaxy",
        "tags": ["email", "communication"],
        "downloads": 400,
        "rating": 3.8,
    },
]


# ============================================================================
# API 端点
# ============================================================================

@router.get("/api/v1/market/skills")
async def list_market_skills(
    tag: str = None,
    limit: int = 20,
    offset: int = 0,
):
    """列出市场技能"""
    skills = BUILTIN_SKILLS
    
    # 按标签过滤
    if tag:
        skills = [s for s in skills if tag in s["tags"]]
    
    # 分页
    total = len(skills)
    skills = skills[offset:offset + limit]
    
    return JSONResponse({
        "success": True,
        "skills": skills,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@router.get("/api/v1/market/skills/{skill_id}")
async def get_market_skill(skill_id: str):
    """获取技能详情"""
    for skill in BUILTIN_SKILLS:
        if skill["id"] == skill_id:
            # 返回完整信息
            return JSONResponse({
                "success": True,
                "skill": {
                    **skill,
                    "download_url": f"https://raw.githubusercontent.com/DannyFish-11/ufo-galaxy-realization-v2/main/skills/examples/{skill_id}/SKILL.md",
                    "readme": f"# {skill['name']}\n\n{skill['description']}",
                },
            })
    
    return JSONResponse({
        "success": False,
        "error": "技能不存在",
    }, status_code=404)


@router.get("/api/v1/market/search")
async def search_market_skills(q: str, limit: int = 10):
    """搜索技能"""
    q = q.lower()
    
    results = []
    for skill in BUILTIN_SKILLS:
        # 搜索名称、描述、标签
        if (q in skill["name"].lower() or
            q in skill["description"].lower() or
            any(q in tag.lower() for tag in skill["tags"])):
            results.append(skill)
    
    return JSONResponse({
        "success": True,
        "query": q,
        "skills": results[:limit],
        "total": len(results),
    })


@router.post("/api/v1/market/publish")
async def publish_skill(req: SkillPublishRequest):
    """发布技能 (需要认证)"""
    # TODO: 实现认证和存储
    
    return JSONResponse({
        "success": True,
        "message": "技能发布功能暂未开放",
        "skill": {
            "id": req.name.lower().replace(" ", "-"),
            "name": req.name,
            "description": req.description,
            "version": req.version,
        },
    })


@router.get("/api/v1/market/tags")
async def list_tags():
    """列出所有标签"""
    tags = set()
    for skill in BUILTIN_SKILLS:
        tags.update(skill["tags"])
    
    return JSONResponse({
        "success": True,
        "tags": sorted(list(tags)),
    })


@router.get("/api/v1/market/stats")
async def market_stats():
    """市场统计"""
    return JSONResponse({
        "success": True,
        "stats": {
            "total_skills": len(BUILTIN_SKILLS),
            "total_downloads": sum(s["downloads"] for s in BUILTIN_SKILLS),
            "avg_rating": sum(s["rating"] for s in BUILTIN_SKILLS) / len(BUILTIN_SKILLS),
        },
    })


# ============================================================================
# 导出
# ============================================================================

__all__ = ["router"]
