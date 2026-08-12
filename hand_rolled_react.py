import os
import re
from dotenv import load_dotenv
import openai
from tools.sql_tools import SQLTools

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
sqltools = SQLTools("example.db", readonly=True)

SYSTEM = """You are a helpful SQL assistant that follows the ReAct format. Use tools when needed.
When you decide to call a tool, emit exactly:
Thought: <your thought>
Action: <tool_name>
Action Input: <input>
Then wait for the observation text (the tool output), then continue.
When ready to finish, output:
Final Answer: <answer>
Allowed tools: get_schema, run_sql, explain_sql
Only call tools for DB inspection or running queries. Do not fabricate tool outputs.
"""

TOOL_DOCS = {
    "get_schema": "returns database schema (tables and CREATE statements). Input ignored.",
    "run_sql": "runs a read-only SQL query; input is SQL. Returns table or error.",
    "explain_sql": "returns EXPLAIN QUERY PLAN for SQL; input is SQL."
}

def call_llm(messages, max_tokens=300):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini", # change to available model
        messages=messages,
        max_tokens=max_tokens,
        temperature=0
    )
    return response["choices"][0]["message"]["content"]

def run_react(user_input):
    messages = [{"role":"system","content":SYSTEM},
                {"role":"user","content":f"{user_input}\n\nTools:\n" + "\n".join(f"{k}: {v}" for k,v in TOOL_DOCS.items())}]
    while True:
        assistant_text = call_llm(messages)
        print("\nAssistant reply:\n", assistant_text)
        messages.append({"role":"assistant","content":assistant_text})
        # parse Action if present
        m_action = re.search(r"Action:\s*(\w+)", assistant_text)
        if m_action:
            tool = m_action.group(1).strip()
            m_input = re.search(r"Action Input:\s*(.+)", assistant_text, flags=re.S)
            tool_input = m_input.group(1).strip() if m_input else ""
            if tool == "get_schema":
                obs = sqltools.get_schema()
            elif tool == "run_sql":
                obs, _ = sqltools.run_sql(tool_input)
            elif tool == "explain_sql":
                obs = sqltools.explain_sql(tool_input)
            else:
                obs = f"Unknown tool: {tool}"
            print(f"\nObservation (from tool {tool}):\n{obs}")
            messages.append({"role":"system","content":f"Observation: {obs}"})
            # continue loop for next thought/action
            # If assistant already included Final Answer, break
            if "Final Answer:" in assistant_text:
                break
        else:
            # No action found; if assistant gave Final Answer, break
            if "Final Answer:" in assistant_text:
                break
            # else let loop continue with LLM call (but avoid infinite loop)
            messages.append({"role":"system","content":"No tool called. If you need data, call a tool. Otherwise provide the final answer."})
    return messages[-1]["content"]

if __name__ == "__main__":
    while True:
        q = input("User> ").strip()
        if q.lower() in ("exit","quit"):
            break
        run_react(q)
