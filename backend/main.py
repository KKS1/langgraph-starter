from enum import Enum
from typing import List, Optional
from uuid import uuid4
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, AIMessage, AnyMessage
from pydantic import BaseModel
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

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

# Utility to add messages to state
def add_message(state: State, role: str, content: str) -> State:
    state.messages.append(Message(role=role, content=content))
    return state

# Convert State.messages -> LangChain messages
def state_to_lc_msgs(state: State) -> List[AnyMessage]:
    lc_msgs = []
    for msg in state.messages:
        if msg.role == "user":
            lc_msgs.append(HumanMessage(content=msg.content))
        else:
            lc_msgs.append(AIMessage(content=msg.content))
    return lc_msgs

# Convert LangChain messages -> State.messages dicts
def lc_msgs_to_state(msgs: List[AnyMessage]) -> List[Message]:
    res = []
    for msg in msgs:
        if isinstance(msg, HumanMessage):
            res.append(Message(role="user", content=msg.content))
        elif isinstance(msg, AIMessage):
            res.append(Message(role="assistant", content=msg.content))
    return res

# --------------------------------------
# 2. Define the nodes (functions)
# --------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini")

async def call_llm(state: State) -> State:
    lc_msgs = state_to_lc_msgs(state)
    ai_response = await llm.ainvoke(lc_msgs)
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

origins = [
    "http://localhost:3000",
    # "https://your-frontend-domain.com", 
]

api.add_middleware(
    CORSMiddleware,
    allow_origins='*',         # Allows requests from the origins list
    allow_credentials=True,        # Allows cookies/auth headers to be included in requests
    allow_methods=["*"],           # Allows all standard methods (GET, POST, etc.)
    allow_headers=["*"],           # Allows all headers
)

# Input/output models
class UserInput(BaseModel):
    content: str = "Tell me a joke"

class ResponseType(str, Enum):
    UPDATE = "update"
    DONE = "done"
    ERROR = "error"

class Result(BaseModel):
    thread_id: str
    type: ResponseType
    messages: List[Message] = []
    node: Optional[str] = None
    content: Optional[str] = None

# --------------------
# POST /chat endpoint
# --------------------
@api.get("/messages/{thread_id}")
async def get_messages(thread_id: str) -> List[Message]:
    saved = memory.get({"configurable": {"thread_id": thread_id}})
    if saved and "channel_values" in saved and "messages" in saved["channel_values"]:
        return [msg.model_dump() for msg in saved["channel_values"]["messages"]]
    return []

@api.post("/chat")
async def chat(user_input: UserInput, thread_id: str = None) -> Result:
    if thread_id is None:
        thread_id = str(uuid4())

    saved = memory.get({"configurable": {"thread_id": thread_id}})
    prev = []
    if saved and "channel_values" in saved and "messages" in saved["channel_values"]:
        prev = [msg.model_dump() for msg in saved["channel_values"]["messages"]]

    state = State(messages=prev)
    state = add_message(state, "user", user_input.content)
    try:
        result = await app.ainvoke(state.model_dump(), config={"configurable": {"thread_id": thread_id}})
        messages = [msg if isinstance(msg, dict) else msg.model_dump() for msg in result.get("messages", [])]

        return Result(
            thread_id=thread_id,
            type=ResponseType.DONE,
            messages=messages,
            node="call_llm",
            content=messages[-1]["content"] if messages else None
        )
    except Exception as e:
        return Result(
            thread_id=thread_id,
            type=ResponseType.ERROR,
            messages=[],
            node="call_llm",
            content=str(e)
        )

# --------------------
# WebSocket /ws/{thread_id}
# --------------------
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
                prev = [msg.model_dump() for msg in saved["channel_values"]["messages"]]

            state = State(messages=prev)
            state = add_message(state, "user", user_input.content)

            async for event in app.astream(state.model_dump(), config={"configurable": {"thread_id": thread_id}}):
                inner = list(event.values())[0] if len(event) == 1 else event
                messages = [msg if isinstance(msg, dict) else msg.model_dump() for msg in inner.get("messages", [])]

                ws_payload = Result(
                    thread_id=thread_id,
                    type=ResponseType.UPDATE,
                    messages=messages,
                    node=inner.get("node", "call_llm"),
                    content=messages[-1]["content"] if messages else None
                )

                await websocket.send_json(ws_payload.model_dump())

            # await websocket.send_json(Result(thread_id=thread_id, type=ResponseType.DONE, messages=messages, node="call_llm", content=messages[-1]["content"] if messages else None).model_dump())

        except WebSocketDisconnect:
            print(f"WebSocket disconnected: {thread_id}")
            break
        except Exception as e:
            await websocket.send_json(Result(thread_id=thread_id, type=ResponseType.ERROR, content=str(e)).model_dump())


# --------------------------------------
# 5. Run with uvicorn
# --------------------------------------
if __name__ == "__main__":
    print("Run with: uvicorn main:api --reload --host 0.0.0.0 --port 18000")
