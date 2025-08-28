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
        user_msg = json.loads(request.body).get("message", "").strip()
        if not user_msg:
            return JsonResponse({"reply": "Please ask a valid question."})

        # Build context from RAG
        context = build_context(user_msg, k=5)

        system_prompt = (
            "You are RAG-GPT, a strict assistant.\n"
            "RULES:\n"
            "1. Answer ONLY using the provided context.\n"
            "2. If the answer is not found, reply exactly: "
            "'Oops! Not my fault, Rohan kept this secret.'\n"
            "3. Elitte College Of Engineering and  elitte . elite , ece all same name \n"
            "4. Be concise and accurate.\n"
        )

        user_prompt = f"Context:\n{context}\n\nQuestion: {user_msg}"

        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "rag_answer",
                        "schema": {
                            "type": "object",
                            "properties": {"answer": {"type": "string"}},
                            "required": ["answer"],
                        },
                    },
                },
            )

            reply_json = completion.choices[0].message.content
            reply = json.loads(reply_json)["answer"]

        except Exception as e:
            reply = f"Error: {str(e)}"

        return JsonResponse({"reply": reply})

    return JsonResponse({"error": "POST only"}, status=405)