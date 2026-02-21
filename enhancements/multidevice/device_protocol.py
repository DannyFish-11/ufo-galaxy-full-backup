"""
UFO Galaxy - Device Protocol Module
AIP v3.0 Protocol Implementation (统一版本)

此文件是 UFO Galaxy 系统的设备通信协议实现。
基于 galaxy_gateway/protocol/aip_v3.py 的统一协议定义。

版本: v3.0.0
"""

# 从统一协议导入
from galaxy_gateway.protocol.aip_v3 import (
    # 设备类型
    DeviceType, DevicePlatform, DeviceCapability,
    # 消息类型
    MessageType, TaskStatus, ResultStatus,
    # 数据结构
    Rect, UIElement, DeviceInfo, Command, CommandResult,
    # 消息
    AIPMessage,
    # 构造函数
    create_register_message, create_heartbeat_message,
    create_task_message, create_gui_click_message,
    create_gui_input_message, create_screenshot_message,
    create_error_message,
    # 解析验证
    parse_message, validate_message
)

# 导出所有公共接口
__all__ = [
    # 设备类型
    'DeviceType', 'DevicePlatform', 'DeviceCapability',
    # 消息类型
    'MessageType', 'TaskStatus', 'ResultStatus',
    # 数据结构
    'Rect', 'UIElement', 'DeviceInfo', 'Command', 'CommandResult',
    # 消息
    'AIPMessage',
    # 构造函数
    'create_register_message', 'create_heartbeat_message',
    'create_task_message', 'create_gui_click_message',
    'create_gui_input_message', 'create_screenshot_message',
    'create_error_message',
    # 解析验证
    'parse_message', 'validate_message'
]
