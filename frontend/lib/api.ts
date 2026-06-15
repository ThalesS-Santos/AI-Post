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
  local_do_preco?: string;
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
  preco?: string;
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
  quantidade = 7,
  estilos_imagem: string[] = []
): Promise<GerarPostsResultado> {
  const { data } = await api.post(
    "/api/v1/gerar-posts",
    { cliente_id: clienteId, foco_semana: foco, quantidade, estilos_imagem },
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
  produtoId: string,
  estilos_imagem: string[] = []
): Promise<PostContent> {
  const { data } = await api.post(
    "/api/v1/regenerar-legenda",
    { cliente_id: clienteId, foco_semana: foco, produto_id: produtoId, estilos_imagem },
    { timeout: 60000 }
  );
  return data as PostContent;
}

export async function regenerarImagem(
  clienteId: string,
  foco: string,
  produtoId: string,
  legenda: string,
  estilos_imagem: string[] = []
): Promise<{ imagem_gerada_base64: string | null; imagem_disponivel: boolean }> {
  const { data } = await api.post(
    "/api/v1/regenerar-imagem",
    { cliente_id: clienteId, foco_semana: foco, produto_id: produtoId, legenda, estilos_imagem },
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
  preco: string = "",
  onProgress?: (pct: number) => void
): Promise<{ id: string; url: string }> {
  const form = new FormData();
  form.append("arquivo", arquivo);
  form.append("cliente_id", clienteId);
  form.append("texto_base", textoBase);
  form.append("preco", preco);

  const { data } = await api.post("/api/v1/upload-produto", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e: AxiosProgressEvent) => {
      if (e.total) onProgress?.(Math.round((e.loaded / e.total) * 100));
    },
  });
  return data;
}

export async function uploadLogo(
  clienteId: string,
  arquivo: File,
  onProgress?: (pct: number) => void
): Promise<{ url_logo: string }> {
  const form = new FormData();
  form.append("arquivo", arquivo);
  form.append("cliente_id", clienteId);

  const { data } = await api.post("/api/v1/upload-logo", form, {
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

export async function updateProduto(clienteId: string, produtoId: string, textoBase: string, preco: string = "") {
  await api.put(`/api/v1/produtos/${clienteId}/${produtoId}`, {
    texto_base: textoBase,
    preco: preco,
  });
}

export async function deleteProduto(clienteId: string, produtoId: string) {
  await api.delete(`/api/v1/produtos/${clienteId}/${produtoId}`);
}

export interface MarcaSetup {
  id: string;
  nome_marca: string;
  tom_voz: string;
  nicho: string;
  descricao: string;
  url_logo: string;
}

export async function getMarca(clienteId: string): Promise<MarcaSetup> {
  const { data } = await api.get(`/api/v1/setup-marca/${clienteId}`);
  return data as MarcaSetup;
}

export async function updateMarca(payload: {
  clienteId: string;
  nomeMarca: string;
  tomVoz: string;
  nicho: string;
  descricao?: string;
}): Promise<void> {
  await api.put(`/api/v1/setup-marca/${payload.clienteId}`, {
    cliente_id: payload.clienteId,
    nome_marca: payload.nomeMarca,
    tom_voz: payload.tomVoz,
    nicho: payload.nicho,
    descricao: payload.descricao,
  });
}

export default api;
