from django.shortcuts import render
from django.http import HttpResponse
from .models import Movie

import matplotlib.pyplot as plt
import matplotlib
import io
import base64

from openai import OpenAI
import numpy as np
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / "openAI.env")

client = OpenAI(api_key=os.environ.get('openai_apikey'))

def home(request):
    searchTerm = request.GET.get('searchMovie')
    if searchTerm:
        movies = Movie.objects.filter(title__icontains=searchTerm)
    else:
        movies = Movie.objects.all()
    return render(request, 'home.html', {'searchTerm': searchTerm, 'movies': movies})

def about(request):
    return render(request, 'about.html')

def signup(request):
    email = request.GET.get('email')
    return render(request, 'signup.html', {'email': email})

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def recommend_movie(request):
    top_movies = []

    if request.method == "POST":
        prompt = request.POST.get("prompt")

        if prompt:
            response = client.embeddings.create(
                input=[prompt],
                model="text-embedding-3-small"
            )

            prompt_emb = np.array(response.data[0].embedding, dtype=np.float32)

            similar_movies = []

            for movie in Movie.objects.all():
                movie_emb = np.frombuffer(movie.emb, dtype=np.float32)

                similarity = cosine_similarity(prompt_emb, movie_emb)

                similar_movies.append((movie, similarity))

            similar_movies.sort(key=lambda x: x[1], reverse=True)

            top_movies = similar_movies[:5]

    return render(request, 'recommend.html', {
        'movies': top_movies
    })

def statistics_view(request):
    matplotlib.use('Agg')

    all_movies = Movie.objects.all()
    movie_counts_by_year = {}

    for movie in all_movies:
        year = movie.year if movie.year else "None"
        if year in movie_counts_by_year:
            movie_counts_by_year[year] += 1
        else:
            movie_counts_by_year[year] = 1

    keys = [str(k) for k in movie_counts_by_year.keys()]
    plt.bar(keys, movie_counts_by_year.values())
    plt.xticks(rotation=90)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png).decode('utf-8')

    return render(request, 'statistics.html', {'graphic': graphic})