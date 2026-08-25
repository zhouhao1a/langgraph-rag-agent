from operator import add
from typing_extensions import TypedDict, Annotated


class AgentState(TypedDict):
    messages: Annotated[list[str], add]
    retrieved_docs: list[str]
    user_query: str
    final_answer: str

class InputState(TypedDict):
    user_query: str


class OutputState(TypedDict):
    final_answer: str
