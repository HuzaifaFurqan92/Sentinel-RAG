from typing_extensions import TypedDict
from langchain.chat_models import init_chat_model
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph,START,END
from typing import Annotated,Literal

llm = init_chat_model()



