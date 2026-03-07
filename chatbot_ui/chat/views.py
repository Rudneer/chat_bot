from django.shortcuts import render
from django.http import JsonResponse
import requests
import json


def home(request):
    return render(request, "chat/chat.html")


def chat(request):
    if request.method == "POST":
        body = json.loads(request.body)
        user_message = body.get("message")

        response = requests.post(
            "http://127.0.0.1:8000/chat",
            json={
                "user_id": "user123",
                "question": user_message
            }
        )

        print("FASTAPI RAW RESPONSE:", response.text)
        print("FASTAPI JSON:", response.json())

        bot_reply = response.json().get("response")

        print("BOT REPLY:", bot_reply)

        return JsonResponse({"response": bot_reply})




