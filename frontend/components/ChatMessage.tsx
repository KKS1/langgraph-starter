import { Message } from '@/hooks/useChat';

export const ChatMessage = ({ message }: { message: Message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={isUser ? 'text-right self-end' : 'text-left self-start'}>
      <div
        className={`py-2 px-3 rounded-xl inline-block ${
          isUser ? 'bg-blue-500 text-white' : 'bg-gray-200 text-black'
        }`}
      >
        {message.content}
      </div>
    </div>
  );
};

export default ChatMessage;
