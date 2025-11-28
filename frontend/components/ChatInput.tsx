import { useState } from 'react';

export const ChatInput = ({
  onSend,
}: {
  onSend: (message: string) => void;
}) => {
  const [inputValue, setInputValue] = useState<string>('');

  const handleSend = () => {
    if (inputValue.trim() === '') return;
    onSend(inputValue);
    setInputValue('');
  };

  return (
    <form
      className="flex gap-2 p-4 border-t"
      onSubmit={(e) => {
        e.preventDefault();
        handleSend();
      }}
    >
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        className="flex-1 p-4 border rounded"
        placeholder="Type your message..."
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            handleSend();
          }
        }}
      />
      <button
        onClick={handleSend}
        className="px-4 bg-blue-500 text-white rounded"
      >
        Send
      </button>
    </form>
  );
};
