/**
 * AIP v3.0 协议兼容层
 * 
 * 保持向后兼容，内部使用 AIPMessageV3
 * 
 * 版本: v3.0.0
 */

package com.ufo.galaxy.protocol

import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*

@Deprecated("使用 AIPMessageV3 代替", ReplaceWith("AIPMessageV3", "com.ufo.galaxy.protocol.AIPMessageV3"))
object AIPProtocol {
    
    const val VERSION = "AIP/3.0"
    const val CLIENT_ID = "Android_Client"
    const val NODE_50_ID = "Node_50"
    
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }
    
    object MessageType {
        const val COMMAND = "command"
        const val RESPONSE = "response"
        const val HEARTBEAT = "heartbeat"
        const val REGISTER = "register"
        const val STATUS = "status"
        const val ERROR = "error"
    }
    
    fun generateMessageId(): String {
        return "${CLIENT_ID.lowercase()}_${System.currentTimeMillis()}"
    }
    
    fun getCurrentTimestamp(): String {
        return dateFormat.format(Date())
    }
    
    /**
     * 创建 AIP v3.0 消息
     */
    fun createMessage(
        to: String,
        type: String,
        payload: JSONObject
    ): JSONObject {
        return JSONObject().apply {
            put("version", "3.0")
            put("message_id", generateMessageId())
            put("timestamp", getCurrentTimestamp())
            put("from", CLIENT_ID)
            put("to", to)
            put("type", type)
            put("payload", payload)
        }
    }
    
    /**
     * 创建命令消息 - 使用 AIP v3.0 格式
     */
    fun createCommandMessage(
        command: String,
        context: JSONObject? = null
    ): JSONObject {
        val payload = JSONObject().apply {
            put("command", command)
            if (context != null) {
                put("context", context)
            } else {
                put("context", createDefaultContext())
            }
        }
        
        return createMessage(NODE_50_ID, MessageType.COMMAND, payload)
    }
    
    fun createDefaultContext(): JSONObject {
        return JSONObject().apply {
            put("device_id", CLIENT_ID)
            put("device_type", DeviceType.ANDROID_PHONE.value)
            put("platform", "android")
            put("timestamp", System.currentTimeMillis())
        }
    }
    
    fun createHeartbeatMessage(): JSONObject {
        val payload = JSONObject().apply {
            put("status", "online")
            put("timestamp", System.currentTimeMillis())
        }
        return createMessage(NODE_50_ID, MessageType.HEARTBEAT, payload)
    }
    
    fun createRegisterMessage(deviceInfo: JSONObject): JSONObject {
        return createMessage(NODE_50_ID, MessageType.REGISTER, deviceInfo)
    }
    
    fun createDeviceRegistrationInfo(): JSONObject {
        return JSONObject().apply {
            put("device_id", CLIENT_ID)
            put("device_type", DeviceType.ANDROID_PHONE.value)
            put("platform", DevicePlatform.ANDROID.value)
            put("name", android.os.Build.MODEL)
            put("model", android.os.Build.MODEL)
            put("manufacturer", android.os.Build.MANUFACTURER)
            put("android_version", android.os.Build.VERSION.RELEASE)
            put("sdk_version", android.os.Build.VERSION.SDK_INT)
        }
    }
}
