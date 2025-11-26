# LangGraph Starter: Simple LLM Agent

This is a minimal Python prototype using **LangGraph** and **LangChain OpenAI** to create a stateful LLM agent. It’s designed for learning and experimentation.

---

## Features

- Simple **single-node LangGraph** workflow
- LLM-powered response using `gpt-4o-mini`
- State stored as a list of messages (`user` / `assistant`)
- Fully compatible with **LangChain 1.1.0** (no `langchain.schema` imports)

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

Expected output:

```
AI response:
Why did the programmer quit his job? Because he didn't get arrays!
```

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
- This prototype uses **dicts for messages**, compatible with LangChain 1.1.0.
- For advanced workflows, consider upgrading LangChain and using `HumanMessage` / `AIMessage` classes.

---

## Next Steps

- Add multiple nodes / branching in LangGraph
- Integrate tools or function calls
- Add memory for multi-turn conversations