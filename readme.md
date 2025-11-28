# LangGraph Starter: Simple LLM Agent

This is a minimal Python prototype using **LangGraph** and **LangChain OpenAI** to create a **stateful LLM agent**. It’s designed for learning and experimentation.

---

## Features

- Simple **single-node LangGraph** workflow
- LLM-powered response using `gpt-4o-mini`
- **Unified response schema** for both POST and WebSocket endpoints
- State stored as a list of messages (`user` / `assistant`)
- Fully compatible with **LangChain 1.1.0** (no `langchain.schema` imports)
- **Memory for multi-turn conversations** using `thread_id`

---

## Prerequisites

- Python 3.10+
- OpenAI API key

---

## Setup

1. **Clone the repository**

```bash
git clone https://github.com/<your-username>/langgraph-starter.git
cd langgraph-starter
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set OpenAI API key**

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-your-api-key-here
```

---

## Run the Agent

```bash
python main.py
```

Run with **uvicorn** for API:

```bash
uvicorn main:api --reload --host 0.0.0.0 --port 18000
```

---

## API Endpoints

### 1. POST `/chat`

Send a user message and get a single response.

- **Request**

```http
POST /chat
Content-Type: application/json

{
  "content": "Tell me a joke"
}
```

- **Query Parameter (optional)**

```
thread_id=<uuid>   # Reuse for multi-turn conversations
```

- **Response (shared with WebSocket)**

```json
{
  "thread_id": "123e4567-e89b-12d3-a456-426614174000",
  "type": "done",
  "messages": [
    { "role": "user", "content": "Tell me a joke" },
    {
      "role": "assistant",
      "content": "Why did the programmer quit his job? Because he didn't get arrays!"
    }
  ],
  "node": "call_llm",
  "content": "Why did the programmer quit his job? Because he didn't get arrays!"
}
```

---

### 2. WebSocket `/ws/{thread_id}`

Real-time chat streaming. Each message from the assistant is sent incrementally.

- **Connect**

```javascript
const ws = new WebSocket('ws://localhost:18000/ws/<thread_id>');
```

- **Send a user message**

```json
{ "content": "Tell me a joke" }
```

- **Responses**

| type     | description                        |
| -------- | ---------------------------------- |
| `update` | Partial/streamed response from LLM |
| `done`   | Final response completed           |
| `error`  | Error message                      |

- **Response format (same as POST)**

```json
{
  "thread_id": "<uuid>",
  "type": "update|done|error",
  "messages": [
    { "role": "user", "content": "Tell me a joke" },
    {
      "role": "assistant",
      "content": "Why did the programmer quit his job? ..."
    }
  ],
  "node": "call_llm",
  "content": "Latest content from assistant"
}
```

---

## Multi-turn Conversations

- Use the same `thread_id` to continue a conversation.
- Both POST and WebSocket endpoints will load previous messages from memory and append new messages automatically.
- Example:

```bash
POST /chat?thread_id=123e4567-e89b-12d3-a456-426614174000
{
  "content": "And another joke?"
}
```

The response will include all previous messages in that thread.

---

## File Structure

```
langgraph-starter/
├─ main.py           # LangGraph agent
├─ requirements.txt  # Python dependencies
├─ .gitignore
└─ README.md
```

---

## Notes

- Keep your `.env` **private** — do NOT commit it to GitHub.
- Both POST and WebSocket share the **same response schema**, making frontend integration easier.
- Memory is automatically handled via `thread_id`.
- Integrated `HumanMessage` / `AIMessage` classes, for advanced workflows leveraging LangChain tooling.

---
