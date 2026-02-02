"""
UFO Galaxy - Universal Node Communication System

Provides bidirectional communication between ANY nodes:
- Server nodes ↔ Server nodes
- Server nodes ↔ Android nodes
- Android nodes ↔ Android nodes
- Any node → Self (self-activation)

Author: UFO Galaxy Team
Version: 3.0.0
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Universal message types for node communication"""
    # Node lifecycle
    NODE_WAKEUP = "node_wakeup"           # Wake up a node
    NODE_ACTIVATE = "node_activate"       # Activate a node
    NODE_SHUTDOWN = "node_shutdown"       # Shutdown a node
    NODE_RESTART = "node_restart"         # Restart a node
    NODE_STATUS = "node_status"           # Get node status
    
    # Command execution
    COMMAND = "command"                   # Execute command
    COMMAND_RESULT = "command_result"     # Command result
    COMMAND_ASYNC = "command_async"       # Async command
    
    # Event broadcasting
    EVENT_BROADCAST = "event_broadcast"   # Broadcast event
    EVENT_SUBSCRIBE = "event_subscribe"   # Subscribe to events
    EVENT_UNSUBSCRIBE = "event_unsubscribe"  # Unsubscribe
    
    # Data exchange
    DATA_REQUEST = "data_request"         # Request data
    DATA_RESPONSE = "data_response"       # Data response
    DATA_SYNC = "data_sync"               # Sync data
    
    # Health & monitoring
    HEARTBEAT = "heartbeat"               # Heartbeat
    HEARTBEAT_ACK = "heartbeat_ack"       # Heartbeat ack
    HEALTH_CHECK = "health_check"         # Health check
    
    # Error handling
    ERROR = "error"                       # Error message
    ERROR_RECOVERY = "error_recovery"     # Error recovery


class NodeType(str, Enum):
    """Node types"""
    SERVER = "server"                     # Server-side node
    ANDROID = "android"                   # Android node
    IOS = "ios"                           # iOS node
    WEB = "web"                           # Web node
    EMBEDDED = "embedded"                 # Embedded node
    CLOUD = "cloud"                       # Cloud node


@dataclass
class NodeIdentity:
    """Node identity information"""
    node_id: str
    node_type: NodeType
    node_name: str
    host: str = "localhost"
    port: int = 0
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "node_name": self.node_name,
            "host": self.host,
            "port": self.port,
            "capabilities": self.capabilities,
            "metadata": self.metadata
        }


@dataclass
class Message:
    """Universal message format"""
    message_type: MessageType
    source_id: str
    target_id: str  # "*" for broadcast, "self" for self
    payload: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    priority: int = 5  # 1-10, lower = higher priority
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_type": self.message_type.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "payload": self.payload,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            message_type=MessageType(data["message_type"]),
            source_id=data["source_id"],
            target_id=data["target_id"],
            payload=data.get("payload", {}),
            message_id=data.get("message_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", time.time()),
            priority=data.get("priority", 5)
        )


class NodeRegistry:
    """
    Central node registry for tracking all nodes in the system
    
    Supports:
    - Server nodes (Python)
    - Android nodes (Kotlin)
    - Any other node types
    """
    
    def __init__(self):
        self._nodes: Dict[str, NodeIdentity] = {}
        self._handlers: Dict[str, Callable] = {}  # node_id -> message handler
        self._subscribers: Dict[str, Set[str]] = {}  # event_type -> node_ids
        self._lock = asyncio.Lock()
    
    async def register_node(self, node: NodeIdentity, handler: Callable = None):
        """Register a node"""
        async with self._lock:
            self._nodes[node.node_id] = node
            if handler:
                self._handlers[node.node_id] = handler
        logger.info(f"Node registered: {node.node_id} ({node.node_name})")
    
    async def unregister_node(self, node_id: str):
        """Unregister a node"""
        async with self._lock:
            self._nodes.pop(node_id, None)
            self._handlers.pop(node_id, None)
        logger.info(f"Node unregistered: {node_id}")
    
    def get_node(self, node_id: str) -> Optional[NodeIdentity]:
        """Get node by ID"""
        return self._nodes.get(node_id)
    
    def get_all_nodes(self) -> List[NodeIdentity]:
        """Get all registered nodes"""
        return list(self._nodes.values())
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[NodeIdentity]:
        """Get nodes by type"""
        return [n for n in self._nodes.values() if n.node_type == node_type]
    
    def get_handler(self, node_id: str) -> Optional[Callable]:
        """Get message handler for node"""
        return self._handlers.get(node_id)
    
    async def subscribe(self, node_id: str, event_type: str):
        """Subscribe node to event type"""
        async with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = set()
            self._subscribers[event_type].add(node_id)
    
    async def unsubscribe(self, node_id: str, event_type: str):
        """Unsubscribe node from event type"""
        async with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type].discard(node_id)
    
    def get_subscribers(self, event_type: str) -> Set[str]:
        """Get subscribers for event type"""
        return self._subscribers.get(event_type, set())


