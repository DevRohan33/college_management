from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .openai_client import client
from .rag import build_context


def chat_page(request):
    return render(request, "includes/chatbot.html")


@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        user_msg = json.loads(request.body).get("message","")
        context = build_context(user_msg, k=5)

        system = (
            "You are a helpful assistant. "
            "Answer using ONLY the provided context. "
            "If the answer isn't in context, say Oops! Not my fault, Rohan kept this secret."
        )
        user = f"Context:\n{context}\n\nQuestion: {user_msg}"

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content": system},
                {"role":"user","content": user}
            ],
            temperature=0.1,
        )
        reply = completion.choices[0].message.content
        return JsonResponse({"reply": reply})
    return JsonResponse({"error":"POST only"}, status=405)
