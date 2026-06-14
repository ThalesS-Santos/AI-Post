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
  produto_id?: string | null;
  produto_url?: string | null;
  imagem_gerada_base64?: string | null;
  imagem_disponivel?: boolean;
}

export interface GerarPostsResultado {
  posts: PostContent[];
  gerados: number;
  solicitados: number;
}

export interface ProdutoSalvo {
  id: string;
  texto_base: string;
  url_imagem: string;
}

/** Extrai a mensagem de erro do backend (campo "detail"). */
export function mensagemErro(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail;
    return detail ?? error.message;
  }
  return error instanceof Error ? error.message : fallback;
}

export async function gerarPosts(
  clienteId: string,
  foco: string,
  quantidade = 7
): Promise<GerarPostsResultado> {
  const { data } = await api.post(
    "/api/v1/gerar-posts",
    { cliente_id: clienteId, foco_semana: foco, quantidade },
    // Geração com imagens pode levar minutos para lotes grandes.
    { timeout: 300000 }
  );
  return {
    posts: data.posts as PostContent[],
    gerados: data.gerados ?? data.posts.length,
    solicitados: data.solicitados ?? quantidade,
  };
}

export async function listarProdutos(clienteId: string): Promise<ProdutoSalvo[]> {
  const { data } = await api.get(`/api/v1/produtos/${clienteId}`);
  return data.produtos as ProdutoSalvo[];
}

export interface SetupStatus {
  tem_marca: boolean;
  tem_fotos: boolean;
  total_fotos: number;
}

export async function getStatus(clienteId: string): Promise<SetupStatus> {
  const { data } = await api.get(`/api/v1/status/${clienteId}`);
  return {
    tem_marca: !!data.tem_marca,
    tem_fotos: !!data.tem_fotos,
    total_fotos: data.total_fotos ?? 0,
  };
}

export async function regenerarLegenda(
  clienteId: string,
  foco: string,
  produtoId: string
): Promise<PostContent> {
  const { data } = await api.post(
    "/api/v1/regenerar-legenda",
    { cliente_id: clienteId, foco_semana: foco, produto_id: produtoId },
    { timeout: 60000 }
  );
  return data as PostContent;
}

export async function regenerarImagem(
  clienteId: string,
  foco: string,
  produtoId: string,
  legenda: string
): Promise<{ imagem_gerada_base64: string | null; imagem_disponivel: boolean }> {
  const { data } = await api.post(
    "/api/v1/regenerar-imagem",
    { cliente_id: clienteId, foco_semana: foco, produto_id: produtoId, legenda },
    { timeout: 120000 }
  );
  return {
    imagem_gerada_base64: data.imagem_gerada_base64 ?? null,
    imagem_disponivel: data.imagem_disponivel ?? false,
  };
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
