"""
示例技能处理函数
"""

async def execute(name: str) -> dict:
    """
    执行技能
    
    Args:
        name: 要问候的名字
    
    Returns:
        结果
    """
    return {
        "message": f"你好, {name}!",
        "status": "success"
    }
