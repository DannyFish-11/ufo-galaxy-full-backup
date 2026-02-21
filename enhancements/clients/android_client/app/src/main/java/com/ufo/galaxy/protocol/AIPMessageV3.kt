/**
 * AIP v3.0 - Agent Interaction Protocol (Android 端实现)
 * 
 * 此文件是 UFO Galaxy 系统的协议 Android 端实现。
 * 与 galaxy_gateway/protocol/aip_v3.py 完全对齐。
 * 
 * 版本: v3.0.0
 */

package com.ufo.galaxy.protocol

import java.util.UUID
import java.util.Date

// ============================================================================
// 设备类型定义
// ============================================================================

enum class DeviceType(val value: String) {
    // 移动端
    ANDROID_PHONE("android_phone"),
    ANDROID_TABLET("android_tablet"),
    ANDROID_TV("android_tv"),
    ANDROID_CAR("android_car"),
    ANDROID_WEAR("android_wear"),
    
    IOS_PHONE("ios_phone"),
    IOS_TABLET("ios_tablet"),
    IOS_WATCH("ios_watch"),
    
    // 桌面端
    WINDOWS_DESKTOP("windows_desktop"),
    WINDOWS_LAPTOP("windows_laptop"),
    WINDOWS_WSL("windows_wsl"),
    
    MACOS_DESKTOP("macos_desktop"),
    MACOS_LAPTOP("macos_laptop"),
    
    LINUX_DESKTOP("linux_desktop"),
    LINUX_SERVER("linux_server"),
    LINUX_RASPBERRY("linux_raspberry"),
    
    // 云端
    CLOUD_HUAWEI("cloud_huawei"),
    CLOUD_ALIYUN("cloud_aliyun"),
    CLOUD_TENCENT("cloud_tencent"),
    CLOUD_AWS("cloud_aws"),
    CLOUD_AZURE("cloud_azure"),
    
    // 嵌入式/IoT
    EMBEDDED_ESP32("embedded_esp32"),
    EMBEDDED_ARDUINO("embedded_arduino"),
    IOT_GENERIC("iot_generic"),
    
    // 容器/虚拟
    CONTAINER_DOCKER("container_docker"),
    VIRTUAL_VM("virtual_vm"),
    
    // 通用
    UNKNOWN("unknown")
}

enum class DevicePlatform(val value: String) {
    ANDROID("android"),
    IOS("ios"),
    WINDOWS("windows"),
    MACOS("macos"),
    LINUX("linux"),
    CLOUD("cloud"),
    EMBEDDED("embedded"),
    UNKNOWN("unknown")
}

// ============================================================================
// 消息类型定义
// ============================================================================

enum class MessageType(val value: String) {
    // 设备管理
    DEVICE_REGISTER("device_register"),
    DEVICE_REGISTER_ACK("device_register_ack"),
    DEVICE_UNREGISTER("device_unregister"),
    DEVICE_HEARTBEAT("heartbeat"),
    DEVICE_HEARTBEAT_ACK("heartbeat_ack"),
    DEVICE_STATUS("device_status"),
    DEVICE_CAPABILITIES("device_capabilities"),
    
    // 任务调度
    TASK_SUBMIT("task_submit"),
    TASK_ASSIGN("task_assign"),
    TASK_STATUS("task_status"),
    TASK_RESULT("task_result"),
    TASK_CANCEL("task_cancel"),
    TASK_PROGRESS("task_progress"),
    TASK_END("task_end"),
    
    // 命令执行
    COMMAND("command"),
    COMMAND_RESULT("command_result"),
    COMMAND_BATCH("command_batch"),
    
    // GUI 操作
    GUI_CLICK("gui_click"),
    GUI_SWIPE("gui_swipe"),
    GUI_INPUT("gui_input"),
    GUI_SCROLL("gui_scroll"),
    GUI_SCREENSHOT("gui_screenshot"),
    GUI_ELEMENT_QUERY("gui_element_query"),
    GUI_ELEMENT_WAIT("gui_element_wait"),
    GUI_SCREEN_CONTENT("gui_screen_content"),
    
    // 屏幕/媒体
    SCREEN_CAPTURE("screen_capture"),
    SCREEN_STREAM_START("screen_stream_start"),
    SCREEN_STREAM_STOP("screen_stream_stop"),
    SCREEN_STREAM_DATA("screen_stream_data"),
    
    // 文件操作
    FILE_READ("file_read"),
    FILE_WRITE("file_write"),
    FILE_DELETE("file_delete"),
    FILE_LIST("file_list"),
    FILE_TRANSFER("file_transfer"),
    
    // 进程管理
    PROCESS_START("process_start"),
    PROCESS_STOP("process_stop"),
    PROCESS_LIST("process_list"),
    PROCESS_STATUS("process_status"),
    
    // 协调同步
    COORD_SYNC("coord_sync"),
    COORD_BROADCAST("coord_broadcast"),
    COORD_LOCK("coord_lock"),
    COORD_UNLOCK("coord_unlock"),
    
