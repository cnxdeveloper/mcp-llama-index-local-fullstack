from llama_index.llms.openai import OpenAI
from llama_index.llms.openllm import OpenLLM
from llama_index.llms.openrouter import OpenRouter
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from dotenv import load_dotenv
import anyio
import os

load_dotenv()

BASE_URL = os.getenv("LLM_HOST")
API_KEY =  os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")

print(BASE_URL, API_KEY, LLM_MODEL)
llm = OpenRouter(
    api_base=BASE_URL,
    api_key=API_KEY,
    max_tokens=30000,
    context_window=30000,
    model=LLM_MODEL,
    is_function_calling_model=True
)

from llama_index.tools.mcp import McpToolSpec
from llama_index.core.agent.workflow import FunctionAgent, ToolCallResult, ToolCall
from llama_index.core.workflow import Context

SYSTEM_PROMPT = """\
You are an AI assistant for Tool Calling.

Before you help a user, you need to work with tools to interact with Our Database,
"""


async def get_agent(tools: McpToolSpec):
    tools = await tools.to_tool_list_async()
    agent = FunctionAgent(
        name="Agent",
        description="An agent that can work with Our Database software.",
        tools=tools,
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
    )
    return agent


async def handle_user_message(
    message_content: str,
    agent: FunctionAgent,
    agent_context: Context,
    verbose: bool = False,
):
    handler = agent.run(message_content, ctx=agent_context)
    async for event in handler.stream_events():
        if verbose and type(event) == ToolCall:
            print("CNX calling")
            print(f"CNX Calling tool {event.tool_name} with kwargs {event.tool_kwargs}")
        elif verbose and type(event) == ToolCallResult:
            print(f"Tool {event.tool_name} returned {event.tool_output}")

    response = await handler
    return str(response)


async def main():
    mcp_client = BasicMCPClient("http://127.0.0.1:8180/sse")
    mcp_tool = McpToolSpec(client=mcp_client)
    tools = await mcp_tool.to_tool_list_async()
    print(len(tools))
    for tool in tools:
        print(tool.metadata.name, tool.metadata.description)
        print(len(tool.metadata.description))

    # get the agent
    agent = await get_agent(mcp_tool)
    # create the agent context
    agent_context = Context(agent)

    while True:
        user_input = input("Enter your message: ")
        if user_input == "exit":
            break
        print("CNX User: ", user_input)
        response = await handle_user_message(user_input, agent, agent_context, verbose=False)
        print("CNX Agent: ", response)
        
        
if __name__ == "__main__":
    anyio.run(main)