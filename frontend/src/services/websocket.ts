import { AssistantState } from '../types';

type MessageHandler = (data: any) => void;

class AegisWebSocketService {
  private socket: WebSocket | null = null;
  private handlers: Set<MessageHandler> = new Set();
  private reconnectInterval: number = 2000;
  private isConnected: boolean = false;
  private currentAudio: HTMLAudioElement | null = null;

  public connect(url: string = `ws://${window.location.hostname}:8000/ws`) {
    try {
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        this.isConnected = true;
        console.log('[AEGIS WS] Connected to backend engine.');
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleIncoming(data);
        } catch (e) {
          console.error('[AEGIS WS] Parse error:', e);
        }
      };

      this.socket.onclose = () => {
        this.isConnected = false;
        console.warn('[AEGIS WS] Disconnected. Reconnecting in 2s...');
        setTimeout(() => this.connect(url), this.reconnectInterval);
      };

      this.socket.onerror = (err) => {
        console.error('[AEGIS WS] WebSocket error:', err);
      };
    } catch (e) {
      console.error('[AEGIS WS] Connection initiation error:', e);
    }
  }

  public subscribe(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => {
      this.handlers.delete(handler);
    };
  }

  public send(data: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn('[AEGIS WS] Socket not open, failed to send:', data);
    }
  }

  public sendMessage(text: string, isVoice: boolean = false) {
    this.send({
      type: 'message',
      text,
      is_voice: isVoice
    });
  }

  public bargeIn() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    if ('speechSynthesis' in window && window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }
    this.send({ type: 'barge_in' });
  }

  public playAudioBase64(base64Data: string, onEnded?: () => void) {
    try {
      if (this.currentAudio) {
        this.currentAudio.pause();
      }
      const audioUrl = `data:audio/mp3;base64,${base64Data}`;
      this.currentAudio = new Audio(audioUrl);
      this.currentAudio.onended = () => {
        this.currentAudio = null;
        if (onEnded) onEnded();
      };
      this.currentAudio.play().catch((err) => {
        console.warn('[AEGIS Audio] Play notice:', err);
      });
    } catch (e) {
      console.error('[AEGIS Audio] Failed to play audio:', e);
    }
  }

  private handleIncoming(data: any) {
    if (data.audio_base64) {
      this.playAudioBase64(data.audio_base64);
    }
    this.handlers.forEach((h) => h(data));
  }
}

export const wsService = new AegisWebSocketService();