    // 错误处理
    ERROR("error"),
    ERROR_RECOVERY("error_recovery")
}

enum class TaskStatus(val value: String) {
    PENDING("pending"),
    RUNNING("running"),
    CONTINUE("continue"),
    COMPLETED("completed"),
    FAILED("failed"),
    CANCELLED("cancelled")
}

enum class ResultStatus(val value: String) {
    SUCCESS("success"),
    FAILURE("failure"),
    SKIPPED("skipped"),
    TIMEOUT("timeout"),
    NONE("none")
}

// ============================================================================
// 数据结构
// ============================================================================

data class Rect(
    val x: Int,
    val y: Int,
    val width: Int,
    val height: Int
) {
    val centerX: Int get() = x + width / 2
    val centerY: Int get() = y + height / 2
}

data class UIElement(
    val elementId: String? = null,
    val className: String? = null,
    val text: String? = null,
    val contentDescription: String? = null,
    val viewId: String? = null,
    val bounds: Rect? = null,
    val isClickable: Boolean = false,
    val isEditable: Boolean = false,
    val isFocusable: Boolean = false,
    val isEnabled: Boolean = true,
    val isChecked: Boolean = false,
    val children: List<UIElement> = emptyList()
)

data class DeviceInfo(
    val deviceId: String,
    val deviceType: DeviceType = DeviceType.UNKNOWN,
    val platform: DevicePlatform = DevicePlatform.UNKNOWN,
    val name: String? = null,
    val model: String? = null,
    val osVersion: String? = null,
    val sdkVersion: Int? = null,
    val screenWidth: Int? = null,
    val screenHeight: Int? = null,
    val capabilities: Int = 0,
    val metadata: Map<String, Any> = emptyMap()
)

data class Command(
    val commandId: String = UUID.randomUUID().toString(),
    val toolName: String,
    val toolType: String = "action",
    val parameters: Map<String, Any> = emptyMap(),
    val timeout: Int = 30
)

data class CommandResult(
    val commandId: String,
    val status: ResultStatus = ResultStatus.NONE,
    val result: Any? = null,
    val error: String? = null,
    val executionTime: Double = 0.0
)

// ============================================================================
// AIP 消息定义
// ============================================================================

data class AIPMessage(
    val version: String = "3.0",
    val messageId: String = UUID.randomUUID().toString(),
    val correlationId: String? = null,
    val type: MessageType,
    val deviceId: String,
    val deviceType: DeviceType? = null,
    val timestamp: Long = System.currentTimeMillis(),
    val taskId: String? = null,
    val taskStatus: TaskStatus? = null,
    val commands: List<Command> = emptyList(),
    val results: List<CommandResult> = emptyList(),
    val payload: Map<String, Any> = emptyMap(),
    val error: String? = null
)

// ============================================================================
// 消息构造函数
// ============================================================================

object MessageBuilder {
    
    fun createRegisterMessage(
        deviceId: String,
        deviceType: DeviceType,
        deviceInfo: DeviceInfo
    ): AIPMessage {
        return AIPMessage(
            type = MessageType.DEVICE_REGISTER,
            deviceId = deviceId,
            deviceType = deviceType,
            payload = mapOf("device_info" to deviceInfo)
        )
    }
    
    fun createHeartbeatMessage(deviceId: String): AIPMessage {
        return AIPMessage(
            type = MessageType.DEVICE_HEARTBEAT,
            deviceId = deviceId
        )
    }
    
    fun createTaskMessage(
        deviceId: String,
        taskId: String,
        commands: List<Command>
    ): AIPMessage {
        return AIPMessage(
            type = MessageType.TASK_ASSIGN,
            deviceId = deviceId,
            taskId = taskId,
            commands = commands
        )
    }
    
    fun createGuiClickMessage(
        deviceId: String,
        x: Int,
        y: Int,
        taskId: String? = null
    ): AIPMessage {
        return AIPMessage(
            type = MessageType.GUI_CLICK,
            deviceId = deviceId,
            taskId = taskId,
            payload = mapOf("x" to x, "y" to y)
        )
    }
    
    fun createGuiInputMessage(
        deviceId: String,
        text: String,
        elementId: String? = null,
        taskId: String? = null
    ): AIPMessage {
        return AIPMessage(
            type = MessageType.GUI_INPUT,
            deviceId = deviceId,
            taskId = taskId,
            payload = mapOf("text" to text, "element_id" to elementId)
        )
    }
    
    fun createScreenshotMessage(
        deviceId: String,
        taskId: String? = null
    ): AIPMessage {
        return AIPMessage(
            type = MessageType.GUI_SCREENSHOT,
            deviceId = deviceId,
            taskId = taskId
        )
    }
    
    fun createErrorMessage(
        deviceId: String,
        error: String,
        correlationId: String? = null
    ): AIPMessage {
        return AIPMessage(
            type = MessageType.ERROR,
            deviceId = deviceId,
            correlationId = correlationId,
            error = error
        )
    }
}
