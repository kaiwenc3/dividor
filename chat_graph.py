"""Conversation storage and the LangGraph response pipeline."""
from typing import TypedDict
from uuid import uuid4


def message(role, content):
    return {"id": uuid4().hex, "role": role, "content": content}


def new_conversation(title="New conversation", parent=None, source=None):
    return {"id": uuid4().hex, "title": title, "parent": parent,
            "source": source, "messages": []}


def context_for(conversations, conversation_id):
    """Reconstruct ancestors only through each branch's source message."""
    conversation = conversations[conversation_id]
    context = []
    if conversation["parent"]:
        parent_context = context_for(conversations, conversation["parent"])
        index = next(i for i, m in enumerate(parent_context)
                     if m["id"] == conversation["source"])
        context = parent_context[:index + 1]
    return context + conversation["messages"]


def branch(conversations, parent_id, source_id, title):
    if not any(m["id"] == source_id for m in conversations[parent_id]["messages"]):
        raise ValueError("Choose a message in the parent conversation.")
    child = new_conversation(title, parent_id, source_id)
    conversations[child["id"]] = child
    return child["id"]


class ChatState(TypedDict):
    conversations: dict
    conversation_id: str
    prompt: str
    context: list
    answer: str


def build_graph(responder):
    from langgraph.graph import END, START, StateGraph

    def assemble_context(state):
        history = context_for(state["conversations"], state["conversation_id"])
        return {"context": [{"role": m["role"], "content": m["content"]}
                            for m in history] +
                           [{"role": "user", "content": state["prompt"]}]}

    def generate_response(state):
        return {"answer": responder(state["context"])}

    graph = StateGraph(ChatState)
    graph.add_node("assemble_context", assemble_context)
    graph.add_node("generate_response", generate_response)
    graph.add_edge(START, "assemble_context")
    graph.add_edge("assemble_context", "generate_response")
    graph.add_edge("generate_response", END)
    return graph.compile()


def demo_response(context):
    return ("**Demo response — no AI request was sent.**\n\n"
            f"Your question: {context[-1]['content']}\n\n"
            f"This branch has {len(context) - 1} earlier messages in its context. "
            "Create a branch from this message to explore a separate question.")


def live_responder(api_key, model):
    from langchain_openai import ChatOpenAI
    client = ChatOpenAI(api_key=api_key, model=model, timeout=45, max_retries=1)

    def respond(context):
        result = client.invoke([
            {"role": "system", "content": "You are a helpful technical tutor. "
             "Answer the current question using the provided conversation context. "
             "Use clear explanations and concise examples."}, *context])
        if not isinstance(result.content, str) or not result.content.strip():
            raise ValueError("The model returned no text. Try another model.")
        return result.content
    return respond
