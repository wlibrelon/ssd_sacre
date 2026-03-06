# SACRE - Soluções Integradas de Água para Cidades Resilientes

## Visão Geral

O projeto SACRE é uma aplicação web baseada em Streamlit, projetada para ser um sistema de suporte à decisão (SSD) focado na gestão de recursos hídricos. A plataforma permite a visualização, análise e gerenciamento de dados geoespaciais, químicos e de projetos relacionados à água, visando promover a resiliência de cidades.

A arquitetura é baseada em microserviços containerizados, incluindo a aplicação principal em Python, um banco de dados MySQL e um servidor web Nginx como proxy reverso.

## Ferramentas Necessárias

Para executar, desenvolver ou fazer o deploy desta aplicação, as seguintes ferramentas são essenciais:

*   **Docker:** Para a execução dos contêineres da aplicação, banco de dados e servidor web.
*   **Docker Compose:** Para orquestrar os múltiplos contêineres da aplicação.
*   **Git:** Para controle de versão e colaboração no código-fonte.
*   **Um navegador web:** Para acessar a interface da aplicação.

## Gitflow (Fluxo de Trabalho com Git)

O projeto adota um fluxo de trabalho baseado no Gitflow para organizar o desenvolvimento:

*   `main`: Contém o código de produção estável. Nenhuma submissão direta é permitida. Merges para a `main` são feitos apenas a partir da `develop` ou de `hotfix`.
*   `develop`: Ramo principal de desenvolvimento. Integra as novas funcionalidades e correções antes de serem enviadas para a `main`.
*   `feature/<nome-da-feature>`: Ramos criados a partir da `develop` para desenvolver novas funcionalidades. Ex: `feature/novo-dashboard-analitico`.
*   `bugfix/<nome-do-bug>`: Ramos criados a partir da `develop` para corrigir bugs não críticos.
*   `hotfix/<nome-da-correcao>`: Ramos criados a partir da `main` para correções críticas em produção. Após a correção, devem ser mesclados de volta na `main` e na `develop`.

**Processo:**
1.  Para uma nova funcionalidade, crie um ramo `feature/*` a partir da `develop`.
2.  Ao concluir o desenvolvimento, abra um Pull Request (PR) para mesclar o seu ramo na `develop`.
3.  Após a aprovação e testes, o código da `develop` é mesclado na `main` para um novo release.

## Como Fazer o Deploy da Aplicação em ambiente novo

O deploy da aplicação é orquestrado com Docker Compose em diferentes contextos (banco de dados, aplicação e proxy). Siga os passos abaixo para implantar o ambiente completo em um ambiente de produção ou desenvolvimento.

**Passo 1: Clonar o Repositório**

```bash
git clone <URL_DO_REPOSITORIO>
cd ssd_sacre
```

**Passo 2: Criar a Rede Docker Externa**

A comunicação entre os contêineres depende de uma rede externa compartilhada. Crie-a com o seguinte comando (executar somente uma vez):

```bash
docker network create sacre
```

**Passo 3: Iniciar o Banco de Dados**

O serviço de banco de dados MySQL é o primeiro a ser iniciado, pois a aplicação depende dele.

```bash
docker-compose -f database/docker-compose.yml up -d
```
O banco de dados será inicializado com os schemas e dados localizados em `database/init-db/`.

**Passo 4: Iniciar a Aplicação Streamlit**

Com o banco de dados em execução, inicie o contêiner da aplicação. O comando `--build` garante que a imagem será construída com as dependências mais recentes do `requirements.txt`.

```bash
docker-compose -f app/docker-compose.yml up -d --build
```
A aplicação estará disponível na porta `8501`.

**Passo 5: Iniciar o Nginx (Proxy Reverso)**

O Nginx atua como proxy reverso, gerenciando o tráfego e a segurança (SSL). Ele direciona as requisições das portas 80/443 para a aplicação Streamlit.

```bash
docker-compose -f devops/docker-compose.yml up -d
```

Após estes passos, a aplicação estará acessível através do endereço do seu servidor web (ex: `http://localhost` ou `https://seu-dominio.com`).

### Parando os Serviços

Para parar todos os serviços, execute os comandos `down` na ordem inversa ou de forma independente:

```bash
docker-compose -f devops/docker-compose.yml down
docker-compose -f app/docker-compose.yml down
docker-compose -f database/docker-compose.yml down
```

## Como Fazer o Deploy de Atualizões no Aplicativo

A aplicação está contida no diretório /app e sua atualiza deve ser feita da seguinte forma:

**Passo 1: garantir que a branch `main` contém as alterações.**

**Passo 2: no servidor, acessar `/source/ssd_sacre` e executar:**

```bash
git fetch
git pull
```

**Passo3: acessar a pasta `./app` e rodar:**

```bash
docker compose down
docker compose up -d --build
```

