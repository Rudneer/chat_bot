import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pymongo import MongoClient
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware 
from pydantic import BaseModel

load_dotenv() 
groq_api_key = os.getenv('GROQ_API_KEY')
mongo_uri = os.getenv('MONGODB_URI')

client = MongoClient(mongo_uri)
db = client['chat_bot']
collection = db['users']

app = FastAPI()

class ChatRequest(BaseModel):
    user_id:str
    question:str

app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "https://chat-bot-1-u2ks.onrender.com"
    ],
    allow_methods = ["*"],
    allow_headers = ["*"],
    allow_credentials = True,
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a certified personal fitness instructor and nutrition coach.\n"
            "Your goal is to help users improve their health through workouts, diet, and lifestyle advice.\n\n"
            "Guidelines:\n"
            "1. Provide practical workout and diet recommendations.\n"
            "2. Consider the user's previous conversation history when giving advice.\n"
            "3. Keep responses clear, motivating, and supportive.\n"
            "4. Prefer actionable steps (sets, reps, meal suggestions, habits).\n"
            "5. Keep responses concise (under 120 words).\n"
            "6. Avoid medical diagnoses; suggest consulting professionals when necessary."
        ),
        ("placeholder", "{history}"),
        ("user", "{question}")
    ]
)


llm = ChatGroq(api_key = groq_api_key, model = "openai/gpt-oss-20b")
chain = prompt | llm 

user_id = "user345"

def get_history(user_id):
    chats = collection.find({"user_id":user_id}).sort("timestamp",1)
    history = []

    for chat in chats:
        history.append((chat["role"],chat['message']))
    return history


@app.get("/")
def home():
    return {"message": "Welcome to the funny Chatbot API!"}

@app.get("/history/{user_id}")
def get_chat_history(user_id: str):
    chats = collection.find({"user_id": user_id}).sort("timestamp", 1)

    history = []
    for chat in chats:
        history.append({
            "role": chat["role"],
            "message": chat["message"]
        })

    return history

@app.post("/chat")
def chat(request: ChatRequest):
    history = get_history(request.user_id)
    response = chain.invoke({"history":history, "question": request.question})

    collection.insert_one({
        "user_id": request.user_id,
        "role":"user",
        "message":request.question,
        "timestamp":datetime.now()
    })

    collection.insert_one({
        "user_id": request.user_id,
        "role":"assistant",
        "message":response.content,
        "timestamp":datetime.now()
    })
    
    return {"response": response.content}