class UniversalCommunicator:
    """
    Universal Communicator for ANY node-to-node communication
    
    Features:
    - Send messages to any node (server/android/ios/embedded)
    - Broadcast messages to multiple nodes
    - Self-activation (node controls itself)
    - Async command execution
    - Event subscription/publishing
    
    Example:
        >>> comm = UniversalCommunicator(node_registry)
        >>> 
        >>> # Server node activates Android node
        >>> await comm.send_to_node(
        ...     source_id="server_node_01",
        ...     target_id="android_device_01",
        ...     message_type=MessageType.NODE_WAKEUP,
        ...     payload={"reason": "task_assigned"}
        ... )
        >>> 
        >>> # Android node controls server node
        >>> await comm.send_to_node(
        ...     source_id="android_device_01",
        ...     target_id="server_node_50",
        ...     message_type=MessageType.COMMAND,
        ...     payload={"command": "process_data", "args": [...]}
        ... )
        >>> 
        >>> # Node self-activation
        >>> await comm.activate_self(
        ...     node_id="server_node_01",
        ...     action="restart_service",
        ...     params={"service": "database"}
        ... )
    """
    
    def __init__(self, registry: NodeRegistry):
        self.registry = registry
        self._pending_responses: Dict[str, asyncio.Future] = {}
        self._message_handlers: Dict[MessageType, Callable] = {}
        self._event_listeners: Dict[str, List[Callable]] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self._message_handlers[MessageType.NODE_WAKEUP] = self._handle_wakeup
        self._message_handlers[MessageType.NODE_ACTIVATE] = self._handle_activate
        self._message_handlers[MessageType.NODE_SHUTDOWN] = self._handle_shutdown
        self._message_handlers[MessageType.NODE_RESTART] = self._handle_restart
        self._message_handlers[MessageType.NODE_STATUS] = self._handle_status
        self._message_handlers[MessageType.COMMAND] = self._handle_command
        self._message_handlers[MessageType.EVENT_BROADCAST] = self._handle_event_broadcast
    
    # ========================================================================
    # Public API - Send Messages
    # ========================================================================
    
    async def send_to_node(
        self,
        source_id: str,
        target_id: str,
        message_type: MessageType,
        payload: Dict[str, Any] = None,
        wait_response: bool = False,
        timeout: float = 30.0,
        priority: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Send message to a specific node
        
        Args:
            source_id: Source node ID
            target_id: Target node ID ("*" for broadcast, "self" for self)
            message_type: Type of message
            payload: Message payload
            wait_response: Whether to wait for response
            timeout: Response timeout
            priority: Message priority (1-10)
            
        Returns:
            Response if wait_response=True, else None
        """
        payload = payload or {}
        
        # Handle self-targeting
        if target_id == "self":
            target_id = source_id
        
        # Create message
        message = Message(
            message_type=message_type,
            source_id=source_id,
            target_id=target_id,
            payload=payload,
            priority=priority
        )
        
        # Handle broadcast
        if target_id == "*":
            return await self._broadcast(message)
        
        # Get target node
        target_node = self.registry.get_node(target_id)
        if not target_node:
            logger.warning(f"Target node not found: {target_id}")
            return None
        
        # Get handler
        handler = self.registry.get_handler(target_id)
        if not handler:
            logger.warning(f"No handler for node: {target_id}")
            return None
        
        try:
            if wait_response:
                # Create future for response
                future = asyncio.get_event_loop().create_future()
                self._pending_responses[message.message_id] = future
                
                # Send message
                await handler(message)
                
                # Wait for response
                try:
                    return await asyncio.wait_for(future, timeout=timeout)
                except asyncio.TimeoutError:
                    self._pending_responses.pop(message.message_id, None)
                    logger.warning(f"Response timeout for message: {message.message_id}")
                    return None
            else:
                # Fire and forget
                await handler(message)
                return {"success": True, "message_id": message.message_id}
                
        except Exception as e:
            logger.error(f"Failed to send message to {target_id}: {e}")
            return None
    
    async def send_to_android(
        self,
        source_id: str,
        android_device_id: str,
        message_type: MessageType,
        payload: Dict[str, Any] = None,
        wait_response: bool = False,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Send message to Android device
        
        This uses the Android Bridge to communicate with Android nodes
        """
        payload = payload or {}
        
        # Import Android Bridge
        try:
            from galaxy_gateway.android_bridge import android_bridge, MessageBuilder
            
            # Convert universal message to Android message format
            android_msg = MessageBuilder.command(
                device_id=android_device_id,
                command_type=message_type.value,
                params=payload
            )
            
            # Send via Android Bridge
            return await android_bridge.send_to_device(
                device_id=android_device_id,
                message=android_msg,
                wait_response=wait_response,
                timeout=timeout
            )
            
        except ImportError:
            logger.error("Android Bridge not available")
            return None
        except Exception as e:
            logger.error(f"Failed to send to Android: {e}")
            return None
    
    async def broadcast(
        self,
        source_id: str,
        message_type: MessageType,
        payload: Dict[str, Any] = None,
        node_types: List[NodeType] = None
    ) -> Dict[str, Any]:
        """
        Broadcast message to all nodes
        
        Args:
            source_id: Source node ID
            message_type: Type of message
            payload: Message payload
            node_types: Filter by node types (None = all)
            
        Returns:
            Broadcast results
        """
        payload = payload or {}
        
        message = Message(
            message_type=message_type,
            source_id=source_id,
            target_id="*",
            payload=payload
        )
        
        return await self._broadcast(message, node_types)
    
    async def activate_self(
        self,
        node_id: str,
        action: str,
        params: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Activate self (node controls itself)
        
        Args:
            node_id: Node ID
            action: Action to perform
            params: Action parameters
            
        Returns:
            Activation result
        """
        return await self.send_to_node(
            source_id=node_id,
            target_id=node_id,  # Self-targeting
            message_type=MessageType.NODE_ACTIVATE,
            payload={"action": action, "params": params or {}},
            wait_response=True
        )
    
    async def wakeup_node(
        self,
        source_id: str,
        target_id: str,
        reason: str = "",
        params: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Wake up a node
        
        Args:
            source_id: Source node ID
            target_id: Target node ID to wake up
            reason: Reason for wakeup
            params: Additional parameters
            
        Returns:
            Wakeup result
        """
        return await self.send_to_node(
            source_id=source_id,
            target_id=target_id,
            message_type=MessageType.NODE_WAKEUP,
            payload={"reason": reason, "params": params or {}},
            wait_response=True
        )
    
    async def execute_command(
        self,
        source_id: str,
        target_id: str,
        command: str,
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Execute command on target node
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            command: Command name
            args: Command arguments
            kwargs: Command keyword arguments
            timeout: Execution timeout
            
        Returns:
            Command result
        """
        return await self.send_to_node(
            source_id=source_id,
            target_id=target_id,
            message_type=MessageType.COMMAND,
            payload={
                "command": command,
                "args": args or [],
                "kwargs": kwargs or {}
            },
            wait_response=True,
            timeout=timeout
        )
    
    # ========================================================================
    # Event System
    # ========================================================================
    
    def on_event(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(handler)
    
    async def publish_event(
        self,
        source_id: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """Publish event to all subscribers"""
        # Get subscribers
        subscribers = self.registry.get_subscribers(event_type)
        
        # Send to each subscriber
        for node_id in subscribers:
            await self.send_to_node(
                source_id=source_id,
                target_id=node_id,
                message_type=MessageType.EVENT_BROADCAST,
                payload={"event_type": event_type, "data": data}
            )
        
        # Call local listeners
        for handler in self._event_listeners.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    # ========================================================================
    # Response Handling
    # ========================================================================
    
    def send_response(self, message_id: str, response: Dict[str, Any]):
        """Send response to pending request"""
        if message_id in self._pending_responses:
            future = self._pending_responses.pop(message_id)
            if not future.done():
                future.set_result(response)
    
    # ========================================================================
    # Internal Handlers
    # ========================================================================
    
    async def _broadcast(
        self,
        message: Message,
        node_types: List[NodeType] = None
    ) -> Dict[str, Any]:
        """Broadcast message to all nodes"""
        results = {"success": [], "failed": []}
        
        for node in self.registry.get_all_nodes():
            # Filter by node type
            if node_types and node.node_type not in node_types:
                continue
            
            # Skip self if broadcasting
            if node.node_id == message.source_id:
                continue
            
            try:
                handler = self.registry.get_handler(node.node_id)
                if handler:
                    await handler(message)
                    results["success"].append(node.node_id)
                else:
                    results["failed"].append(node.node_id)
            except Exception as e:
                logger.error(f"Broadcast to {node.node_id} failed: {e}")
                results["failed"].append(node.node_id)
        
        return results
    
    async def _handle_wakeup(self, message: Message) -> Dict[str, Any]:
        """Handle node wakeup"""
        logger.info(f"Node {message.target_id} waking up (reason: {message.payload.get('reason')})")
        return {"success": True, "status": "awake", "node_id": message.target_id}
    
    async def _handle_activate(self, message: Message) -> Dict[str, Any]:
        """Handle node activation"""
        action = message.payload.get("action")
        params = message.payload.get("params", {})
        
        logger.info(f"Node {message.target_id} activating action: {action}")
        
        # Execute activation action
        # This would be implemented by the node itself
        return {
            "success": True,
            "action": action,
            "node_id": message.target_id,
            "result": f"Action '{action}' executed"
        }
    
    async def _handle_shutdown(self, message: Message) -> Dict[str, Any]:
        """Handle node shutdown"""
        logger.info(f"Node {message.target_id} shutting down")
        return {"success": True, "status": "shutting_down", "node_id": message.target_id}
    
    async def _handle_restart(self, message: Message) -> Dict[str, Any]:
        """Handle node restart"""
        logger.info(f"Node {message.target_id} restarting")
        return {"success": True, "status": "restarting", "node_id": message.target_id}
    
    async def _handle_status(self, message: Message) -> Dict[str, Any]:
        """Handle status request"""
        node = self.registry.get_node(message.target_id)
        if node:
            return {
                "success": True,
                "node_id": message.target_id,
                "status": "online",
                "node_info": node.to_dict()
            }
        return {"success": False, "error": "Node not found"}
    
    async def _handle_command(self, message: Message) -> Dict[str, Any]:
        """Handle command execution"""
        command = message.payload.get("command")
        args = message.payload.get("args", [])
        kwargs = message.payload.get("kwargs", {})
        
        logger.info(f"Executing command '{command}' on {message.target_id}")
        
        # Command would be executed by the node
        return {
            "success": True,
            "command": command,
            "node_id": message.target_id,
            "result": f"Command '{command}' executed with args={args}, kwargs={kwargs}"
        }
    
    async def _handle_event_broadcast(self, message: Message) -> Dict[str, Any]:
        """Handle event broadcast"""
        event_type = message.payload.get("event_type")
        data = message.payload.get("data", {})
        
        logger.debug(f"Event '{event_type}' received from {message.source_id}")
        
        return {"success": True, "event_type": event_type}


# =============================================================================
# Global Instances
# =============================================================================

# Global node registry
node_registry = NodeRegistry()

# Global communicator
universal_communicator = UniversalCommunicator(node_registry)


# =============================================================================
# Convenience Functions
# =============================================================================

async def wakeup_node(
    source_id: str,
    target_id: str,
    reason: str = "",
    params: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """Convenience function to wake up a node"""
    return await universal_communicator.wakeup_node(
        source_id=source_id,
        target_id=target_id,
        reason=reason,
        params=params
    )


async def send_to_node(
    source_id: str,
    target_id: str,
    message_type: MessageType,
    payload: Dict[str, Any] = None,
    wait_response: bool = False,
    timeout: float = 30.0
) -> Optional[Dict[str, Any]]:
    """Convenience function to send message to node"""
    return await universal_communicator.send_to_node(
        source_id=source_id,
        target_id=target_id,
        message_type=message_type,
        payload=payload,
        wait_response=wait_response,
        timeout=timeout
    )


async def activate_self(node_id: str, action: str, params: Dict[str, Any] = None):
    """Convenience function for self-activation"""
    return await universal_communicator.activate_self(
        node_id=node_id,
        action=action,
        params=params
    )


# =============================================================================
# Example Usage
# =============================================================================

async def example():
    """Example usage of universal communicator"""
    
    # Register some nodes
    await node_registry.register_node(
        NodeIdentity(
            node_id="server_01",
            node_type=NodeType.SERVER,
            node_name="Task Processor",
            host="localhost",
            port=8001
        )
    )
    
    await node_registry.register_node(
        NodeIdentity(
            node_id="android_01",
            node_type=NodeType.ANDROID,
            node_name="Android Device 1",
            host="192.168.1.100",
            port=0
        )
    )
    
    # Server wakes up Android
    result = await wakeup_node(
        source_id="server_01",
        target_id="android_01",
        reason="new_task_available"
    )
    print(f"Wakeup result: {result}")
    
    # Android sends command to Server
    result = await universal_communicator.execute_command(
        source_id="android_01",
        target_id="server_01",
        command="process_data",
        args=["data_123"]
    )
    print(f"Command result: {result}")
    
    # Server self-activation
    result = await activate_self(
        node_id="server_01",
        action="reload_config",
        params={"config_file": "settings.json"}
    )
    print(f"Self-activation result: {result}")


if __name__ == "__main__":
    asyncio.run(example())
