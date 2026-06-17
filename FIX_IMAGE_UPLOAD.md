# 🔧 Fix: Imagens não salvam no Supabase

## ❌ Problema
O código estava salvando imagens **localmente no servidor** em vez de usar o **Supabase Storage**. Em produção (Render/Netlify), isso não funciona porque:
- A URL `localhost:8000` não existe
- Arquivos locais são deletados quando o server reinicia
- Frontend no Netlify não consegue acessar

## ✅ Solução
Corrigi o código para usar o Supabase Storage de verdade. Agora você precisa:

### 1. Criar o Bucket no Supabase
1. Acesse seu dashboard do Supabase: https://supabase.com/
2. Vá em **Storage**
3. Clique em **Create a new bucket**
4. Nome: **catalogo-produtos**
5. Marque **Public bucket** (para poder acessar as imagens públicamente)
6. Clique **Create bucket**

### 2. Configurar Permissões (Policy)
1. No bucket **catalogo-produtos**, vá em **Policies**
2. Clique em **New Policy**
3. Escolha **For authenticated users**
4. Deixe tudo com permissões **SELECT, INSERT, UPDATE, DELETE**
5. Salve

### 3. Fazer Deploy da Atualização
No **Render** (backend):
1. Vá em seu projeto
2. Clique em **Manual Deploy** → **Deploy latest commit**
3. Espere a build terminar

No **Netlify** (frontend):
1. Vai fazer redeploy automaticamente quando o backend estiver pronto

### 4. Testar
Tente fazer upload de uma imagem novamente. Agora deve funcionar! ✨

## 📝 Variáveis de Ambiente (certifique-se que estão no Render)
```
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_chave_service_role
SUPABASE_ANON_KEY=sua_chave_anon
GEMINI_API_KEY=sua_chave_gemini
JWT_SECRET=sua_chave_jwt
ALLOWED_ORIGINS=https://seu-site.netlify.app
```

## 🐛 Se ainda não funcionar
1. Verifique os logs no Render (Dashboard → Logs)
2. Abra o DevTools do navegador (F12) → Network
3. Veja qual erro aparece no upload
4. Compartilhe o erro para debugar

Pronto! 🎉
