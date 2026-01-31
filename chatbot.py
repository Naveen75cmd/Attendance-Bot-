import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents import AgentType
import os

def get_chatbot_agent():
    """
    Creates and returns a LangChain SQL Agent powered by Gemini.
    """
    # 1. Setup API Key
    if "google" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["google"]["api_key"]
    
    if "supabase" not in st.secrets:
        st.error("Supabase secrets missing.")
        return None

    # 2. Setup Database Connection URL
    # Supabase uses Postgres. Connect via sqlalchemy.
    # We need the connection string. Supabase provides a connection string in dashboard.
    # Usually: postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
    # The 'url' in secrets is usually the API URL (HTTPS). We need the DB Connection string for SQLDatabase.
    
    # ASK USER: We need the DB_CONNECTION_STRING in secrets for this to work natively with SQLDatabase.
    # OR we can write custom tools that use the Supabase Python Client (API) instead of direct SQL connection.
    # Python Client is safer and easier with the provided credentials (URL + KEY).
    # Writing custom tools is better here to avoid needing the direct DB password/connection string explicitly if we only have API Key.
    
    # HOWEVER, the User Request mentioned "Text-to-SQL". 
    # Standard Text-to-SQL requires a SQLDatabase connection.
    # The user instructions said instructions for `requirements.txt` and `secrets.toml` specifically.
    # I will assume for now we use Custom Tools wrapping the `utils` functions or Supabase Client, 
    # OR I can ask the user for the postgres connection string. 
    # Let's try to capture the requirement "Text-to-SQL" literally if possible. 
    # But usually Supabase API key is for REST. 
    # I will add a 'db_url' field to secrets and use SQLDatabase for true Text-to-SQL.
    
    db_url = st.secrets["supabase"].get("db_url")
    if not db_url:
        st.warning("To use the Text-to-SQL Chatbot, please add `db_url` to `.streamlit/secrets.toml` under `[supabase]` section.\nFormat: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres` (Transaction mode recommended)")
        return None

    db = SQLDatabase.from_uri(db_url)

    # 3. Setup LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)

    # 4. Create Agent
    agent = create_sql_agent(
        llm=llm,
        db=db,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent
