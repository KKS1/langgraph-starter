'use client';

import { ChatInput } from '@/components/ChatInput';
import { ChatMessages } from '@/components/ChatMessages';
import useChat from '@/hooks/useChat';

export default function ChatPage() {
  const { messages, sendMessage } = useChat();

  return (
    <div className="flex flex-col h-screen max-w-xl mx-auto border rounded shadow m-2">
      <ChatMessages messages={messages} />
      <ChatInput onSend={sendMessage} />
    </div>
  );
}
