# OurCore/N1 — Guia de Execução Local

Plataforma de geração de conteúdo para Instagram com IA. Gera legendas, títulos e hashtags personalizados analisando fotos reais de produtos via Gemini multimodal.

---

## 📋 Requisitos do Sistema

- **Python 3.14** (instalado via Windows Package Manager ou [python.org](https://python.org))
- **Node.js 18+** (para o frontend)
- **Git**
- **Contas externas (gratuitas)**:
  - [Supabase](https://supabase.com) — banco de dados + storage
  - [Google AI Studio](https://aistudio.google.com) — chave Gemini

**Verificar instalações:**
```powershell
py -3.14 --version
node --version
npm --version
git --version
```

---

## 🔧 Passo 1: Configurar Supabase

### 1.1 Criar um novo projeto

1. Acesse [app.supabase.com](https://app.supabase.com)
2. Clique em **New Project**
3. Preencha:
   - **Name**: `OurCore` (ou o nome que preferir)
   - **Database Password**: crie uma senha forte (você precisará dela)
   - **Region**: `South America (São Paulo)` — mais próximo
4. Clique **Create new project** e aguarde ~2 minutos

### 1.2 Obter as chaves

Dentro do projeto Supabase:

1. Vá para **Settings** → **API** (no menu esquerdo)
2. Copie:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` → `SUPABASE_ANON_KEY`
   - `service_role secret` → `SUPABASE_SERVICE_ROLE_KEY`
   - `JWT Secret` → `JWT_SECRET`

(Você vai usar essas chaves nos arquivos `.env` mais adiante)

### 1.3 Executar as migrações de banco

1. No dashboard Supabase, vá para **SQL Editor** (menu esquerdo)
2. Clique no botão **+ New Query**
3. Cole todo o conteúdo do arquivo [`supabase/migrations/001_init.sql`](supabase/migrations/001_init.sql)
4. Clique **Run** (canto inferior direito)

**Resultado esperado:** A tabela `embeddings_marca` e a função RPC `buscar_contexto_similar` serão criadas.

### 1.4 Criar o bucket de storage

1. No Supabase, vá para **Storage** (menu esquerdo)
2. Clique **New Bucket**
3. Nome: `catalogo-produtos`
4. Marque **Public bucket** (importante — sem isso, as fotos não carregam)
5. Clique **Create bucket**

---

## 🐍 Passo 2: Executar o Backend (FastAPI)

### 2.1 Configurar variáveis de ambiente

1. Abra PowerShell e navegue até a pasta do backend:
   ```powershell
   cd C:\GitHub\Trabalho-IA-UFBA\backend
   ```

2. Copie o arquivo de exemplo:
   ```powershell
   cp .env.example .env
   ```

3. Abra o arquivo `.env` com um editor de texto (notepad ou VS Code):
   ```powershell
   notepad .env
   ```

4. Preencha com os valores obtidos no Passo 1.2:
   ```env
   SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   GEMINI_API_KEY=AIzaSyD...
   JWT_SECRET=super-secret-jwt-key-from-supabase
   JWT_ALGORITHM=HS256
   ALLOWED_ORIGINS=http://localhost:3000
   ```

   **Onde pegar cada uma:**
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`: Settings → API (conforme 1.2)
   - `GEMINI_API_KEY`: veja seção 2.3 abaixo
   - `JWT_SECRET`: Settings → API → JWT Secret do Supabase

### 2.2 Instalar dependências do backend

```powershell
cd C:\GitHub\Trabalho-IA-UFBA\backend
py -3.14 -m pip install -r requirements.txt
```

**Esperado:** Instala ~30 pacotes. Se der erro de wheel, verifique se tem Python 3.14 instalado corretamente.

### 2.3 Obter chave da Gemini API

1. Acesse [aistudio.google.com](https://aistudio.google.com)
2. Clique **Get API Key** (canto superior direito)
3. Escolha **Create API key in new Google Cloud project**
4. Copie a chave exibida
5. Cole no arquivo `.env` como `GEMINI_API_KEY`

### 2.4 Rodar o servidor FastAPI

```powershell
cd C:\GitHub\Trabalho-IA-UFBA\backend
py -3.14 -m uvicorn app.main:app --reload
```

**Resultado esperado:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

Deixe esse terminal aberto. A API estará disponível em `http://localhost:8000`.

**Verificar se está rodando:**
```powershell
# Em outro terminal PowerShell:
curl http://localhost:8000/health
```

Deve retornar: `{"status":"ok"}`

---

## 🎨 Passo 3: Executar o Frontend (Next.js)

### 3.1 Instalar dependências do frontend

Abra um **novo terminal PowerShell** e navegue para o frontend:

```powershell
cd C:\GitHub\Trabalho-IA-UFBA\frontend
npm install
```

**Esperado:** Instala ~200 pacotes (leva 3-5 minutos).

### 3.2 Configurar variáveis de ambiente

1. Copie o arquivo de exemplo:
   ```powershell
   cp .env.local.example .env.local
   ```

2. Abra e preencha:
   ```powershell
   notepad .env.local
   ```

   **Conteúdo:**
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

   - `NEXT_PUBLIC_API_URL` — URL do backend (deixe como está se rodar local)
   - `NEXT_PUBLIC_SUPABASE_URL` e `NEXT_PUBLIC_SUPABASE_ANON_KEY` — do Passo 1.2

### 3.3 Rodar o servidor de desenvolvimento

No terminal do frontend:

```powershell
cd C:\GitHub\Trabalho-IA-UFBA\frontend
npm run dev
```

**Resultado esperado:**
```
  ▲ Next.js 14.2.5
  - Local:        http://localhost:3000
```

---

## 🌐 Acessar a aplicação

Abra o navegador em:
```
http://localhost:3000
```

Você verá a **Welcome Page** com a malha 3D de partículas.

---

## 📝 Fluxo de Teste Completo

### 1. **Welcome Page** (`/`)
- Veja a animação da malha 3D
- Clique em **"Começar grátis"** → vai para `/setup`

### 2. **Setup de Marca** (`/setup` — Step 1)
Preencha o formulário:
- **Nome da marca**: `Doceria da Jú`
- **Tom de voz**: `Jovem, descontraído, apaixonado por doces artesanais`
- **Nicho**: `Confeitaria gourmet`
- **Descrição**: `Bolos e brigadeiros feitos à mão`

Clique **Próximo →**

**Esperado:** Marca é salva no Supabase e você avança para o Step 2.

### 3. **Upload de Produtos** (`/setup` — Step 2)
- Arraste uma foto de um produto (qualquer imagem servirá para teste)
- Ou clique na zona para selecionar
- Preencha: `Brigadeiro de morango com cobertura de chocolate`
- Clique **Adicionar ao catálogo**

**Esperado:** Foto é comprimida (Pillow), enviada ao Storage, e um embedding é gerado.

### 4. **Dashboard de Geração** (`/dashboard`)
- Clique **"Ir para o Dashboard"** (fim do Setup Step 2)
- Ou acesse direto: `http://localhost:3000/dashboard`

### 5. **Gerar Posts**
- Preencha o campo: `Dia dos Namorados — foco em presentes românticos`
- Clique **✦ Gerar Semana de Posts**

**Esperado:**
1. Skeleton loaders aparecem (pulsando)
2. Após 5-10 segundos, 7 cards com posts aparecem
3. Cada card tem:
   - Título interno
   - Legenda Instagram
   - Sugestão de edição visual
   - Hashtags

### 6. **Copiar Conteúdo**
Clique **"Copiar legenda + hashtags"** em qualquer card.

A legenda + hashtags serão copiadas para a clipboard. Cole no Instagram.

---

## 🐛 Troubleshooting

### Backend não inicia
**Erro:** `ModuleNotFoundError: No module named 'fastapi'`

**Solução:**
```powershell
# Certifique-se de estar na pasta backend
cd C:\GitHub\Trabalho-IA-UFBA\backend
py -3.14 -m pip install -r requirements.txt
```

---

### `GEMINI_API_KEY` inválida
**Erro:** `ValueError: API key not valid.`

**Solução:**
1. Verifique que a chave foi copiada inteira (sem espaços)
2. Gere uma nova em [aistudio.google.com](https://aistudio.google.com)
3. Restarte o servidor FastAPI (Ctrl+C e rode de novo)

---

### Frontend não conecta ao backend
**Erro:** `Failed to fetch from http://localhost:8000`

**Solução:**
1. Verifique que o backend está rodando: `curl http://localhost:8000/health`
2. Se retornar erro, o backend não está ativo — rode `py -3.14 -m uvicorn app.main:app --reload`
3. Se a porta 8000 já está em uso:
   ```powershell
   # Libere a porta ou rode em outra:
   py -3.14 -m uvicorn app.main:app --reload --port 8001
   # E atualize .env.local: NEXT_PUBLIC_API_URL=http://localhost:8001
   ```

---

### Erro ao fazer upload de foto
**Erro:** `Erro no upload. Tente novamente.`

**Solução:**
1. Verifique que o bucket `catalogo-produtos` foi criado (Supabase → Storage)
2. Verifique que está marcado como **Public bucket**
3. Verifique `SUPABASE_SERVICE_ROLE_KEY` no `.env` (backend)

---

### Posts não são gerados
**Erro:** `Nenhum contexto de marca encontrado.`

**Solução:**
1. Execute o setup de marca primeiro (você pulou para o dashboard sem preencher a marca?)
2. Verifique que a tabela `embeddings_marca` foi criada (SQL do Passo 1.3)
3. Verifique os logs do FastAPI (terminal backend) — pode haver erro de autenticação Supabase

---

### Erro de CORS
**Erro no console do navegador:** `Access to XMLHttpRequest blocked by CORS policy`

**Solução:**
Verifique que `ALLOWED_ORIGINS` no `.env` (backend) está correto:
```env
ALLOWED_ORIGINS=http://localhost:3000
```

Depois reinicie o FastAPI.

---

## 📊 Arquitetura de Pastas

```
Trabalho-IA-UFBA/
├── README.md                        ← você está aqui
├── supabase/migrations/001_init.sql ← schema do banco
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes.py
│   │   ├── core/(config, security)
│   │   ├── services/(llm, rag, storage)
│   │   ├── models/database.py
│   │   └── schemas/
│   └── [venv/] ← opcional (env Python virtual)
│
└── frontend/
    ├── .env.local.example
    ├── package.json
    ├── app/(layout, pages)
    ├── components/(UI, Three.js)
    ├── lib/(API client, context)
    └── node_modules/ ← gerado por npm install
```

---

## 🚀 Próximos Passos (Após Testar)

1. **Deploy do Backend:** Vercel, Railway, Render (Python support)
2. **Deploy do Frontend:** Vercel, Netlify (otimizado para Next.js)
3. **Autenticação Real:** Integrar com `supabase.auth.signUp()` em vez do demo `DEMO_CLIENT_ID`
4. **Banco de Dados de Usuários:** Extensão do Supabase auth com tabela `profiles`

---

## 📚 Referências

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Next.js Docs](https://nextjs.org/docs)
- [Supabase Docs](https://supabase.com/docs)
- [Google Gemini API](https://ai.google.dev)
- [Framer Motion](https://www.framer.com/motion)

---

## 💡 Dicas

- **Desenvolvimento mais rápido:** Use `--reload` no FastAPI (recarrega ao salvar arquivo)
- **Limpar cache frontend:** Abra DevTools (F12) → Cmd+Shift+R (hard refresh)
- **Ver logs do backend:** Todos os requests aparecem no terminal onde rodou `uvicorn`
- **Testar API manualmente:** Use Postman, Insomnia, ou `curl` (exemplos abaixo)

---

## 🧪 Testar a API com cURL

Gerar posts (exemplo):
```powershell
$headers = @{
    "Authorization" = "Bearer seu_token_jwt_aqui"
    "Content-Type" = "application/json"
}

$body = @{
    cliente_id = "00000000-0000-0000-0000-000000000001"
    foco_semana = "Black Friday"
    quantidade = 3
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/v1/gerar-posts" `
    -Headers $headers `
    -Body $body `
    -Method Post
```

Para simplificar durante testes, a segurança JWT foi deixada comentada — descomente em produção.

---

**Pronto para começar? Execute o Passo 1 acima! 🚀**
