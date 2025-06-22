import asyncio
import json
import os
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # 从 .env 加载环境变量


class MCPClient:
    def __init__(self):
        # 初始化会话和客户端对象
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.client = OpenAI(api_key=os.environ.get("deepseek_api_key"), base_url="https://api.deepseek.com")

    # 方法将在这里添加

    async def connect_to_server(self, server_script_path: str):
        """连接到 MCP 服务器

        Args:
            server_script_path: 服务器脚本的路径 (.py 或 .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("服务器脚本必须是 .py 或 .js 文件")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # 列出可用的工具
        response = await self.session.list_tools()
        tools = response.tools
        print("\n已连接到服务器，工具包括：", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """使用 Claude 和可用的工具处理查询"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{"type": "function", "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema
        }} for tool in response.tools]
        # print(available_tools)

        # 初始 Claude API 调用
        # response = self.client.messages.create(
        #     model="claude-3-5-sonnet-20241022",
        #     max_tokens=1000,
        #     messages=messages,
        #     tools=available_tools
        # )

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=available_tools,
            stream=False
        )
        # print(response)

        # 处理响应并处理工具调用
        final_text = []

        assistant_message_content = []
        for content in response.choices:
            if content.finish_reason == 'stop':
                final_text.append(content.message.content)
                assistant_message_content.append(content)
            elif content.finish_reason == 'tool_calls':
                tool_name = content.message.tool_calls[0].function.name
                tool_args = content.message.tool_calls[0].function.arguments

                tool_args_dict = json.loads(tool_args)

                # 执行工具调用
                result = await self.session.call_tool(tool_name, tool_args_dict)
                final_text.append(f"[调用工具 {tool_name}，参数 {tool_args}]")
                # assistant_message_content.append(json.dumps(content))
                # messages.append({
                #     "role": "assistant",
                #     "content": assistant_message_content
                # })
                messages.append({
                    "role": "user",
                    #  deepseek 的content内容必须为字符串,否则解析会错误
                    "content": json.dumps([
                        {
                            "type": "tool_result",
                            "tool_use_id": "0",
                            "content": result.content[0].text
                        }
                    ])
                })
                # 获取 Claude 的下一个响应
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    tools=available_tools,
                    stream=False
                )
                final_text.append(response.choices[0].message.content)

        return "\n".join(final_text)

    async def chat_loop(self):
        """运行交互式聊天循环"""
        print("\nMCP 客户端已启动！")
        print("输入你的查询或输入 'quit' 退出。")

        while True:
            try:
                query = input("\n查询: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\n错误: {str(e)}")

    async def cleanup(self):
        """清理资源"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("使用方法: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
