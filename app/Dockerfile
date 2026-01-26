# Usa a imagem oficial do Python 3.11 (versão slim para ser mais leve)
FROM python:3.11-slim
 
# Define o diretório de trabalho dentro do container
WORKDIR /app
 
# Instala dependências do sistema necessárias para algumas bibliotecas Python

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
&& rm -rf /var/lib/apt/lists/*
 
# Copia o arquivo de requisitos e instala as bibliotecas

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
 
# Copia o restante do código da aplicação

COPY . .
 
# Expõe a porta padrão do Streamlit

EXPOSE 8501
 
# Comando para rodar a aplicação

ENTRYPOINT ["streamlit", "run", "projeto_sacre.py", "--server.port=8501", "--server.address=0.0.0.0"]
 