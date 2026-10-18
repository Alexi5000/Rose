import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph


@pytest.mark.asyncio
async def test_sqlite_checkpoints_survive_reopening(tmp_path):
    builder = StateGraph(MessagesState)
    builder.add_node("reply", lambda state: {"messages": [AIMessage(content="Saved reply")]})
    builder.add_edge(START, "reply")
    builder.add_edge("reply", END)
    path = str(tmp_path / "memory.db")
    config = {"configurable": {"thread_id": "isolated-session"}}
    async with AsyncSqliteSaver.from_conn_string(path) as saver:
        graph = builder.compile(checkpointer=saver)
        await graph.ainvoke({"messages": [HumanMessage(content="Remember this")]}, config)
    async with AsyncSqliteSaver.from_conn_string(path) as saver:
        graph = builder.compile(checkpointer=saver)
        state = await graph.aget_state(config)
        assert [message.content for message in state.values["messages"]] == ["Remember this", "Saved reply"]
        other = await graph.aget_state({"configurable": {"thread_id": "other-session"}})
        assert not other.values
