import os, math, json
from django.core.management.base import BaseCommand
from django.conf import settings
from openai import OpenAI
from chatbot.models import dataChunks as KBChunk
from PyPDF2 import PdfReader

CHUNK_SIZE = 900     
CHUNK_OVERLAP = 150

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    text = " ".join(text.split())  # normalize spaces
    i = 0
    while i < len(text):
        yield text[i:i+size]
        i += size - overlap

class Command(BaseCommand):
    help = "Embed files in chatbot/resources into KBChunk"

    def handle(self, *args, **kwargs):
        client = OpenAI()
        resources_dir = os.path.join(settings.BASE_DIR, "chatbot", "resources")
        files = [os.path.join(resources_dir, f) for f in os.listdir(resources_dir) if not f.startswith(".")]

        total_chunks = 0
        for path in files:
            ext = os.path.splitext(path)[1].lower()
            if ext in [".txt", ".md"]:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            elif ext == ".pdf":
                reader = PdfReader(path)
                content = "\n".join([p.extract_text() or "" for p in reader.pages])
            else:
                self.stdout.write(self.style.WARNING(f"Skip {path}"))
                continue

            for piece in chunk_text(content):
                emb = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=piece
                ).data[0].embedding

                KBChunk.objects.create(
                    source=os.path.basename(path),
                    text=piece,
                    embedding=emb
                )
                total_chunks += 1

        self.stdout.write(self.style.SUCCESS(f"Indexed {total_chunks} chunks"))
