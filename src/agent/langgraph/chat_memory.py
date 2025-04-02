import os
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(api_key=os.environ.get("QWEN_APIKEY"),
                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                 model="qwen-turbo")


def chatbot(state: State):
    print(state,state["messages"])
    return {"messages": [llm.invoke(state["messages"])]}


graph_builder.add_node("chatbot", chatbot)

graph_builder.set_entry_point("chatbot")
graph_builder.set_finish_point("chatbot")
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "1"}}
user_input = "Hi there! My name is Will."



# 1.
# The config is the **second positional argument** to stream() or invoke()!
events = graph.stream(
    {"messages": [{"role": "user", "content": user_input}]},
    config,
    stream_mode="values",
)
for event in events:
    event["messages"][-1].pretty_print()

snapshot = graph.get_state(config)
print(snapshot)

# 2.
user_input = "Remember my name?"

# The config is the **second positional argument** to stream() or invoke()!
events = graph.stream(
    {"messages": [{"role": "user", "content": user_input}]},
    config,
    stream_mode="values",
)
for event in events:
    event["messages"][-1].pretty_print()

snapshot = graph.get_state(config)
print(snapshot)

"""
历史消息
{'messages': [HumanMessage(content='Hi there! My name is Will.', additional_kwargs={}, response_metadata={},
                           id='eb92a2fe-ec48-49a1-a50b-fdadb1cead9b'),
              AIMessage(content='Hello Will! Nice to meet you. How can I assist you today?',
                        additional_kwargs={'refusal': None}, response_metadata={
                      'token_usage': {'completion_tokens': 15, 'prompt_tokens': 16, 'total_tokens': 31,
                                      'completion_tokens_details': None,
                                      'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 0}},
                      'model_name': 'qwen-turbo', 'system_fingerprint': None,
                      'id': 'chatcmpl-4a545378-f8be-9028-bb73-812e7c3a1999', 'finish_reason': 'stop', 'logprobs': None},
                        id='run-835f795e-a9df-4bab-a84e-25f193de12a2-0',
                        usage_metadata={'input_tokens': 16, 'output_tokens': 15, 'total_tokens': 31,
                                        'input_token_details': {'cache_read': 0}, 'output_token_details': {}}),
              HumanMessage(content='Remember my name?', additional_kwargs={}, response_metadata={},
                           id='81b80fe0-12d3-43e0-90bd-9b8cf46b9782')]}
"""