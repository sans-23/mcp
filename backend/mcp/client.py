import json
import asyncio
import logging
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict, Optional

import google.generativeai as genai # type: ignore
from dotenv import load_dotenv # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.future import select # type: ignore
from sqlalchemy.exc import SQLAlchemyError # type: ignore

from mcp import ClientSession # type: ignore
from mcp.client.streamable_http import streamablehttp_client # type: ignore
from backend.models.models import ChatSession, ChatMessage

class MCPClient:
    def __init__(self, config_path: str = "mcp.json"):
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()

        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

        self.config_path = config_path
        self.all_tools: list[Dict[str, Any]] = []
        self.gemini_tools: list[genai.protos.FunctionDeclaration] = []
        self.connection_retries = 3
        self.timeout = 60

    async def load_config(self) -> Dict[str, Any]:
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file {self.config_path} does not exist.")
        with open(config_file, 'r') as file:
            config_data = json.load(file)
        return config_data

    async def connect_to_servers(self) -> None:
        config = await self.load_config()
        servers = config.get("servers", {})

        if not servers:
            raise ValueError("No servers found in configuration.")

        successful_connections = 0
        for server_name, server_info in servers.items():
            try:
                await self.connect_to_server(server_name, server_info)
                successful_connections += 1
            except Exception as e:
                print(f"Failed to connect to {server_name}: {e}")

        if successful_connections == 0:
            raise ConnectionError("Failed to connect to any servers.")
        await self.aggregate_tools()

    async def connect_to_server(self, server_name: str, server_info: Dict[str, Any]) -> None:
        url = server_info.get("url")
        headers = server_info.get("headers", {})

        if not url:
            raise ValueError(f"Server {server_name} does not have a valid URL.")

        try:
            streamable_transport = await self.exit_stack.enter_async_context(
                streamablehttp_client(url, headers=headers)
            )

            read_stream, write_stream, _ = streamable_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            try:
                await asyncio.wait_for(session.initialize(), timeout=self.timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Connection to {server_name} timed out.")
            except Exception as e:
                raise ConnectionError(f"Failed to initialize session with {server_name}: {e}")

            self.sessions[server_name] = session
            response = await session.list_tools()
            tools = response.tools
            return

        except Exception as e:
            raise ConnectionError(f"Failed to connect to {server_name}: {e}")

    async def aggregate_tools(self) -> None:
        self.all_tools = []
        for server_name, session in self.sessions.items():
            try:
                response = await session.list_tools()
                for tool in response.tools:
                    tool_info = {
                        "name": f"{server_name}_{tool.name}",
                        "original_name": tool.name,
                        "server": server_name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    self.all_tools.append(tool_info)
            except Exception as e:
                print(f"Failed to retrieve tools from {server_name}: {e}")

    def get_tools_summary(self) -> str:
        if not self.all_tools:
            return "No tools available."

        # Group tools by server
        servers = {}
        summary_lines = ["Available Tools:"]

        for tool in self.all_tools:
            server = tool['server']
            if server not in servers:
                servers[server] = []

        for tool in self.all_tools:
            servers[tool['server']].append(tool)

        for server_name, tools in servers.items():
            summary_lines.append(f"\nServer: {server_name} with {len(tools)} tools:")
            for tool in tools:
                summary_lines.append(f"  - {tool['original_name']}: {tool['description']}")
        return "\n".join(summary_lines)

    async def get_or_create_chat_session(self, db: AsyncSession, chat_id: Optional[str] = None) -> tuple[str, genai.ChatSession]:
        chat_session = None
        if chat_id:
            try:
                result = await db.execute(select(ChatSession).where(ChatSession.id == chat_id))
                chat_session = result.scalars().first()
            except SQLAlchemyError as e:
                print(f"Database query error: {e}")
                chat_session = None

        if not chat_session:
            new_chat_id = os.urandom(8).hex()
            chat_session = ChatSession(id=new_chat_id)
            db.add(chat_session)
            await db.commit()
            await db.refresh(chat_session)
            print(f"Created new chat with ID: {new_chat_id}")
        else:
            print(f"Resuming chat with ID: {chat_id}")

        # Reconstruct the chat history from the database
        history_result = await db.execute(
            select(ChatMessage).where(ChatMessage.chat_session_id == chat_session.id).order_by(ChatMessage.created_at)
        )
        history = history_result.scalars().all()

        # Correct the role for the genai library
        genai_history = []
        for msg in history:
            # The genai library expects 'model' for bot responses
            genai_role = 'model' if msg.role == 'bot' else msg.role
            
            # Ensure the content is in the correct format with a role key
            content_with_role = {
                "role": genai_role,
                "parts": msg.content["parts"]  # Access the 'parts' key from the JSON content
            }
            genai_history.append(content_with_role)

        # Create the genai chat session with the loaded history
        genai_chat = self.model.start_chat(
            enable_automatic_function_calling=True,
            history=genai_history
        )

        return chat_session.id, genai_chat

    async def _save_message_to_db(self, db: AsyncSession, chat_id: str, role: str, content: Any) -> None:
        try:
            message = ChatMessage(
                chat_session_id=chat_id,
                role=role,
                content=content
            )
            db.add(message)
            await db.commit()
            await db.refresh(message)
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Failed to save message to database: {e}")

    async def process_query(self, db: AsyncSession, chat_id: str, query: str) -> str:
        if not self.all_tools:
            return "No tools available to process the query."
        
        # We need to save the user's message before getting the response
        await self._save_message_to_db(db, chat_id, 'user', {"parts": [{"text": query}]})

        # Re-fetch the chat session and history to ensure it's up-to-date
        # This is crucial for a robust system with concurrent requests
        chat_id, chat_session = await self.get_or_create_chat_session(db, chat_id)

        try:
            response = chat_session.send_message(
                query,
                tools=self.gemini_tools,
                tool_config={
                    "function_calling_config": {
                        "mode": "AUTO"
                    }
                }
            )

            final_text = []

            if response.candidates and response.candidates[0].content.parts:
                # Prepare the model's response for database storage
                response_content_dict = {
                    "parts": [
                        p.to_dict() if hasattr(p, 'to_dict') else {"text": p.text}
                        for p in response.candidates[0].content.parts
                    ],
                    "role": "model"
                }

                # Save the bot's response to the database
                await self._save_message_to_db(db, chat_id, 'bot', response_content_dict)

                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text != "":
                        final_text.append(part.text)
                    elif hasattr(part, 'function_call'):
                        tool_result = await self._execute_gemini_tool_call(part.function_call)
                        if tool_result:
                            function_response = genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=part.function_call.name,
                                    response={"result": tool_result}
                                )
                            )

                            follow_up_response = chat_session.send_message(function_response)

                            # Save the follow-up response to the database
                            follow_up_content_dict = {
                                "parts": [
                                    p.to_dict() if hasattr(p, 'to_dict') else {"text": p.text}
                                    for p in follow_up_response.candidates[0].content.parts
                                ],
                                "role": "model"
                            }
                            await self._save_message_to_db(db, chat_id, 'bot', follow_up_content_dict)

                            if follow_up_response.candidates and follow_up_response.candidates[0].content.parts:
                                for follow_up_part in follow_up_response.candidates[0].content.parts:
                                    if hasattr(follow_up_part, 'text') and follow_up_part.text:
                                        final_text.append(follow_up_part.text)

            return "\n".join(final_text) if final_text else "No response generated."

        except Exception as e:
            # Catching a general exception and logging it
            print(f"Error processing query: {e}")
            return f"Error processing query: {e}"

    def _convert_json_type_to_genai(self, prop_schema: str) -> genai.protos.Schema:
        """
        Recursively converts a JSON schema type definition to a genai.protos.Schema.
        """
        json_type = prop_schema.get('type')
        description = prop_schema.get('description', '')

        if json_type == 'string':
            return genai.protos.Schema(type=genai.protos.Type.STRING, description=description)
        elif json_type == 'integer':
            return genai.protos.Schema(type=genai.protos.Type.INTEGER, description=description)
        elif json_type == 'number':
            return genai.protos.Schema(type=genai.protos.Type.NUMBER, description=description)
        elif json_type == 'boolean':
            return genai.protos.Schema(type=genai.protos.Type.BOOLEAN, description=description)
        elif json_type == 'array':
            item_schema = prop_schema.get('items', {})
            return genai.protos.Schema(
                type=genai.protos.Type.ARRAY,
                description=description,
                items=self._convert_json_type_to_genai(item_schema)
            )
        elif json_type == 'object':
            properties = {
                prop_name: self._convert_json_type_to_genai(prop_val)
                for prop_name, prop_val in prop_schema.get('properties', {}).items()
            }
            return genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                description=description,
                properties=properties,
                required=prop_schema.get('required', [])
            )
        else:
            return genai.protos.Schema(type=genai.protos.Type.STRING, description=description)

    async def _execute_gemini_tool_call(self, function_call: genai.protos.FunctionCall) -> Any:
        tool_name = function_call.name
        tool_args = function_call.args

        print(f"Invoking tool: {tool_name} with arguments: {tool_args}")

        tool_info = next((tool for tool in self.all_tools if tool['name'] == tool_name), None)
        if not tool_info:
            return f"Tool {tool_name} not found."

        server_name = tool_info['server']
        original_tool_name = tool_info['original_name']
        session = self.sessions.get(server_name)
        if not session:
            return f"Session for server {server_name} not found."

        try:
            result = await session.call_tool(original_tool_name, tool_args)
            if hasattr(result, 'content'):
                if isinstance(result.content, str):
                    return result.content
                elif isinstance(result.content, list):
                    content_parts = []
                    for item in result.content:
                        if hasattr(item, 'text'):
                            content_parts.append(item.text)
                        else:
                            content_parts.append(str(item))
                    return "\n".join(content_parts)
            else:
                return str(result.content)
        except Exception as e:
            return f"Error invoking tool {original_tool_name} on server {server_name}: {e}"

    async def list_all_tools(self) -> None:
        print("Preparing tools for Gemini function calling...")
        print(len(self.all_tools), "tools found.")
        for tool in self.all_tools:
            function_declaration = genai.protos.FunctionDeclaration(
                name=tool['name'],
                description=tool['description'],
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        prop_name: self._convert_json_type_to_genai(prop_schema)
                        for prop_name, prop_schema in tool['input_schema'].get('properties', {}).items()
                    },
                    required=tool['input_schema'].get('required', [])
                )
            )
            self.gemini_tools.append(function_declaration)

        print(len(self.gemini_tools), "tools prepared for Gemini function calling.")
        print(self.get_tools_summary())

    async def get_server_status(self) -> str:
        if not self.sessions:
            return "No active sessions."

        status_reports = [f"Connected servers ({len(self.sessions)}):"]
        for server_name, session in self.sessions.items():
            try:
                status = await session.list_tools()
                tool_count = len(status.tools)
                status_reports.append(f"- {server_name}: {tool_count} tools available.")
            except Exception as e:
                status_reports.append(f"- {server_name}: Error retrieving status - {e}")

        return "\n".join(status_reports)

    async def reconnect_server(self, server_name: str) -> None:
        config = await self.load_config()
        servers = config.get("servers", {})
        server_info = servers.get(server_name)

        if not server_info:
            print(f"Server {server_name} not found in configuration.")
            return

        try:
            await self.connect_to_server(server_name, server_info)
            print(f"Reconnected to {server_name} successfully.")
            await self.aggregate_tools()
        except Exception as e:
            print(f"Failed to reconnect to {server_name}: {e}")

    async def cleanup(self) -> None:
        try:
            # close sessions first
            for server_name in list(self.sessions.keys()):
                try:
                    session = self.sessions.pop(server_name)
                    if hasattr(session, 'close'):
                        await session.close()
                except Exception as e:
                    print(f"Error closing session for {server_name}: {e}")
            await self.exit_stack.aclose()
        except Exception as e:
            print(f"Error during cleanup: {e}")