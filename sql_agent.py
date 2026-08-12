import os
from dotenv import load_dotenv
from langchain import OpenAI, LLMChain
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.tools import BaseTool
from tools.sql_tools import SQLTools

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("Set OPENAI_API_KEY in environment or .env file")

# Wrap SQLTools methods as LangChain Tools
sqltools = SQLTools(db_path="example.db", readonly=True)

class SchemaTool(BaseTool):
    name = "get_schema"
    description = "Returns database schema: tables and CREATE statements. Use for exploration."

    def _run(self, query: str):
        return sqltools.get_schema()

    async def _arun(self, query: str):
        return self._run(query)

class RunSQLTool(BaseTool):
    name = "run_sql"
    description = "Executes a read-only SQL query (SELECT/PRAGMA). Input is a SQL string. Returns tabulated rows or error."

    def _run(self, query: str):
        out, cols = sqltools.run_sql(query)
        return out

    async def _arun(self, query: str):
        return self._run(query)

class ExplainTool(BaseTool):
    name = "explain_sql"
    description = "Returns an EXPLAIN QUERY PLAN for a SQL query."

    def _run(self, query: str):
        return sqltools.explain_sql(query)

    async def _arun(self, query: str):
        return self._run(query)

def main():
    llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
    tools = [
        Tool.from_function(sqltools.get_schema, name="get_schema", description="get database schema"),
        Tool.from_function(lambda q: sqltools.run_sql(q)[0], name="run_sql", description="execute read-only SQL and return results (string)"),
        Tool.from_function(sqltools.explain_sql, name="explain_sql", description="return EXPLAIN QUERY PLAN for SQL")
    ]

    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

    print("SQL ReAct agent ready. Try asking questions like:")
    print(" - 'List tables and tell me how many users are in the users table.'")
    print(" - 'Show the total amount per user for paid orders.'")
    while True:
        prompt = input("\nUser> ").strip()
        if not prompt:
            continue
        if prompt.lower() in ("exit", "quit"):
            break
        result = agent.run(prompt)
        print("\nAgent final answer:\n", result)

if __name__ == "__main__":
    main()
