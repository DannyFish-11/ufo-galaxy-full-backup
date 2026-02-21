/**
 * Galaxy TypeScript 前端组件
 * ==========================
 * 
 * 类型安全的前端组件
 */

import type { SystemInfo, Device, Agent, LLMProvider, ChatResponse } from './types';
import { GalaxyAPI, galaxyAPI } from './api';

/**
 * ASCII 艺术字组件
 */
export class AsciiArtComponent {
  private container: HTMLElement;
  private style: 'minimal' | 'normal' | 'large';

  constructor(container: HTMLElement, style: 'minimal' | 'normal' | 'large' = 'minimal') {
    this.container = container;
    this.style = style;
  }

  async render(): Promise<void> {
    try {
      const { ascii } = await galaxyAPI.getAsciiArt(this.style);
      this.container.innerHTML = `<pre class="ascii-art">${ascii}</pre>`;
    } catch (error) {
      console.error('Failed to load ASCII art:', error);
    }
  }
}

/**
 * 系统状态组件
 */
export class SystemStatusComponent {
  private container: HTMLElement;

  constructor(container: HTMLElement) {
    this.container = container;
  }

  async render(): Promise<void> {
    try {
      const info = await galaxyAPI.getSystemInfo();
      this.container.innerHTML = `
        <div class="system-status">
          <h2>${info.name} v${info.version}</h2>
          <p>${info.description}</p>
          <div class="features">
            ${Object.entries(info.features)
              .filter(([_, enabled]) => enabled)
              .map(([name, _]) => `<span class="feature">✅ ${name}</span>`)
              .join('')}
          </div>
          <div class="stats">
            <span>节点: ${info.nodes}</span>
            <span>代码: ${info.code_lines.toLocaleString()} 行</span>
          </div>
        </div>
      `;
    } catch (error) {
      console.error('Failed to load system status:', error);
    }
  }
}

/**
 * 设备列表组件
 */
export class DeviceListComponent {
  private container: HTMLElement;
  private devices: Device[] = [];

  constructor(container: HTMLElement) {
    this.container = container;
  }

  async load(): Promise<void> {
    try {
      const { devices } = await galaxyAPI.getDevices();
      this.devices = devices;
    } catch (error) {
      console.error('Failed to load devices:', error);
    }
  }

  render(): void {
    if (this.devices.length === 0) {
      this.container.innerHTML = '<p class="no-devices">没有已连接的设备</p>';
      return;
    }

    this.container.innerHTML = `
      <div class="device-list">
        ${this.devices.map(device => `
          <div class="device-card ${device.status}">
            <span class="device-icon">${this.getDeviceIcon(device.platform)}</span>
            <div class="device-info">
              <span class="device-name">${device.name}</span>
              <span class="device-platform">${device.platform}</span>
            </div>
            <span class="device-status ${device.status}">${device.status}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  private getDeviceIcon(platform: string): string {
    const icons: Record<string, string> = {
      android: '📱',
      windows: '💻',
      macos: '🍎',
      linux: '🐧',
      ios: '📱',
      tablet: '📲',
    };
    return icons[platform] || '📟';
  }
}

/**
 * Agent 列表组件
 */
export class AgentListComponent {
  private container: HTMLElement;
  private agents: Agent[] = [];

  constructor(container: HTMLElement) {
    this.container = container;
  }

  async load(): Promise<void> {
    try {
      const { agents } = await galaxyAPI.getAgents();
      this.agents = agents;
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  }

  render(): void {
    if (this.agents.length === 0) {
      this.container.innerHTML = '<p class="no-agents">没有活动的 Agent</p>';
      return;
    }

    this.container.innerHTML = `
      <div class="agent-list">
        ${this.agents.map(agent => `
          <div class="agent-card ${agent.state}">
            <div class="agent-header">
              <span class="agent-name">${agent.name}</span>
              <span class="agent-state ${agent.state}">${agent.state}</span>
            </div>
            <div class="agent-details">
              <span class="agent-task">${agent.task}</span>
              <span class="agent-llm">LLM: ${agent.llm_provider}</span>
              <span class="agent-complexity">复杂度: ${agent.complexity}</span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }
}

/**
 * 聊天组件
 */
export class ChatComponent {
  private container: HTMLElement;
  private messages: Array<{ role: 'user' | 'assistant'; content: string }> = [];
  private inputElement: HTMLInputElement | null = null;
  private messagesElement: HTMLElement | null = null;

  constructor(container: HTMLElement) {
    this.container = container;
  }

  render(): void {
    this.container.innerHTML = `
      <div class="chat-container">
        <div class="chat-messages" id="chat-messages"></div>
        <div class="chat-input-container">
          <input type="text" id="chat-input" placeholder="输入消息..." />
          <button id="chat-send">发送</button>
        </div>
      </div>
    `;

    this.messagesElement = this.container.querySelector('#chat-messages');
    this.inputElement = this.container.querySelector('#chat-input');
    const sendButton = this.container.querySelector('#chat-send');

    if (sendButton && this.inputElement) {
      sendButton.addEventListener('click', () => this.sendMessage());
      this.inputElement.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') this.sendMessage();
      });
    }
  }

  private async sendMessage(): Promise<void> {
    if (!this.inputElement || !this.messagesElement) return;

    const message = this.inputElement.value.trim();
    if (!message) return;

    // 添加用户消息
    this.messages.push({ role: 'user', content: message });
    this.renderMessages();
    this.inputElement.value = '';

    try {
      // 发送到后端
      const response = await galaxyAPI.chat(message);
      
      // 添加助手消息
      this.messages.push({ role: 'assistant', content: response.response });
      this.renderMessages();
    } catch (error) {
      this.messages.push({ role: 'assistant', content: '❌ 发生错误，请重试。' });
      this.renderMessages();
    }
  }

  private renderMessages(): void {
    if (!this.messagesElement) return;

    this.messagesElement.innerHTML = this.messages.map(msg => `
      <div class="chat-message ${msg.role}">
        <div class="message-content">${this.escapeHtml(msg.content)}</div>
      </div>
    `).join('');

    // 滚动到底部
    this.messagesElement.scrollTop = this.messagesElement.scrollHeight;
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

/**
 * LLM 提供商组件
 */
export class LLMProviderComponent {
  private container: HTMLElement;
  private providers: LLMProvider[] = [];

  constructor(container: HTMLElement) {
    this.container = container;
  }

  async load(): Promise<void> {
    try {
      const { providers } = await galaxyAPI.getLLMProviders();
      this.providers = providers;
    } catch (error) {
      console.error('Failed to load LLM providers:', error);
    }
  }

  render(): void {
    this.container.innerHTML = `
      <div class="llm-providers">
        ${this.providers.map(provider => `
          <div class="provider-card ${provider.available ? 'available' : 'unavailable'}">
            <span class="provider-status">${provider.available ? '✅' : '❌'}</span>
            <span class="provider-name">${provider.provider}</span>
            <span class="provider-model">${provider.model}</span>
            <div class="provider-scores">
              <span>速度: ${provider.speed_score}/10</span>
              <span>质量: ${provider.quality_score}/10</span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }
}
