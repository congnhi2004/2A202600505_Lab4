from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from tools import search_flights, search_hotels, calculate_budget
from dotenv import load_dotenv

load_dotenv()

# ===== 1. Load system prompt =====
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# ===== 2. State =====
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# ===== 3. Tools =====
tools_list = [search_flights, search_hotels, calculate_budget]

# ===== 4. LLM =====
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2  # quan trọng
)

llm_with_tools = llm.bind_tools(tools_list)

# ===== 5. Agent Node =====
def agent_node(state: AgentState):
    messages = state.get("messages", [])

    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)

    # ===== Logging =====
    if getattr(response, "tool_calls", None):
        for tc in response.tool_calls:
            print(f"[TOOL CALL] {tc['name']} → {tc['args']}")
    else:
        print("[LLM RESPONSE] trả lời trực tiếp")

    return {"messages": [response]}

# ===== 6. Graph =====
builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools_list))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

graph = builder.compile()

# ===== 7. CLI =====
if __name__ == "__main__":
    print("=" * 60)
    print("TravelBuddy - Trợ lý Du lịch Thông minh")
    print("Gõ 'quit' để thoát")
    print("=" * 60)

    while True:
        user_input = input("\nBạn: ").strip()

        if user_input.lower() in ("quit", "exit", "q"):
            break

        print("\nTravelBuddy đang suy nghĩ...")

        result = graph.invoke({
            "messages": [("human", user_input)]
        })

        final = result["messages"][-1]
        print(f"\nTravelBuddy: {final.content}")