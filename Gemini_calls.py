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
