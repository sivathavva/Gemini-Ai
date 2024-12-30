# Main App
st.title("Gemini AI SQL Generator")

def set_question(question):
    st.session_state["my_question"] = question

assistant_message_suggested = st.chat_message("assistant", avatar=avatar_url)
if assistant_message_suggested.button("Click to show suggested questions"):
    st.session_state["my_question"] = None
    questions = ["What are the top products?", "How many sales were made last year?", "Which employees are the highest earners?"]  # Sample questions
    for i, question in enumerate(questions):
        time.sleep(0.05)
        st.button(question, on_click=set_question, args=(question,))

my_question = st.session_state.get("my_question", default=None)
if my_question is None:
    my_question = st.chat_input("Ask me a question about your data")

if my_question:
    st.session_state["my_question"] = my_question
    user_message = st.chat_message("user")
    user_message.write(f"{my_question}")

    try:
        sql = generate_sql_from_gemini(my_question)
        if sql:
            if validate_sql(sql=sql):
                if st.session_state.get("show_sql", True):
                    assistant_message_sql = st.chat_message("assistant", avatar=avatar_url)
                    assistant_message_sql.code(sql, language="sql", line_numbers=True)
            else:
                st.chat_message("assistant", avatar=avatar_url).error("Generated SQL is invalid.")
                st.stop()

            df = execute_sql(sql=sql)
            if df is not None:
                st.session_state["df"] = df

            if st.session_state.get("df") is not None:
                df = st.session_state["df"]
                if st.session_state.get("show_table", True):
                    st.chat_message("assistant", avatar=avatar_url).dataframe(df.head(10) if len(df) > 10 else df)

                if st.session_state.get("show_summary", True):
                    summary = generate_summary(my_question, df)
                    if summary:
                        st.chat_message("assistant", avatar=avatar_url).text(summary)

                if st.session_state.get("show_followup", True):
                    followups = generate_followup_questions(my_question, sql, df)
                    if followups:
                        for followup in followups[:5]:
                            st.button(followup, on_click=set_question, args=(followup,))

                if st.session_state.get("show_plotly", False):
                    try:
                        fig = px.histogram(df, x=df.columns[0], y=df.columns[1], title="Sample Plotly Chart")
                        st.plotly_chart(fig)
                    except Exception as e:
                        st.chat_message("assistant", avatar=avatar_url).error(f"Error generating plot: {e}")

        else:
            st.chat_message("assistant", avatar=avatar_url).error("Failed to generate SQL.")
    except Exception as e:
        st.chat_message("assistant", avatar=avatar_url).error(f"Error: {e}")

# gemini_calls.py
import sqlite3
import pandas as pd
import requests
import streamlit as st

# Retrieve Gemini API key from Streamlit secrets file
GEMINI_API_KEY = st.secrets["gemini"]["api_key"]
GEMINI_API_URL = "https://api.gemini.com/v1/flash"  # Adjust the endpoint if needed

# SQLite Database Path (Local)
DB_PATH = '/home/ubuntu/gemini-streamlit/Chinook.sqlite'  # Path to your SQLite3 local database

# Function to generate SQL from Gemini using the user's question
def generate_sql_from_gemini(question):
    payload = {
        "model": "gemini-1.5-flash",  # Replace with the appropriate model
        "prompt": f"Translate the following question into an SQL query: {question}",
        "max_tokens": 150
    }

    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(GEMINI_API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()['choices'][0]['text'].strip()
    else:
        raise Exception(f"Error generating SQL: {response.status_code}, {response.text}")

# Function to validate SQL by executing it on SQLite3
def validate_sql(sql):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)  # Test if SQL is valid
        conn.close()
        return True
    except Exception as e:
        return False

# Function to execute the SQL query on SQLite3 and return the result as a DataFrame
def execute_sql(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Function to generate a summary using Gemini
def generate_summary(question, df):
    prompt = f"Provide a summary of the following data based on the question: {question}\nData: {df.head(5)}"
    payload = {
        "model": "gemini-1.5-flash",  # Replace with the appropriate model
        "prompt": prompt,
        "max_tokens": 200
    }

    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(GEMINI_API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()['choices'][0]['text'].strip()
    else:
        raise Exception(f"Error generating summary: {response.status_code}, {response.text}")

# Function to generate follow-up questions using Gemini
def generate_followup_questions(question, sql, df):
    prompt = f"Suggest follow-up questions based on the question: {question}, SQL: {sql}, and data: {df.head(5)}"
    payload = {
        "model": "gemini-1.5-flash",  # Replace with the appropriate model
        "prompt": prompt,
        "max_tokens": 200
    }

    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        followups = response.json()['choices'][0]['text'].strip().split('\n')
        return followups
    else:
        raise Exception(f"Error generating follow-up questions: {response.status_code}, {response.text}")
