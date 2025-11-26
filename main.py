# main.py
from ast import match_case
import stat
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
    topic: str
    keep_going: bool

# --------------------------------------
# 2. Define the nodes (functions)
# --------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini")

def greet(state:State) -> State:
    print("Hello! What do you want to hear today: a joke, trivia, or a quote?")
    user_input = input("You: ")
    state["messages"].append({"role": "user", "content": user_input})
    return state

def select_topic(state:State) -> State:
    last_msg = state["messages"][-1]["content"]
    match last_msg.lower():
        case x if "joke" in x:
            state["topic"] = "joke"
        case x if "trivia" in x:
            state["topic"] = "trivia"
        case x if "quote" in x:
            state["topic"] = "quote"
        case _:
            state["topic"] = "joke"
    print(f"Great Topic: {state['topic']}!!. Here is one coming up...")
    return state
        

def call_llm(state:State) -> State:
    user_messages = state["messages"]
    ai_response = llm.invoke(user_messages)
    user_messages.append({"role": "assistant", "content":  ai_response.content})
    print(f"AI: {ai_response.content}")
    return {"messages": user_messages}


# greet/ get input -> select topic -> call_llm/ show response -> ask_continue -> greet if yes else go to -> summarize

# --------------------------------------
# 3. Build & Compile the graph
# --------------------------------------
builder = StateGraph(State)
builder.add_node("greet", greet)
builder.add_node("call_llm", call_llm)
builder.set_entry_point("greet")
builder.set_finish_point("summarize")
app = builder.compile()

# --------------------------------------
# 4. Run it
# --------------------------------------
if __name__ == "__main__":
    initial_state = {"messages": [], "topic": "", "keep_going": True}
    app.invoke(initial_state)
    
