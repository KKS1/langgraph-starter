# main.py
from typing import List
from uuid import uuid4
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder
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
                safe_event = jsonable_encoder(event)
                safe_event["thread_id"] = thread_id

                await websocket.send_json(safe_event)
            
            # Send done message (optional)
            await websocket.send_json({"thread_id": thread_id, "type": "done"})

        except WebSocketDisconnect:
            print(f"WebSocket disconnected: {thread_id}")
            break
        except Exception as e:
            await websocket.send_json({"thread_id": thread_id, "type": "error", "message": str(e)})




# --------------------------------------
# 5. Run with uvicorn
# --------------------------------------
if __name__ == "__main__":
    print("Run with: uvicorn main:api --reload --host 0.0.0.0 --port 18000")
