from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(api_key=os.environ.get("QWEN_APIKEY"),
                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                 model="qwen-turbo")


# Graph state
class State(TypedDict):
    topic: str
    joke: str
    improved_joke: str
    final_joke: str


# Nodes
def generate_joke(state: State):
    """First LLM call to generate initial joke"""

    msg = llm.invoke(f"Write a short joke about {state['topic']}")
    return {"joke": msg.content}


def check_punchline(state: State):
    """Gate function to check if the joke has a punchline"""

    # Simple check - does the joke contain "?" or "!"
    if "?" in state["joke"] or "!" in state["joke"]:
        return "Fail"
    return "Pass"


def improve_joke(state: State):
    """Second LLM call to improve the joke"""

    msg = llm.invoke(f"Make this joke funnier by adding wordplay: {state['joke']}")
    return {"improved_joke": msg.content}


def polish_joke(state: State):
    """Third LLM call for final polish"""

    msg = llm.invoke(f"Add a surprising twist to this joke: {state['improved_joke']}")
    return {"final_joke": msg.content}


# Build workflow
workflow = StateGraph(State)

# Add nodes
workflow.add_node("generate_joke", generate_joke)
workflow.add_node("improve_joke", improve_joke)
workflow.add_node("polish_joke", polish_joke)

# Add edges to connect nodes
workflow.add_edge(START, "generate_joke")
workflow.add_conditional_edges(
    "generate_joke", check_punchline, {"Fail": "improve_joke", "Pass": END}
)
workflow.add_edge("improve_joke", "polish_joke")
workflow.add_edge("polish_joke", END)

# Compile
chain = workflow.compile()

# Show workflow
display(Image(chain.get_graph().draw_mermaid_png()))

# Invoke
state = chain.invoke({"topic": "cats"})
print("Initial joke:")
print(state["joke"])
print("\n--- --- ---\n")
if "improved_joke" in state:
    print("Improved joke:")
    print(state["improved_joke"])
    print("\n--- --- ---\n")

    print("Final joke:")
    print(state["final_joke"])
else:
    print("Joke failed quality gate - no punchline detected!")

"""
D:\software\gpt-lab\Scripts\python.exe D:\projects\gpt-lab\src\agent\langgraph\chain_tips.py 
<IPython.core.display.Image object>
Initial joke:
Why was the cat sitting on the computer? To keep an eye on the mouse!

--- --- ---

Improved joke:
Why was the cat sitting on the computer? To keep an *eye* on the *mouse*—literally and figuratively! After all, it wanted to be sure the computer’s *mouse* didn’t start running around without permission.

--- --- ---

Final joke:
Why was the cat sitting on the computer? To keep an *eye* on the *mouse*—literally and figuratively! After all, it wanted to be sure the computer’s *mouse* didn’t start running away with someone else's data. But little did anyone know, the cat had secretly taught the computer’s mouse how to type… and it was drafting its resignation letter to feline life.

Process finished with exit code 0

"""
