import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
import os

# from langchain.agents import AgentType # Removed to avoid ImportError

def get_chatbot_agent():
    """
    Creates and returns a LangChain SQL Agent powered by Groq (Llama 3).
    """
    # 1. Setup API Key
    if "groq" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["groq"]["api_key"]
    else:
        st.error("Groq secrets missing.")
        return None

    # 2. Setup Database Connection URL
    db_url = st.secrets["supabase"].get("db_url")
    if not db_url:
        st.warning("To use the Chatbot, please add `db_url` to `.streamlit/secrets.toml` under `[supabase]` section.")
        return None

    try:
        db = SQLDatabase.from_uri(db_url)
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

    # 3. Setup LLM (Using Groq - Llama 3 70b is good for SQL)
    try:
        llm = ChatGroq(
            model_name="llama-3.3-70b-versatile", 
            temperature=0
        )
    except Exception as e:
        st.error(f"Failed to init Groq: {e}")
        return None

    # 4. Create Agent
    agent = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="zero-shot-react-description",
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent
