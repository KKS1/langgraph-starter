# main.py
from typing import Dict, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langgraph.graph import StateGraph

load_dotenv()

# --------------------------------------
# 1. Define the state that flows between nodes
# --------------------------------------
class State(TypedDict):
    messages: List[Dict[str, str]]

# --------------------------------------
# 2. Define the nodes (functions)
# --------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini")

def call_llm(state:State) -> State:
    user_messages = state["messages"]
    ai_response = llm.invoke(user_messages)
    user_messages.append({"role": "assistant", "content":  ai_response.content})
    return {"messages": user_messages}

# --------------------------------------
# 3. Build & Compile the graph
# --------------------------------------
builder = StateGraph(State)
builder.add_node("call_llm", call_llm)
builder.set_entry_point("call_llm")
builder.set_finish_point("call_llm")
app = builder.compile()

# --------------------------------------
# 4. Run it
# --------------------------------------
if __name__ == "__main__":
    initial_message = {"messages": [{"role": "user", "content": "Give a geek joke."}]}
    result = app.invoke(initial_message)
    print("\n AI response:")
    print(result["messages"][-1]["content"])
