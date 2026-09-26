# Agendamento Digital SUS

O **Agendamento Digital SUS** é uma aplicação web Full-Stack criada para facilitar o agendamento e o acompanhamento de consultas médicas nas Unidades Básicas de Saúde (UBS) da região de Patrocínio-MG. A solução busca ampliar o acesso da população aos serviços de saúde por meio de um fluxo simples, digital e integrado a uma API REST.

## Arquitetura

O projeto utiliza uma arquitetura desacoplada:

```text
frontend/  ->  HTML, CSS e JavaScript Vanilla  ->  API REST Flask  ->  SQLite
```

- **Back-end:** Python 3.13, Flask 3.0 e Flask-CORS.
- **Banco de dados:** SQLite, com criação automática do arquivo `backend/banco.db`.
- **Front-end:** HTML5, CSS3 e JavaScript Vanilla.
- **Comunicação:** requisições HTTP com `fetch` e respostas em JSON.
- **Hospedagem prevista:** PythonAnywhere para a API e GitHub Pages para o front-end.

## Estrutura do projeto

```text
sus_agendamento/
├── backend/
│   ├── app.py
│   └── requirements.txt
└── frontend/
    ├── admin.html
    ├── index.html
    ├── script.js
    └── style.css
```

## Como executar localmente

### 1. Pré-requisitos

- Python 3.13 ou versão compatível.
- Git, opcional para clonar o repositório.
- Um navegador atualizado.

### 2. Configurar o back-end

Abra um terminal na raiz do projeto e crie um ambiente virtual:

```powershell
python -m venv .venv
\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r backend\requirements.txt
```

Inicie a API:

```powershell
python backend\app.py
```

A API ficará disponível em `http://127.0.0.1:5000`. Na primeira execução, o banco SQLite e suas tabelas serão criados automaticamente.

### 3. Servir o front-end

Em outro terminal, na raiz do projeto, ative o mesmo ambiente virtual se necessário e execute:

```powershell
cd frontend
python -m http.server 5500
```

Acesse:

- Página de agendamento: `http://127.0.0.1:5500/index.html`
- Painel administrativo: `http://127.0.0.1:5500/admin.html`

O front-end está configurado para consumir a API local em `http://127.0.0.1:5000`. A API e o servidor do front-end devem permanecer em execução simultaneamente.

## Funcionalidades

- Agendamento de consultas por paciente, CPF, UBS, especialidade, data e horário.
- Consulta de agendamentos ativos por CPF.
- Painel administrativo com listagem de todos os registros.
- Cancelamento de consultas e liberação imediata da vaga.
- Remarcação de consultas com verificação de disponibilidade.
- Exclusão definitiva de registros já cancelados.
- Modais assíncronos de alerta e confirmação, evitando o uso dos alertas nativos do navegador.

## Regras de negócio

- Os horários são disponibilizados em intervalos de 15 minutos, entre 8h e 17h, com intervalo de almoço das 12h às 13h.
- Horários passados não podem ser agendados ou usados em uma remarcação.
- Um horário ativo não pode ser ocupado por mais de um agendamento na mesma UBS e especialidade.
- O CPF identifica unicamente o paciente.
- Um CPF já cadastrado só pode ser usado com o mesmo nome registrado no sistema.
- Apenas agendamentos com status `Ativo` aparecem na consulta pública por CPF.
- O cancelamento executa um **soft delete**: altera o status para `Cancelado` e libera a vaga.
- O botão **Limpar Registro** executa um **hard delete** somente para registros cancelados.
- A API rejeita remarcações para horários ocupados, passados ou para agendamentos inexistentes.

## Principais endpoints

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| `POST` | `/login` | Valida o acesso administrativo |
| `GET` | `/horarios-ocupados` | Lista horários ativos ocupados |
| `POST` | `/agendar` | Cria um novo agendamento |
| `GET` | `/agendamentos/<cpf>` | Consulta agendamentos ativos do paciente |
| `DELETE` | `/agendamentos/<id>` | Cancela um agendamento |
| `GET` | `/admin/todos` | Lista todos os agendamentos |
| `PUT` | `/admin/agendamentos/<id>/remarcar` | Remarca um agendamento |
| `DELETE` | `/admin/agendamentos/<id>/limpar` | Remove definitivamente um cancelamento |

## Acesso administrativo local

Na configuração inicial do sistema, o usuário administrativo criado automaticamente é:

```text
Usuário: controlador_sus
Senha: admin123
```

Altere essas credenciais antes de um uso em produção. Atualmente, o estado de login do painel é mantido no `sessionStorage` do navegador; para ambientes públicos, recomenda-se evoluir a autenticação para sessões ou tokens validados também no back-end e proteger as rotas administrativas na API.

## Deploy

### Back-end no PythonAnywhere

1. Crie uma aplicação web Python no PythonAnywhere.
2. Envie o conteúdo do diretório `backend/` para o servidor.
3. Crie um ambiente virtual com a versão de Python compatível.
4. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

5. Configure o arquivo WSGI para importar a variável `app` de `app.py`.
6. Garanta permissão de escrita no diretório para que o SQLite possa criar e atualizar `banco.db`.
7. Reinicie a aplicação e teste a URL pública da API.

### Front-end no GitHub Pages

1. Publique os arquivos da pasta `frontend/` em um repositório ou em uma branch configurada para o GitHub Pages.
2. Em `frontend/script.js` e no script de `frontend/admin.html`, substitua:

   ```javascript
   const API_URL = 'http://127.0.0.1:5000';
   ```

   pela URL HTTPS da aplicação no PythonAnywhere, por exemplo:

   ```javascript
   const API_URL = 'https://seu-usuario.pythonanywhere.com';
   ```

3. Verifique se o CORS da API permite a origem publicada no GitHub Pages.
4. Teste criação, consulta, cancelamento e remarcação usando a URL publicada.

O GitHub Pages hospeda somente arquivos estáticos. A API Flask, o banco SQLite e as regras de negócio continuam executando no PythonAnywhere.

## Observações de produção

- Use HTTPS tanto no front-end quanto na API.
- Substitua as credenciais administrativas padrão.
- Restrinja as rotas `/admin/*` no back-end, pois a validação atualmente ocorre no fluxo do painel do navegador.
- Faça cópias de segurança do arquivo `banco.db`.
- Configure o CORS para aceitar somente as origens necessárias.