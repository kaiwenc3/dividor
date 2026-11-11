"""Run with: python -m streamlit run app.py"""
import os
import streamlit as st
from chat_graph import (branch, build_graph, context_for, demo_response,
                        live_responder, message, new_conversation)

st.set_page_config(page_title="Dividor", page_icon="🌿", layout="wide")
if "conversations" not in st.session_state:
    root = new_conversation("Main conversation")
    st.session_state.conversations = {root["id"]: root}
    st.session_state.active = root["id"]
    st.session_state.source_focus = None
    st.session_state.pending_branch = None

conversations = st.session_state.conversations


def navigate(conversation_id, source=None):
    st.session_state.active = conversation_id
    st.session_state.source_focus = source
    st.session_state.pending_branch = None
    st.rerun()


def render_tree(parent=None, depth=0):
    for cid, item in conversations.items():
        if item["parent"] == parent:
            label = ("　" * depth) + ("↳ " if depth else "") + item["title"]
            if st.button(label, key=f"nav_{cid}", use_container_width=True,
                         type="primary" if cid == st.session_state.active else "secondary"):
                navigate(cid)
            render_tree(cid, depth + 1)


with st.sidebar:
    st.title("🌿 Dividor")
    st.caption("Keep your questions connected.")
    if st.button("＋ New conversation", use_container_width=True):
        root = new_conversation()
        conversations[root["id"]] = root
        navigate(root["id"])
    st.subheader("Conversation tree")
    render_tree()
    st.divider()
    demo = st.toggle("Demo mode", value=True,
                     help="Explore branching without an API key. Replies are placeholders.")
    api_key = st.text_input("OpenAI API key", type="password",
                            value=os.getenv("OPENAI_API_KEY", ""))
    model = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    st.caption("Conversations last for this browser session. Refreshing may clear them.")

current = conversations[st.session_state.active]
st.title(current["title"])
st.caption("Branch from a message to explore a side question without losing your place.")
if demo:
    st.info("Demo mode is on. Turn it off and enter an API key for real AI responses.")

if current["parent"]:
    parent = conversations[current["parent"]]
    if st.button(f"← Back to source · {parent['title']}"):
        navigate(parent["id"], current["source"])
    inherited = context_for(conversations, current["id"])
    inherited_count = len(inherited) - len(current["messages"])
    with st.expander(f"Inherited context · {inherited_count} messages"):
        for item in inherited[:inherited_count]:
            with st.chat_message(item["role"]):
                st.markdown(item["content"])

focus = st.session_state.source_focus
if focus:
    source = next((m for m in current["messages"] if m["id"] == focus), None)
    if source:
        with st.container(border=True):
            st.markdown("**↩ Original source message**")
            st.caption("Shown here so you do not need to scroll through the conversation.")
            with st.chat_message(source["role"]):
                st.markdown(source["content"])
            if st.button("Dismiss source preview"):
                st.session_state.source_focus = None
                st.rerun()

if not current["messages"]:
    st.markdown("**Start with a question below.** You can branch from any message.")

for item in current["messages"]:
    with st.chat_message(item["role"]):
        if item["id"] == focus:
            st.caption("↩ Source of the branch you just left")
        st.markdown(item["content"])
        if st.button("⑂ Branch", key=f"branch_{item['id']}"):
            st.session_state.pending_branch = item["id"]
            st.rerun()
        children = [c for c in conversations.values()
                    if c["parent"] == current["id"] and c["source"] == item["id"]]
        for child in children:
            if st.button(f"↳ {child['title']}", key=f"child_{child['id']}"):
                navigate(child["id"])

if st.session_state.pending_branch:
    with st.form("create_branch"):
        st.markdown("**Create a related conversation**")
        title = st.text_input("Branch title", placeholder="e.g. Explain the database design")
        create = st.form_submit_button("Create branch")
        cancel = st.form_submit_button("Cancel")
        if create:
            if title.strip():
                cid = branch(conversations, current["id"],
                             st.session_state.pending_branch, title.strip())
                navigate(cid)
            else:
                st.warning("Enter a short title for the branch.")
        if cancel:
            st.session_state.pending_branch = None
            st.rerun()

prompt = st.chat_input("Ask a question…", disabled=bool(st.session_state.pending_branch))
if prompt and prompt.strip():
    if not demo and (not api_key.strip() or not model.strip()):
        st.error("Enter an API key and model in the sidebar, or enable Demo mode.")
        st.stop()
    try:
        with st.spinner("Thinking…"):
            responder = demo_response if demo else live_responder(api_key.strip(), model.strip())
            result = build_graph(responder).invoke({"conversations": conversations,
                      "conversation_id": current["id"], "prompt": prompt})
        # Commit both messages only after success, so failed requests can be retried.
        current["messages"].extend([message("user", prompt),
                                    message("assistant", result["answer"])])
        if current["title"] in ("Main conversation", "New conversation"):
            current["title"] = prompt[:45] + ("…" if len(prompt) > 45 else "")
        st.session_state.source_focus = None
        st.rerun()
    except Exception:
        st.error("The response failed. Check your API key, model, connection, and account quota. "
                 "Your existing conversation is unchanged; resubmit your question to retry.")
        st.code(prompt, language=None)
