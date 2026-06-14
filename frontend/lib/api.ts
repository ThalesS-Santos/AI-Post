import axios, { AxiosProgressEvent } from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 60000,
});

export function setAuthToken(token: string) {
  api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}

export interface PostContent {
  titulo_interno: string;
  legenda_instagram: string;
  sugestao_de_edicao_visual: string;
  hashtags: string[];
}

export async function gerarPosts(
  clienteId: string,
  focoSemana: string,
  quantidade = 7
): Promise<PostContent[]> {
  const { data } = await api.post("/api/v1/gerar-posts", {
    cliente_id: clienteId,
    foco_semana: focoSemana,
    quantidade,
  });
  return data.posts as PostContent[];
}

export async function uploadProduto(
  clienteId: string,
  arquivo: File,
  textoBase: string,
  onProgress?: (pct: number) => void
): Promise<{ id: string; url: string }> {
  const form = new FormData();
  form.append("arquivo", arquivo);
  form.append("cliente_id", clienteId);
  form.append("texto_base", textoBase);

  const { data } = await api.post("/api/v1/upload-produto", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e: AxiosProgressEvent) => {
      if (e.total) onProgress?.(Math.round((e.loaded / e.total) * 100));
    },
  });
  return data;
}

export async function setupMarca(payload: {
  clienteId: string;
  nomeMarca: string;
  tomVoz: string;
  nicho: string;
  descricao?: string;
}): Promise<void> {
  await api.post("/api/v1/setup-marca", {
    cliente_id: payload.clienteId,
    nome_marca: payload.nomeMarca,
    tom_voz: payload.tomVoz,
    nicho: payload.nicho,
    descricao: payload.descricao,
  });
}

export default api;
