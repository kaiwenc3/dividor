# Dividor

A Homework 6 application using Streamlit and LangGraph. Branch from any message,
explore a side question, and return to its source without searching a long chat.

## Run on Windows

```powershell
git clone https://github.com/kaiwenc3/dividor.git
cd dividor
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The app starts in **Demo mode**, which uses clearly labeled placeholder replies
and makes no API requests. Turn Demo mode off and enter your OpenAI API key and
an available model in the sidebar for real AI responses. API usage is billed
through your API account. OPENAI_API_KEY and OPENAI_MODEL environment variables
can also supply defaults. Keys are not written to disk by the app.

## Try the workflow

1. Send a question in the main conversation.
2. Click Branch beneath a message and enter a title.
3. Ask a follow-up in the new branch.
4. Use Back to source to open the parent with the source message previewed at the top.
5. Switch among conversations in the sidebar. Branches can have their own branches.

## Implementation

- `app.py`: Streamlit interface and session storage.
- `chat_graph.py`: conversation helpers and LangGraph pipeline:
  START -> assemble_context -> generate_response -> END.
- `test_branches.py`: checks context boundaries, nested branches, and isolation.

Each conversation holds its own messages plus parent and source-message IDs.
Context is reconstructed through each ancestor up to its source message; later
parent messages and sibling messages are excluded. The visible conversation tree
is separate from LangGraph's execution graph. A turn is saved only after a
successful response.

Conversations live in browser-session memory; refresh or server restart may clear
them. This first version uses Branch buttons and a clickable sidebar tree.
Right-click menus, a node-link graph, persistent storage, and context summarization
are future additions. Long branches can eventually exceed the model context limit.

## Check

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_branches.py
```

Documentation: [Streamlit chat elements](https://docs.streamlit.io/develop/api-reference/chat)
and [LangGraph graph API](https://reference.langchain.com/python/langgraph/graph).

