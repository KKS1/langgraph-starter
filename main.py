# main.py
from ast import match_case
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

def greet_user(state:State) -> State:
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
    print(f"Great Topic: {state['topic']}!!")
    return state
        

def call_llm(state:State) -> State:
    prompt = f"Tell me a {state['topic']}"
    state["messages"].append({"role": "user", "content": prompt})
    ai_response = llm.invoke(state["messages"])
    state["messages"].append({"role": "assistant", "content":  ai_response.content})
    print(f"AI: {ai_response.content}")
    return state

def ask_continue(state:State) -> State:
    print("Do you want to continue? (yes/no)")
    user_input = input("Yes(y)/No(n): ").strip().lower()
    state["messages"].append({"role": "user", "content": user_input})
    state["keep_going"] = user_input.startswith("y")
    return state

def summarize(state:State) -> State:
    summary_prompt = "Summarize the conversation in one sentence."
    state["messages"].append({"role": "user", "content": summary_prompt})
    summary = llm.invoke(state["messages"])
    print(f"Summary: {summary.content}")
    state["keep_going"] = False
    return state

def summarize_or_continue(state:State) -> State:
    return "greet" if state["keep_going"] else "summarize"

# greet/ get input -> select topic -> call_llm/ show response -> ask_continue -> greet if yes else go to -> summarize

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

builder.add_conditional_edges("ask_continue", summarize_or_continue)

builder.set_entry_point("greet")
builder.set_finish_point("summarize")
app = builder.compile()

# --------------------------------------
# 4. Run it
# --------------------------------------
if __name__ == "__main__":
    initial_state = {"messages": [], "topic": "", "keep_going": True}
    app.invoke(initial_state)
    
