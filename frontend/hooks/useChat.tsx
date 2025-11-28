import { useEffect, useRef, useState } from 'react';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface Result {
  thread_id: string;
  type: 'update' | 'error' | 'done';
  messages: Message[];
  node?: string;
  content?: string;
}

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [threadId, setThreadId] = useState<string | null>(crypto.randomUUID());
  const wsRef = useRef<WebSocket | null>(null);

  const sendMessage = (message: string) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      console.error(
        'WebSocket is not open. Ready state:',
        wsRef.current?.readyState
      );
      return;
    }
    wsRef.current?.send(JSON.stringify({ content: message }));
  };

  useEffect(() => {
    wsRef.current = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_BASE_URL}/ws/${threadId || ''}`
    );

    wsRef.current.onopen = () => {
      console.log('WebSocket connection established');
    };

    wsRef.current.onmessage = (event) => {
      const result: Result = JSON.parse(event.data);

      if (result.type === 'error') {
        console.error('Error from server:', result.content);
        return;
      }

      if (result.thread_id && result.thread_id !== threadId) {
        setThreadId(result.thread_id);
      }

      if (result.messages) {
        setMessages((prevMessages) => [...prevMessages, ...result.messages]);
      }
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket connection closed');
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      wsRef.current?.close();
    };
  }, [threadId]);

  return { messages, sendMessage };
};

export default useChat;
