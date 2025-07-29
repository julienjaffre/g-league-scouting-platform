# Étape 1 : image de base
FROM python:3.12-slim

# Étape 2 : installation des dépendances système
RUN apt-get update && apt-get install -y \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Étape 3 : définition du répertoire de travail
WORKDIR /app

# Étape 4 : copie du code source dans l'image
COPY . /app

# Étape 5 : installation de Poetry et des dépendances
RUN pip install poetry
RUN poetry config virtualenvs.create false \
  && poetry install --only main

# Étape 6 : exposition du port utilisé par Streamlit
EXPOSE 8501

# Étape 7 : commande de lancement de l'app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
