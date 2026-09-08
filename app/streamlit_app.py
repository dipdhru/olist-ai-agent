import streamlit as st
import pandas as pd
import plotly.express as px
from src.agent.orchestrator import AIAnalystAgent

st.set_page_config(page_title="AI Database Analyst", layout="wide")

st.title("📊 AI Database Analyst Agent")
st.markdown("Ask questions about your SQL database in natural language.")

# Configuration in sidebar
with st.sidebar:
    st.header("Settings")
    db_url = st.text_input("Database URL", value="sqlite:///data/olist.db")
    semantic_schema_path = st.text_input("Semantic Schema Path", value="data/semantic_schema.json")
    if st.button("Reset Conversation"):
        st.session_state.agent = None

# Initialize agent in session state
if "agent" not in st.session_state or st.session_state.agent is None:
    try:
        st.session_state.agent = AIAnalystAgent(db_url, semantic_schema_path)
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sql" in message:
            with st.expander("View SQL"):
                st.code(message["sql"], language="sql")
        if "data" in message:
            with st.expander("View Raw Data"):
                st.dataframe(pd.DataFrame(message["data"]))
        if "chart" in message:
            spec = message["chart"]
            if spec and spec.get("type") == "bar":
                fig = px.bar(x=spec["x"], y=spec["y"], title=spec["title"]) # simplified
                st.plotly_chart(fig)
            elif spec and spec.get("type") == "line":
                fig = px.line(x=spec["x"], y=spec["y"], title=spec["title"])
                st.plotly_chart(fig)

# User input
if prompt := st.chat_input("How many products did we sell?"):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing data..."):
            try:
                result = st.session_state.agent.ask(prompt)

                if "error" in result:
                    answer = f"❌ Error: {result['error']}"
                    sql = None
                else:
                    answer = result["answer"]
                    sql = result["sql"]
                    data = result["data"]
                    chart = result["chart"]

                st.markdown(answer)

                if sql:
                    with st.expander("View SQL"):
                        st.code(sql, language="sql")

                if "data" in result:
                    with st.expander("View Raw Data"):
                        st.dataframe(pd.DataFrame(result["data"]))

                if "chart" in result and result["chart"]:
                    spec = result["chart"]
                    # In a real app, we'd use the result data and the spec to build the chart
                    # Here we'll just notify the user that a chart spec was generated
                    st.info(f"Chart suggestion: {spec['type']} chart - {spec['title']}")

                # Add assistant message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sql": sql,
                    "data": result.get("data"),
                    "chart": result.get("chart")
                })
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
