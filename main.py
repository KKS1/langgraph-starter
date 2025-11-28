# main.py
from enum import Enum
from typing import List, Optional
from uuid import uuid4
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

load_dotenv()
memory = MemorySaver()

# --------------------------------------
# 1. Define the state that flows between nodes
# --------------------------------------
class Message(BaseModel):
    role: str
    content: str

class State(BaseModel):
    messages: List[Message] = []

#  utility functions
def add_message(state:State, role:str, content:str) -> State:
    state.messages.append(Message(role=role, content=content))
    return state

# --------------------------------------
# 2. Define the nodes (functions)
# --------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini")
        
async def call_llm(state:State) -> State:
    ai_response = await llm.ainvoke([msg.model_dump() for msg in state.messages])
    state = add_message(state, "assistant", ai_response.content)
    return state

# --------------------------------------
# 3. Build & Compile the graph
# --------------------------------------
builder = StateGraph(State)
builder.add_node("call_llm", call_llm)
builder.set_entry_point("call_llm")
app = builder.compile(checkpointer=memory)

# --------------------------------------
# 4. Create FastAPI app
# --------------------------------------
api = FastAPI(title="LangGraph Chat API", description="LangGraph Chat API", version="0.1.0")

# input/output models
class UserInput(BaseModel):
    content: str = "Tell me a joke"

class Result(State):
    thread_id: str

# Post API endpoint for chat interactions
@api.post("/chat")
async def chat(user_input: UserInput, thread_id: str = None) -> Result:
    if thread_id is None:
        thread_id = str(uuid4())

    saved = memory.get({"configurable": {"thread_id": thread_id}})
    prev = saved["channel_values"]["messages"] if saved else []
    state = State(messages=prev)
    state = add_message(state, "user", user_input.content)
    result = await app.ainvoke(state.model_dump(), config={"configurable": {"thread_id": thread_id}})
    return Result(**result, thread_id=thread_id) 

class WSResponseType(str, Enum):
    UPDATE = "update"
    DONE = "done"
    ERROR = "error"
class WSResponse(BaseModel):
    thread_id: str
    type: WSResponseType
    messages: List[Message] = []
    node: Optional[str] = None  # optional, which node emitted this
    content: Optional[str] = None  # optional latest assistant content

# WebSocket endpoint for real-time chat
@api.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_json()
            user_input = UserInput(**data)
            saved = memory.get({"configurable": {"thread_id": thread_id}})
            prev = []

            if saved and "channel_values" in saved and "messages" in saved["channel_values"]:
                prev = [ msg.model_dump() for msg in saved["channel_values"]["messages"]]

            state = State(messages=prev)
            state = add_message(state, "user", user_input.content)

            # Stream assistant response
            async for event in app.astream(state.model_dump(), config={"configurable": {"thread_id": thread_id}}):
                # Flatten event: if dict has single node key, unwrap it
                inner = list(event.values())[0] if len(event) == 1 else event
                messages = [msg if isinstance(msg, dict) else msg.model_dump() for msg in inner.get("messages", [])]

                ws_payload = WSResponse(
                    thread_id=thread_id,
                    type=WSResponseType.UPDATE,
                    messages=messages,
                    node=inner.get("node", "call_llm"),
                    content=messages[-1]["content"] if messages else None
                )

                await websocket.send_json(ws_payload.model_dump())
            
            # Send done message (optional)
            await websocket.send_json(WSResponse(thread_id=thread_id, type=WSResponseType.DONE).model_dump())

        except WebSocketDisconnect:
            print(f"WebSocket disconnected: {thread_id}")
            break
        except Exception as e:
            await websocket.send_json(WSResponse(thread_id=thread_id, type=WSResponseType.ERROR, content=str(e)).model_dump())


# --------------------------------------
# 5. Run with uvicorn
# --------------------------------------
if __name__ == "__main__":
    print("Run with: uvicorn main:api --reload --host 0.0.0.0 --port 18000")
