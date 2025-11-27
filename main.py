# main.py
from ast import match_case
from concurrent.futures import thread
from re import M
from typing import Dict, List
from unittest.mock import Base
from uuid import uuid4
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from fastapi import FastAPI

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
    topic: str = ""
    keep_going: bool = True

#  utility functions
def add_message(state:State, role:str, content:str) -> State:
    state.messages.append(Message(role=role, content=content))
    return state

# --------------------------------------
# 2. Define the nodes (functions)
# --------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini")

def greet_user(state:State) -> State:
    greeting_msg = "Hello! What do you want to hear today: a joke, trivia, or a quote?"
    state = add_message(state, "assistant", greeting_msg)
    print(greeting_msg)
    user_input = input("You: ")
    state = add_message(state, "user", user_input)
    return state

def select_topic(state:State) -> State:
    last_msg = state.messages[-1].content
    match last_msg.lower():
        case x if "joke" in x:
            state.topic = "joke"
        case x if "trivia" in x:
            state.topic = "trivia"
        case x if "quote" in x:
            state.topic = "quote"
        case _:
            state.topic = "joke"
    print(f"Great Topic: {state.topic}!!")
    return state
        

def call_llm(state:State) -> State:
    prompt = f"Tell me a {state.topic}"
    state = add_message(state, "user", prompt)
    ai_response = llm.invoke([msg.model_dump() for msg in state.messages])
    state = add_message(state, "assistant", ai_response.content)
    print(f"AI: {ai_response.content}")
    return state

def ask_continue(state:State) -> State:
    continue_prompt = "Do you want to continue with the conversation (y/n)?"
    state = add_message(state, "assistant", continue_prompt)
    print(continue_prompt)
    user_input = input("Yes(y)/No(n): ").strip().lower()
    state = add_message(state, "user", user_input)
    state.keep_going = user_input.startswith("y")
    return state

def summarize(state:State) -> State:
    summary_prompt = "Summarize the conversation in one sentence."
    state = add_message(state, "user", summary_prompt)
    summary = llm.invoke([msg.model_dump() for msg in state.messages])
    state = add_message(state, "assistant", summary.content)
    print(f"Summary: {summary.content}")
    state.keep_going = False
    return state

# --------------------------------------
# 3. Build & Compile the graph
# --------------------------------------
builder = StateGraph(State)
builder.add_node("greet", greet_user)
builder.add_node("select_topic", select_topic)
builder.add_node("call_llm", call_llm)
builder.add_node("ask_continue", ask_continue)
builder.add_node("summarize", summarize)

builder.add_edge("greet", "select_topic")
builder.add_edge("select_topic", "call_llm")
builder.add_edge("call_llm", "ask_continue")

builder.add_conditional_edges("ask_continue", lambda state: "greet" if state.keep_going else "summarize")

builder.set_entry_point("greet")
builder.set_finish_point("summarize")
app = builder.compile(checkpointer=memory)

# --------------------------------------
# 4. Run it on console and save the graph (Uncomment if needed)
# --------------------------------------
""" if __name__ == "__main__":
    initial_state = {"messages": [], "topic": "", "keep_going": True}
    thread_id = str(uuid4())
    app.invoke(initial_state, config={"configurable": {"thread_id": thread_id}})
    png_bytes = app.get_graph().draw_mermaid_png()

    with open("graph.png", "wb") as f:
        f.write(png_bytes)

    print("Graph saved to graph.png")

    saved_memory = memory.get({"configurable": {"thread_id": thread_id}})
    print(f"Saved memory: {saved_memory}") """

# --------------------------------------
# 4. Create FastAPI app
# --------------------------------------
api = FastAPI(title="LangGraph Chat API", description="LangGraph Chat API", version="0.1.0")

class UserInput(BaseModel):
    content: str
    continue_conversation: bool = True

@api.post("/chat")
async def chat(user_input: UserInput, thread_id: str = None):
    if thread_id is None:
        thread_id = str(uuid4())
    state = State(messages=[Message(role="user", content=user_input.content)], keep_going=user_input.continue_conversation)
    result = app.invoke(state.model_dump(), config={"configurable": {"thread_id": str(uuid4())}})
    # return thread_id also along with result

    return {
        "thread_id": thread_id,
        "messages": [msg.model_dump() for msg in result["messages"]],
        "keep_going": result["keep_going"],
        "last_topic": result["topic"],
    }

# --------------------------------------
# 5. Run with uvicorn
# --------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=18000)