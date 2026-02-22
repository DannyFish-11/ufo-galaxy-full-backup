package com.ufo.galaxy.network

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Settings
import android.util.Log
import androidx.core.content.ContextCompat
import com.google.gson.Gson
import com.google.gson.JsonObject
import kotlinx.coroutines.*
import okhttp3.*
import java.util.UUID
import java.util.concurrent.TimeUnit

/**
 * Galaxy WebSocket 客户端 V2
 * 
 * 对齐服务端新的 DeviceMessage 格式
 * 支持完整的设备注册和能力协商
 */
class GalaxyWebSocketClientV2(
    private val context: Context,
    private val serverUrl: String
) {
    companion object {
        private const val TAG = "GalaxyWebSocketV2"
        private const val RECONNECT_DELAY_MS = 5000L
        private const val HEARTBEAT_INTERVAL_MS = 30000L
        private const val MAX_RECONNECT_ATTEMPTS = 5
    }
    
    /**
     * WebSocket 监听器接口
     */
    interface Listener {
        fun onConnected()
        fun onDisconnected()
        fun onMessage(message: String)
        fun onError(error: String)
        fun onCommand(action: String, payload: Map<String, Any>)
    }
    
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .pingInterval(20, TimeUnit.SECONDS)
        .build()
    
    private val gson = Gson()
    private var webSocket: WebSocket? = null
    private var listener: Listener? = null
    private var isConnected = false
    private var reconnectAttempts = 0
    private var heartbeatJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    // 设备信息
    private val deviceId: String by lazy { generateDeviceId() }
    private val deviceInfo: DeviceInfo by lazy { collectDeviceInfo() }
    
    /**
     * 生成唯一的设备 ID
     */
    private fun generateDeviceId(): String {
        // 使用 Android ID 作为基础
        val androidId = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ANDROID_ID
        ) ?: UUID.randomUUID().toString()
        
        return "android_${androidId.take(8)}"
    }
    
    /**
     * 收集设备信息
     */
    private fun collectDeviceInfo(): DeviceInfo {
        return DeviceInfo(
            deviceId = deviceId,
            deviceName = "${Build.MANUFACTURER} ${Build.MODEL}",
            deviceType = "android",
            manufacturer = Build.MANUFACTURER,
            model = Build.MODEL,
            osVersion = "Android ${Build.VERSION.RELEASE}",
            appVersion = getAppVersion(),
            capabilities = collectCapabilities(),
            groups = listOf("mobile"),
            tags = listOf("android", "mobile")
        )
    }
    
    /**
     * 获取应用版本
     */
    private fun getAppVersion(): String {
        return try {
            val packageInfo = context.packageManager.getPackageInfo(context.packageName, 0)
            packageInfo.versionName ?: "1.0.0"
        } catch (e: Exception) {
            "1.0.0"
        }
    }
    
    /**
     * 收集设备能力
     */
    private fun collectCapabilities(): List<String> {
        val capabilities = mutableListOf<String>(
            "screen",
            "touch",
            "keyboard"
        )
        
        // 检查摄像头
        if (context.packageManager.hasSystemFeature(PackageManager.FEATURE_CAMERA)) {
            capabilities.add("camera")
        }
        
        // 检查麦克风
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) 
            == PackageManager.PERMISSION_GRANTED) {
            capabilities.add("microphone")
        }
        
        // 检查蓝牙
        if (context.packageManager.hasSystemFeature(PackageManager.FEATURE_BLUETOOTH)) {
            capabilities.add("bluetooth")
        }
        
        // 检查 NFC
        if (context.packageManager.hasSystemFeature(PackageManager.FEATURE_NFC)) {
            capabilities.add("nfc")
        }
        
        // 检查 GPS
        if (context.packageManager.hasSystemFeature(PackageManager.FEATURE_LOCATION_GPS)) {
            capabilities.add("gps")
        }
        
        return capabilities
    }
    
    /**
     * 设置监听器
     */
    fun setListener(listener: Listener) {
        this.listener = listener
    }
    
    /**
     * 获取设备 ID
     */
    fun getDeviceId(): String = deviceId
    
    /**
     * 连接到服务器
     */
    fun connect() {
        if (isConnected) {
            Log.d(TAG, "已连接，跳过")
            return
        }
        
        Log.i(TAG, "连接到服务器: $serverUrl")
        
        val request = Request.Builder()
            .url(serverUrl)
            .build()
        
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.i(TAG, "WebSocket 已打开")
                isConnected = true
                reconnectAttempts = 0
                listener?.onConnected()
                startHeartbeat()
                
                // 发送设备注册消息
                sendDeviceRegister()
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                Log.d(TAG, "收到消息: ${text.take(100)}...")
                handleMessage(text)
            }
            
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                Log.i(TAG, "WebSocket 正在关闭: $code - $reason")
                webSocket.close(1000, null)
            }
            
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.i(TAG, "WebSocket 已关闭: $code - $reason")
                isConnected = false
                stopHeartbeat()
                listener?.onDisconnected()
                
                if (code != 1000) {
                    scheduleReconnect()
                }
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "WebSocket 失败: ${t.message}", t)
                isConnected = false
                stopHeartbeat()
                listener?.onError(t.message ?: "连接失败")
                
                scheduleReconnect()
            }
        })
    }
    
    /**
     * 断开连接
     */
    fun disconnect() {
        Log.i(TAG, "断开连接")
        stopHeartbeat()
        webSocket?.close(1000, "用户断开")
        webSocket = null
        isConnected = false
    }
    
    /**
     * 发送设备注册消息
     */
    private fun sendDeviceRegister() {
        val message = JsonObject().apply {
            addProperty("type", "command")
            addProperty("action", "register")
            addProperty("device_id", deviceId)
            addProperty("timestamp", System.currentTimeMillis())
            addProperty("message_id", UUID.randomUUID().toString().take(8))
            
            val payload = JsonObject().apply {
                addProperty("device_id", deviceInfo.deviceId)
                addProperty("device_type", deviceInfo.deviceType)
                addProperty("device_name", deviceInfo.deviceName)
                addProperty("manufacturer", deviceInfo.manufacturer)
                addProperty("model", deviceInfo.model)
                addProperty("os_version", deviceInfo.osVersion)
                addProperty("app_version", deviceInfo.appVersion)
                
                add("capabilities", gson.toJsonTree(deviceInfo.capabilities))
                add("groups", gson.toJsonTree(deviceInfo.groups))
                add("tags", gson.toJsonTree(deviceInfo.tags))
            }
            
            add("payload", payload)
        }
        
        webSocket?.send(gson.toJson(message))
        Log.i(TAG, "发送设备注册: $deviceId")
    }
    
    /**
     * 发送心跳
     */
    private fun sendHeartbeat() {
        val message = JsonObject().apply {
            addProperty("type", "heartbeat")
            addProperty("device_id", deviceId)
            addProperty("timestamp", System.currentTimeMillis())
        }
        
        webSocket?.send(gson.toJson(message))
        Log.d(TAG, "发送心跳")
    }
    
    /**
     * 发送文本消息
     */
    fun send(text: String): Boolean {
        if (!isConnected) {
            Log.w(TAG, "未连接，无法发送")
            return false
        }
        
        val message = JsonObject().apply {
            addProperty("type", "command")
            addProperty("action", "chat")
            addProperty("device_id", deviceId)
            addProperty("timestamp", System.currentTimeMillis())
            addProperty("message_id", UUID.randomUUID().toString().take(8))
            
            val payload = JsonObject().apply {
                addProperty("content", text)
            }
            
            add("payload", payload)
        }
        
        val sent = webSocket?.send(gson.toJson(message)) ?: false
        if (sent) {
            Log.d(TAG, "发送消息: ${text.take(50)}...")
        }
        return sent
    }
    
    /**
     * 发送命令
     */
    fun sendCommand(action: String, payload: Map<String, Any>): Boolean {
        if (!isConnected) {
            return false
        }
        
        val message = JsonObject().apply {
            addProperty("type", "command")
            addProperty("action", action)
            addProperty("device_id", deviceId)
            addProperty("timestamp", System.currentTimeMillis())
            addProperty("message_id", UUID.randomUUID().toString().take(8))
            add("payload", gson.toJsonTree(payload))
        }
        
        return webSocket?.send(gson.toJson(message)) ?: false
    }
    
    /**
     * 处理收到的消息
     */
    private fun handleMessage(text: String) {
        try {
            val json = gson.fromJson(text, JsonObject::class.java)
            
            when (json.get("type")?.asString) {
                "ack" -> {
                    val action = json.get("action")?.asString
                    Log.d(TAG, "收到确认: $action")
                    
                    if (action == "handshake" || action == "register") {
                        Log.i(TAG, "设备注册成功")
                    }
                }
                
                "response" -> {
                    val payload = json.getAsJsonObject("payload")
                    val content = payload?.get("content")?.asString ?: text
                    listener?.onMessage(content)
                }
                
                "command" -> {
                    val action = json.get("action")?.asString ?: ""
                    val payload = json.getAsJsonObject("payload")
                        ?.let { gson.fromJson(it, Map::class.java) as Map<String, Any> }
                        ?: emptyMap()
                    listener?.onCommand(action, payload)
                }
                
                "error" -> {
                    val error = json.get("message")?.asString ?: "未知错误"
                    listener?.onError(error)
                }
                
                else -> {
                    // 默认作为文本消息处理
                    val content = json.getAsJsonObject("payload")
                        ?.get("content")?.asString ?: text
                    listener?.onMessage(content)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "解析消息失败", e)
            listener?.onMessage(text)
        }
    }
    
    /**
     * 启动心跳
     */
    private fun startHeartbeat() {
        heartbeatJob = scope.launch {
            while (isActive && isConnected) {
                delay(HEARTBEAT_INTERVAL_MS)
                sendHeartbeat()
            }
        }
    }
    
    /**
     * 停止心跳
     */
    private fun stopHeartbeat() {
        heartbeatJob?.cancel()
        heartbeatJob = null
    }
    
    /**
     * 安排重连
     */
    private fun scheduleReconnect() {
        if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
            Log.e(TAG, "达到最大重连次数")
            return
        }
        
        reconnectAttempts++
        val delay = RECONNECT_DELAY_MS * reconnectAttempts
        
        Log.i(TAG, "将在 ${delay}ms 后重连 (第 $reconnectAttempts 次)")
        
        scope.launch {
            delay(delay)
            connect()
        }
    }
    
    /**
     * 检查连接状态
     */
    fun isConnected(): Boolean = isConnected
}

/**
 * 设备信息
 */
data class DeviceInfo(
    val deviceId: String,
    val deviceName: String,
    val deviceType: String,
    val manufacturer: String,
    val model: String,
    val osVersion: String,
    val appVersion: String,
    val capabilities: List<String>,
    val groups: List<String>,
    val tags: List<String>
)
