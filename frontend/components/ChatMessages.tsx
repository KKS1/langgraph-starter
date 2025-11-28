import { Message } from '@/hooks/useChat';
import ChatMessage from './ChatMessage';

export const ChatMessages = ({ messages }: { messages: Message[] }) => {
  return (
    <div className="flex flex-col gap-2 p-4 overflow-y-auto flex-1">
      {messages.map((msg, index) => (
        <ChatMessage key={index} message={msg} />
      ))}
    </div>
  );
};
