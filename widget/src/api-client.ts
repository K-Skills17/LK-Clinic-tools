/**
 * LK Clinic Tools - Widget API Client
 * WebSocket connection management for the chat widget.
 */

export interface WebSocketConfig {
  url: string;
  botId: string;
  clinicId: string;
  sessionId: string;
  onMessage: (data: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export class WidgetApiClient {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;

  constructor(config: WebSocketConfig) {
    this.config = config;
  }

  connect(): void {
    const params = new URLSearchParams({
      bot_id: this.config.botId,
      clinic_id: this.config.clinicId,
      session_id: this.config.sessionId,
    });

    const url = `${this.config.url}?${params.toString()}`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.config.onConnect?.();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.config.onMessage(data);
        } catch {
          // Invalid JSON, ignore
        }
      };

      this.ws.onclose = () => {
        this.config.onDisconnect?.();
        this.attemptReconnect();
      };

      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch {
      this.attemptReconnect();
    }
  }

  send(data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect(): void {
    this.maxReconnectAttempts = 0; // Prevent reconnection
    this.ws?.close();
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;

    this.reconnectAttempts++;
    setTimeout(() => this.connect(), this.reconnectDelay);
  }
}
