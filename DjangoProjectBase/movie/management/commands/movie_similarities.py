import os
import numpy as np
from django.core.management.base import BaseCommand
from movie.models import Movie
from openai import OpenAI
from dotenv import load_dotenv


class Command(BaseCommand):
    help = "Compare two movies and optionally a prompt using OpenAI embeddings"

    def add_arguments(self, parser):
        parser.add_argument('--movie1', type=str, required=True, help='Title of the first movie')
        parser.add_argument('--movie2', type=str, required=True, help='Title of the second movie')
        parser.add_argument('--prompt', type=str, required=False, help='Optional prompt to compare')

    def handle(self, *args, **kwargs):
        # Load OpenAI API key
        load_dotenv('../openAI.env')
        client = OpenAI(api_key=os.environ.get('openai_apikey'))

        movie1_title = kwargs['movie1']
        movie2_title = kwargs['movie2']
        prompt = kwargs.get('prompt')

        try:
            movie1 = Movie.objects.get(title=movie1_title)
        except Movie.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Movie not found: {movie1_title}"))
            return

        try:
            movie2 = Movie.objects.get(title=movie2_title)
        except Movie.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Movie not found: {movie2_title}"))
            return

        def get_embedding(text):
            response = client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return np.array(response.data[0].embedding, dtype=np.float32)

        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        emb1 = get_embedding(movie1.description)
        emb2 = get_embedding(movie2.description)

        similarity = cosine_similarity(emb1, emb2)
        self.stdout.write(
            f"🎬 Similaridad entre '{movie1.title}' y '{movie2.title}': {similarity:.4f}"
        )

        if prompt:
            prompt_emb = get_embedding(prompt)
            sim_prompt_movie1 = cosine_similarity(prompt_emb, emb1)
            sim_prompt_movie2 = cosine_similarity(prompt_emb, emb2)

            self.stdout.write(
                f"📝 Similitud prompt vs '{movie1.title}': {sim_prompt_movie1:.4f}"
            )
            self.stdout.write(
                f"📝 Similitud prompt vs '{movie2.title}': {sim_prompt_movie2:.4f}"
            )