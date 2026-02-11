/**
 * LK Clinic Tools - Embeddable Chat Widget
 * Vanilla JS/TS implementation (no React dependency).
 * Connects to backend via WebSocket for real-time chat.
 *
 * Usage:
 * <script src="https://app.lkclinictools.com/widget/chatbot.js"
 *   data-bot-id="xxx" data-clinic-id="yyy" async></script>
 */

import "./widget-styles.css";

interface WidgetConfig {
  botId: string;
  clinicId: string;
  position?: "bottom-right" | "bottom-left";
  primaryColor?: string;
  welcomeMessage?: string;
  launcherText?: string;
  wsUrl?: string;
}

interface ChatMessage {
  type: "bot" | "user";
  text: string;
  buttons?: { id: string; title: string }[];
  timestamp: Date;
}

class LKChatWidget {
  private config: WidgetConfig;
  private ws: WebSocket | null = null;
  private sessionId: string;
  private messages: ChatMessage[] = [];
  private isOpen = false;
  private container: HTMLElement | null = null;

  constructor(config: WidgetConfig) {
    this.config = {
      position: "bottom-right",
      primaryColor: "#2563eb",
      welcomeMessage: "Olá! Como posso ajudar?",
      launcherText: "Chat",
      wsUrl: "ws://localhost:8000/ws/widget",
      ...config,
    };
    this.sessionId = this.generateSessionId();
    this.init();
  }

  private generateSessionId(): string {
    return "lk_" + Math.random().toString(36).substring(2, 15);
  }

  private init() {
    this.createDOM();
    this.connectWebSocket();
  }

  private createDOM() {
    // Container
    this.container = document.createElement("div");
    this.container.id = "lk-clinic-widget";
    this.container.className = `lk-widget lk-widget--${this.config.position}`;
    this.container.innerHTML = this.getWidgetHTML();
    document.body.appendChild(this.container);

    // Apply custom colors
    this.container.style.setProperty("--lk-primary", this.config.primaryColor!);

    // Bind events
    this.bindEvents();
  }

  private getWidgetHTML(): string {
    return `
      <button class="lk-launcher" aria-label="Abrir chat">
        <span class="lk-launcher__text">${this.config.launcherText}</span>
        <svg class="lk-launcher__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </button>
      <div class="lk-chat" style="display:none">
        <div class="lk-chat__header">
          <span>Atendimento</span>
          <button class="lk-chat__close">&times;</button>
        </div>
        <div class="lk-chat__messages"></div>
        <div class="lk-chat__input-area">
          <input type="text" class="lk-chat__input" placeholder="Digite sua mensagem..." />
          <button class="lk-chat__send">Enviar</button>
        </div>
      </div>
    `;
  }

  private bindEvents() {
    if (!this.container) return;

    const launcher = this.container.querySelector(".lk-launcher");
    const closeBtn = this.container.querySelector(".lk-chat__close");
    const input = this.container.querySelector(".lk-chat__input") as HTMLInputElement;
    const sendBtn = this.container.querySelector(".lk-chat__send");

    launcher?.addEventListener("click", () => this.toggle());
    closeBtn?.addEventListener("click", () => this.close());
    sendBtn?.addEventListener("click", () => this.sendUserMessage(input));
    input?.addEventListener("keypress", (e) => {
      if ((e as KeyboardEvent).key === "Enter") this.sendUserMessage(input);
    });
  }

  private toggle() {
    this.isOpen ? this.close() : this.open();
  }

  private open() {
    if (!this.container) return;
    this.isOpen = true;
    const chat = this.container.querySelector(".lk-chat") as HTMLElement;
    const launcher = this.container.querySelector(".lk-launcher") as HTMLElement;
    chat.style.display = "flex";
    launcher.style.display = "none";

    // Show welcome message if first open
    if (this.messages.length === 0 && this.config.welcomeMessage) {
      this.addMessage({ type: "bot", text: this.config.welcomeMessage, timestamp: new Date() });
    }
  }

  private close() {
    if (!this.container) return;
    this.isOpen = false;
    const chat = this.container.querySelector(".lk-chat") as HTMLElement;
    const launcher = this.container.querySelector(".lk-launcher") as HTMLElement;
    chat.style.display = "none";
    launcher.style.display = "flex";
  }

  private sendUserMessage(input: HTMLInputElement) {
    const text = input.value.trim();
    if (!text) return;

    this.addMessage({ type: "user", text, timestamp: new Date() });
    input.value = "";

    // Send via WebSocket
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "text",
          text,
          session_id: this.sessionId,
          bot_id: this.config.botId,
          clinic_id: this.config.clinicId,
        })
      );
    }
  }

  private addMessage(msg: ChatMessage) {
    this.messages.push(msg);
    this.renderMessages();
  }

  private renderMessages() {
    if (!this.container) return;
    const messagesEl = this.container.querySelector(".lk-chat__messages");
    if (!messagesEl) return;

    messagesEl.innerHTML = this.messages
      .map(
        (msg) =>
          `<div class="lk-message lk-message--${msg.type}">
            <div class="lk-message__bubble">${this.escapeHtml(msg.text)}</div>
            ${
              msg.buttons
                ? `<div class="lk-message__buttons">
                    ${msg.buttons
                      .map(
                        (btn) =>
                          `<button class="lk-message__btn" data-id="${btn.id}">${this.escapeHtml(btn.title)}</button>`
                      )
                      .join("")}
                  </div>`
                : ""
            }
          </div>`
      )
      .join("");

    messagesEl.scrollTop = messagesEl.scrollHeight;

    // Bind button clicks
    messagesEl.querySelectorAll(".lk-message__btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = (btn as HTMLElement).dataset.id || "";
        const text = btn.textContent || "";
        this.addMessage({ type: "user", text, timestamp: new Date() });
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send(
            JSON.stringify({
              type: "button_click",
              button_id: id,
              button_text: text,
              session_id: this.sessionId,
            })
          );
        }
      });
    });
  }

  private connectWebSocket() {
    const wsUrl = `${this.config.wsUrl}?bot_id=${this.config.botId}&clinic_id=${this.config.clinicId}&session_id=${this.sessionId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "bot_message") {
          this.addMessage({
            type: "bot",
            text: data.text || "",
            buttons: data.buttons,
            timestamp: new Date(),
          });
        }
      };

      this.ws.onclose = () => {
        // Reconnect after 3 seconds
        setTimeout(() => this.connectWebSocket(), 3000);
      };
    } catch {
      // WebSocket not available, widget still shows but messages won't send
    }
  }

  private escapeHtml(text: string): string {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
}

// Auto-initialize from script tag data attributes
(function () {
  const script = document.currentScript as HTMLScriptElement;
  if (!script) return;

  const config: WidgetConfig = {
    botId: script.dataset.botId || "",
    clinicId: script.dataset.clinicId || "",
    position: (script.dataset.position as any) || "bottom-right",
    primaryColor: script.dataset.color || "#2563eb",
    welcomeMessage: script.dataset.welcome || "Olá! Como posso ajudar?",
    launcherText: script.dataset.launcher || "Chat",
  };

  if (config.botId && config.clinicId) {
    new LKChatWidget(config);
  }
})();

export { LKChatWidget };
