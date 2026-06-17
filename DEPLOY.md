# 🚀 Guia de Deploy

Seu projeto está pronto para deploy! Código já configurado no branch `luca`.

## Deploy do Frontend (Next.js) → Vercel

1. Acesse: https://vercel.com/new
2. Clique em **"Continue with GitHub"** (se não estiver logado, faça login)
3. Autorize o Vercel a acessar seus repositórios
4. Procure por **"AI-Post"** e clique em **Import**
5. Configure:
   - **Project Name**: AI-Post (ou outro nome)
   - **Framework Preset**: Next.js
   - Deixe o resto padrão
6. Clique em **Deploy** e espere (leva ~3-5 min)
7. Pronto! Seu site estará em `https://seu-projeto.vercel.app`

## Deploy do Backend (FastAPI) → Railway

1. Acesse: https://railway.app
2. Clique em **"Start Project"** → **"Deploy from GitHub repo"**
3. Autorize o Railway a acessar seus repositórios
4. Procure por **"AI-Post"** e selecione
5. Configure:
   - **Root Directory**: `backend`
   - Clique em **Deploy**
6. Railway criará uma URL para seu backend automaticamente
7. Copie a URL base (ex: `https://seu-backend.railway.app`)

## Configurar URL do Backend no Frontend

1. Após o deploy do backend, copie sua URL
2. No Vercel, vá em **Project Settings** → **Environment Variables**
3. Adicione:
   ```
   NEXT_PUBLIC_API_URL=https://seu-backend.railway.app
   ```
4. Redeploy o frontend (Vercel vai redeployar automaticamente)

## Variáveis de Ambiente Necessárias

### Backend (Railway)
- `SUPABASE_URL`: Sua URL do Supabase
- `SUPABASE_KEY`: Sua chave do Supabase
- `GOOGLE_GENAI_API_KEY`: Sua chave do Google Gemini
- Outras conforme seu `.env.example`

Para adicionar no Railway:
1. Vá em **Project** → **Variables**
2. Adicione cada variável manualmente

### Frontend (Vercel)
- `NEXT_PUBLIC_API_URL`: URL do backend
- Outras variáveis públicas necessárias

## Pronto! ✨

Seu site estará no ar em:
- **Frontend**: https://seu-projeto.vercel.app
- **Backend**: https://seu-backend.railway.app

Qualquer dúvida, o suporte do Vercel e Railway é bem rápido!
