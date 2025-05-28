# Nexay – Sistema de Mensagens

**Nexay** é um projeto **acadêmico e experimental** que simula um sistema de mensagens. Ele foi desenvolvido com o objetivo de aprender e aplicar boas práticas de segurança da informação. Não se trata de um produto pronto para produção, mas sim de uma base sólida para estudo e evolução.
A nossa aplicação utiliza **Python (Flask)** no backend e **React.js** no frontend, com comunicação entre as partes via **API RESTful**.

---

## Três Pilares de Segurança no Nexay

Durante o desenvolvimento, buscamos aplicar ao menos **três mecanismos centrais de segurança**:

1. **Autenticação via JWT (JSON Web Token)**
   Após o login e registro, o servidor gera um token JWT que é enviado ao cliente e usado para autenticação em cada requisição subsequente. Isso elimina a necessidade de sessões persistentes no servidor e melhora a escalabilidade.

2. **2FA (Autenticação de Dois Fatores por E-mail)**
   Para evitar acessos indevidos mesmo após o login com credenciais corretas, um segundo fator de verificação é enviado por e-mail, exigindo a confirmação de um código antes do acesso completo à conta.

3. **Registro de Logs Sensíveis no Banco de Dados**
   Toda ação relevante (login, logout, falhas de autenticação, envio de mensagens, alterações de senha, etc.) é registrada em uma tabela de logs no banco de dados, permitindo rastreabilidade e auditoria.

---

## Documentação Técnica

Na **raiz do projeto (`nexay/`)**, há uma pasta chamada `DOC/` contendo:

* Documento de Visão do Projeto (DVP)
* Cenários de Casos de Uso
* Diagrama de Casos de Uso
* Diagrama de Sequência

Esses arquivos descrevem como o sistema funciona, os fluxos principais e as interações esperadas.

---

## Funcionalidades Incluídas

* Cadastro e login de usuários
* Autenticação JWT e verificação 2FA por e-mail
* Envio e recebimento de mensagens
* Gerenciamento de contatos (adicionar, bloquear, excluir)
* Histórico de atividades via logs salvos no banco

---

## Autores

### Everton Hian dos Santos Pinheiro

* Backend (Flask, PostgreSQL, JWT)
* Arquitetura de Segurança
* Documentação Técnica

### Allan Kardec de Jesus Feliz Navegantes

* Frontend (React.js)
* Integração com APIs
* Design de Interface

---

## Requisitos para Execução

### Backend

* Python 3.10+
* PostgreSQL (rodando localmente ou em container)
* Ambiente virtual (recomendado)

### Frontend

* Node.js (18+)
* npm

---

## Configurando o Banco de Dados (PostgreSQL)
### Passo 1: Instale o PostgreSQL
Baixe e instale o PostgreSQL no seu computador.
Durante a instalação, anote a senha que você definiu para o usuário postgres.

### Passo 2: Abra o pgAdmin (Interface Gráfica do PostgreSQL)
Após instalar, procure por pgAdmin no seu computador e abra.
Clique em Servers > PostgreSQL e insira a senha que você criou.

### Passo 3: O Banco será Criado Automaticamente
O Nexay já tem um sistema que cria o banco de dados sozinho quando você inicia o backend. Você só precisa garantir que:
* O PostgreSQL está rodando.
* O usuário postgres existe e que sua configuração esta no .env.
---

## Configurando o Arquivo .env (Backend)
O .env guarda configurações importantes como senhas e chaves.
### Passo 1: Edite ou crie o arquivo .env na pasta backend/
    Copie o conteúdo abaixo e cole em um novo arquivo chamado .env:


```env
# Banco de Dados
SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://postgres:senha@localhost:5432/apiNexsay

# Chaves
SECRET_KEY=sua_chave_flask
JWT_SECRET_KEY=sua_chave_jwt

# Uploads
UPLOAD_FOLDER=uploads/fotos_perfil

# WebSocket
SOCKETIO_ASYNC_MODE=eventlet
SOCKETIO_CORS_ALLOWED_ORIGINS=http://localhost:3000
SOCKETIO_PING_TIMEOUT=60
SOCKETIO_PING_INTERVAL=25

# E-mail (2FA)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_app
MAIL_DEFAULT_SENDER=seu_email@gmail.com

# Ambiente
ENV=development
DEBUG=true
```
### Passo 2: Substitua os valores
* SUA_SENHA → A senha do PostgreSQL que você definiu na instalação.
* seu_email@gmail.com → Um e-mail Gmail (para enviar códigos 2FA).
* senha_do_app_do_gmail → Não é a senha do e-mail! É uma "Senha de App" (https://support.google.com/accounts/answer/185833?hl=pt-BR).


---

##  Como Executar o Projeto

### 1. Clonando o Repositório

Certifique-se de ter o **Git** instalado e execute o seguinte comando no terminal:

```bash
git clone https://github.com/EvertonHSP/Nexsay.git
cd Nexsay
```

---

### 2. Executando o Backend

> Requisitos: Python 3.8+, PostgreSQL instalado e rodando.

1. Acesse a pasta do backend:

```bash
cd backend
```

2. Crie e ative o ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure o banco de dados PostgreSQL e verifique se ele está rodando.

5. Realize as migrações:

Não é nescessário, ja existe a função **create_database_if_not_exists()** que inicializa o banco
**Porém** para essa função funcionar, o seu arquivo **.env** deve estar bem definido, pois vai ser nescessario acessar a senha do seu banco de dados


6. Inicie a aplicação:

```bash
python manage.py
```

---

### 3. Executando o Frontend

> Requisitos: Node.js e npm instalados.

1. Acesse a pasta do frontend:

```bash
cd ../frontend
```

2. Instale as dependências do React:

```bash
npm install
```

3. Configure as variáveis de ambiente, se necessário (ex: `.env` com URL da API).

4. Para ambiente de desenvolvimento:

```bash
npm start
```

5. Para ambiente de produção:

```bash
npm run build
npx serve -s build
```

---

## Bibliotecas Utilizadas no Frontend

| Biblioteca       | Comando para instalar          | Função principal                            |
| ---------------- | ------------------------------ | ------------------------------------------- |
| React            | `npm install react`            | Biblioteca principal para criar interfaces. |
| ReactDOM         | `npm install react-dom`        | Renderiza o app na árvore DOM do navegador. |
| React Router DOM | `npm install react-router-dom` | Gerenciamento de rotas entre páginas.       |
| Axios            | `npm install axios`            | Realiza requisições HTTP à API.             |
| Dotenv           | `npm install dotenv`           | Gerencia variáveis de ambiente no frontend. |

---

## Tecnologias Utilizadas

| Camada      | Tecnologias                                        |
| ----------- | -------------------------------------------------- |
| Backend     | Flask, Flask-JWT-Extended, SQLAlchemy, Flask-Mail  |
| Segurança   | JWT, 2FA, bcrypt, logs                             |
| Comunicação | Flask-SocketIO + WebSocket (eventlet)              |
| Banco       | PostgreSQL, Flask-Migrate                          |
| Frontend    | React.js, WebSocket Client, Axios                  |
| Infra       | Variáveis de ambiente, CORS, dotenv, logs em banco |

