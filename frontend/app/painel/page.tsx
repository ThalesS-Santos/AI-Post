"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/ui/Navbar";
import { PageLoader } from "@/components/ui/PageLoader";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import {
  listarProdutos,
  deleteProduto,
  updateProduto,
  ProdutoSalvo,
  getMarca,
  updateMarca,
  uploadLogo,
  uploadProduto,
  MarcaSetup,
  listarPostsSalvos,
  deletarPostSalvo,
  PostSalvo,
} from "@/lib/api";

export default function PainelPage() {
  const { user, loading: authLoading, updateUserName } = useAuth();
  const router = useRouter();
  const { toast: addToast } = useToast();

  const [activeTab, setActiveTab] = useState<"perfil" | "marca" | "fotos" | "posts_salvos">("fotos");
  const [loadingData, setLoadingData] = useState(true);

  // Posts Salvos State
  const [postsSalvos, setPostsSalvos] = useState<PostSalvo[]>([]);
  const [copiedPostId, setCopiedPostId] = useState<string | null>(null);
  const [expandedPosts, setExpandedPosts] = useState<Record<string, boolean>>({});

  // Perfil State
  const [userName, setUserName] = useState("");

  // Marca State
  const [marca, setMarca] = useState<MarcaSetup | null>(null);
  const [nomeMarca, setNomeMarca] = useState("");
  const [nicho, setNicho] = useState("");
  const [tomVoz, setTomVoz] = useState("");
  const [descricao, setDescricao] = useState("");
  const [logoFile, setLogoFile] = useState<File | null>(null);

  // Fotos State
  const [produtos, setProdutos] = useState<ProdutoSalvo[]>([]);
  const [newFotoFile, setNewFotoFile] = useState<File | null>(null);
  const [newFotoDesc, setNewFotoDesc] = useState("");
  const [newFotoPreco, setNewFotoPreco] = useState("");

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      setUserName(user.user_metadata?.full_name || "");
      loadData();
    }
  }, [user]);

  async function loadData() {
    setLoadingData(true);
    try {
      const p = await listarProdutos(user!.id);
      setProdutos(p);

      try {
        const m = await getMarca(user!.id);
        setMarca(m);
        setNomeMarca(m.nome_marca || "");
        setNicho(m.nicho || "");
        setTomVoz(m.tom_voz || "");
        setDescricao(m.descricao || "");
      } catch (err) {
        console.log("Marca não encontrada", err);
      }

      try {
        const posts = await listarPostsSalvos(user!.id);
        setPostsSalvos(posts);
      } catch (err) {
        console.log("Erro ao carregar posts salvos", err);
      }
    } catch (error: any) {
      addToast(error.message || "Erro ao carregar dados", "error");
    } finally {
      setLoadingData(false);
    }
  }

  const handleDeletePostSalvo = async (id: string) => {
    if (!confirm("Certeza que deseja excluir este post do histórico?")) return;
    try {
      await deletarPostSalvo(id);
      addToast("Post excluído com sucesso!", "success");
      setPostsSalvos(postsSalvos.filter((p) => p.id !== id));
    } catch (err: any) {
      addToast(err.message || "Não foi possível excluir o post.", "error");
    }
  };

  const handleCopyLegendaSalva = (post: PostSalvo) => {
    navigator.clipboard.writeText(
      `${post.legenda_instagram}\n\n${post.hashtags.map((h) => `#${h}`).join(" ")}`
    );
    setCopiedPostId(post.id);
    addToast("Legenda copiada!", "success");
    setTimeout(() => setCopiedPostId(null), 2000);
  };

  const handleSavePerfil = async () => {
    try {
      await updateUserName(userName);
      addToast("Perfil atualizado!", "success");
    } catch (err: any) {
      addToast(err.message, "error");
    }
  };

  const handleSaveMarca = async () => {
    try {
      await updateMarca({
        clienteId: user!.id,
        nomeMarca,
        tomVoz,
        nicho,
        descricao,
      });

      if (logoFile) {
        await uploadLogo(user!.id, logoFile);
        setLogoFile(null);
      }

      addToast("Marca atualizada com sucesso!", "success");
      loadData();
    } catch (err: any) {
      addToast(err.message, "error");
    }
  };

  const handleSaveProduto = async (p: ProdutoSalvo) => {
    try {
      await updateProduto(user!.id, p.id, p.texto_base, p.preco || "");
      addToast("Produto atualizado!", "success");
    } catch (err: any) {
      addToast(err.message, "error");
    }
  };

  const handleDeleteProduto = async (id: string) => {
    if (!confirm("Certeza que deseja excluir esta foto?")) return;
    try {
      await deleteProduto(user!.id, id);
      addToast("Produto excluído!", "success");
      setProdutos(produtos.filter((p) => p.id !== id));
    } catch (err: any) {
      addToast(err.message, "error");
    }
  };

  const handleUploadFoto = async () => {
    if (!newFotoFile) return addToast("Selecione uma imagem", "error");
    if (!newFotoDesc) return addToast("Escreva uma descrição", "error");

    try {
      await uploadProduto(user!.id, newFotoFile, newFotoDesc, newFotoPreco);
      addToast("Foto enviada com sucesso!", "success");
      setNewFotoFile(null);
      setNewFotoDesc("");
      setNewFotoPreco("");
      loadData();
    } catch (err: any) {
      addToast(err.message, "error");
    }
  };

  if (authLoading || !user) return <PageLoader label="Autenticando..." />;

  return (
    <div className="min-h-screen bg-slate-900 selection:bg-brand-500/30">
      <Navbar cta={{ label: "Gerar Posts", href: "/dashboard" }} />

      <main className="section-pad mx-auto max-w-5xl py-12">
        <div className="mb-10 text-center md:mb-16">
          <h1 className="font-display text-4xl font-extrabold tracking-tight text-white md:text-5xl lg:text-6xl">
            Seu <span className="text-brand-400">Painel</span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-white/60 md:text-xl">
            Gerencie suas informações, edite sua marca e controle as fotos dos seus produtos.
          </p>
        </div>

        {loadingData ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-8 md:grid-cols-[250px_1fr] items-start">
            <aside className="glass-panel flex flex-col gap-2 p-4">
              <button
                onClick={() => setActiveTab("fotos")}
                className={`rounded-lg px-4 py-3 text-left font-semibold transition-colors ${
                  activeTab === "fotos" ? "bg-brand-600 text-white" : "text-white/60 hover:bg-white/5"
                }`}
              >
                Catálogo de Fotos
              </button>
              <button
                onClick={() => setActiveTab("posts_salvos")}
                className={`rounded-lg px-4 py-3 text-left font-semibold transition-colors ${
                  activeTab === "posts_salvos" ? "bg-brand-600 text-white" : "text-white/60 hover:bg-white/5"
                }`}
              >
                Posts Salvos 🔖
              </button>
              <button
                onClick={() => setActiveTab("marca")}
                className={`rounded-lg px-4 py-3 text-left font-semibold transition-colors ${
                  activeTab === "marca" ? "bg-brand-600 text-white" : "text-white/60 hover:bg-white/5"
                }`}
              >
                Configurações da Marca
              </button>
              <button
                onClick={() => setActiveTab("perfil")}
                className={`rounded-lg px-4 py-3 text-left font-semibold transition-colors ${
                  activeTab === "perfil" ? "bg-brand-600 text-white" : "text-white/60 hover:bg-white/5"
                }`}
              >
                Perfil do Usuário
              </button>
            </aside>

            <section className="glass-panel min-h-[400px] p-6 md:p-8">
              {activeTab === "perfil" && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                  <h2 className="text-2xl font-bold text-white">Perfil do Usuário</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="mb-2 block text-sm font-medium text-white/70">Email</label>
                      <input
                        type="text"
                        disabled
                        value={user.email}
                        className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white/50"
                      />
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-medium text-white/70">Nome Completo</label>
                      <input
                        type="text"
                        value={userName}
                        onChange={(e) => setUserName(e.target.value)}
                        placeholder="Seu nome"
                        className="w-full rounded-xl border border-white/20 bg-white/5 px-4 py-3 text-white focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      />
                    </div>
                    <button
                      onClick={handleSavePerfil}
                      className="rounded-xl bg-brand-600 px-6 py-3 font-bold text-white hover:bg-brand-500"
                    >
                      Salvar Perfil
                    </button>
                  </div>
                </motion.div>
              )}

              {activeTab === "marca" && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                  <h2 className="text-2xl font-bold text-white">Configurações da Marca</h2>
                  {!marca ? (
                    <p className="text-white/60">Você ainda não configurou uma marca.</p>
                  ) : (
                    <div className="grid gap-6">
                      <div className="flex flex-col sm:flex-row gap-6 items-center">
                        <div className="h-24 w-24 flex-shrink-0 overflow-hidden rounded-full border-2 border-white/20 bg-white/5">
                          {marca.url_logo ? (
                            <img src={marca.url_logo} alt="Logo" className="h-full w-full object-cover" />
                          ) : (
                            <div className="flex h-full w-full items-center justify-center text-white/30">Sem Logo</div>
                          )}
                        </div>
                        <div className="w-full">
                          <label className="mb-2 block text-sm font-medium text-white/70">Atualizar Logo</label>
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
                            className="w-full rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-white file:mr-4 file:rounded-full file:border-0 file:bg-brand-600 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-brand-500"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="mb-2 block text-sm font-medium text-white/70">Nome da Marca</label>
                        <input
                          type="text"
                          value={nomeMarca}
                          onChange={(e) => setNomeMarca(e.target.value)}
                          className="w-full rounded-xl border border-white/20 bg-white/5 px-4 py-3 text-white focus:border-brand-500 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="mb-2 block text-sm font-medium text-white/70">Nicho de Mercado</label>
                        <input
                          type="text"
                          value={nicho}
                          onChange={(e) => setNicho(e.target.value)}
                          className="w-full rounded-xl border border-white/20 bg-white/5 px-4 py-3 text-white focus:border-brand-500 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="mb-2 block text-sm font-medium text-white/70">Tom de Voz</label>
                        <input
                          type="text"
                          value={tomVoz}
                          onChange={(e) => setTomVoz(e.target.value)}
                          className="w-full rounded-xl border border-white/20 bg-white/5 px-4 py-3 text-white focus:border-brand-500 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="mb-2 block text-sm font-medium text-white/70">Descrição Adicional</label>
                        <textarea
                          value={descricao}
                          onChange={(e) => setDescricao(e.target.value)}
                          className="min-h-[100px] w-full rounded-xl border border-white/20 bg-white/5 px-4 py-3 text-white focus:border-brand-500 focus:outline-none"
                        />
                      </div>
                      <button
                        onClick={handleSaveMarca}
                        className="w-full rounded-xl bg-brand-600 px-6 py-4 font-bold text-white hover:bg-brand-500"
                      >
                        Salvar Marca
                      </button>
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === "fotos" && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                    <h2 className="text-2xl font-bold text-white">Catálogo de Fotos</h2>
                  </div>

                  <div className="rounded-xl border border-white/10 bg-white/5 p-6">
                    <h3 className="mb-4 text-lg font-semibold text-white">Enviar Nova Foto</h3>
                    <div className="grid gap-4 md:grid-cols-[1fr_2fr_1fr_auto] items-end">
                      <div>
                        <label className="mb-2 block text-sm text-white/70">Arquivo</label>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => setNewFotoFile(e.target.files?.[0] || null)}
                          className="w-full rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-white file:hidden"
                        />
                      </div>
                      <div>
                        <label className="mb-2 block text-sm text-white/70">Descrição (O que é?)</label>
                        <input
                          type="text"
                          placeholder="Ex: Tênis Nike Branco"
                          value={newFotoDesc}
                          onChange={(e) => setNewFotoDesc(e.target.value)}
                          className="w-full rounded-xl border border-white/20 bg-white/10 px-4 py-2.5 text-white"
                        />
                      </div>
                      <div>
                        <label className="mb-2 block text-sm text-white/70">Preço</label>
                        <input
                          type="text"
                          placeholder="R$ 99,90"
                          value={newFotoPreco}
                          onChange={(e) => setNewFotoPreco(e.target.value)}
                          className="w-full rounded-xl border border-white/20 bg-white/10 px-4 py-2.5 text-white"
                        />
                      </div>
                      <button
                        onClick={handleUploadFoto}
                        className="rounded-xl bg-brand-600 px-6 py-2.5 font-bold text-white hover:bg-brand-500"
                      >
                        Enviar
                      </button>
                    </div>
                  </div>

                  {produtos.length === 0 ? (
                    <p className="text-center text-white/60 py-10">Você ainda não tem fotos cadastradas.</p>
                  ) : (
                    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3">
                      {produtos.map((p, idx) => (
                        <div key={p.id} className="group relative flex flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/5">
                          <div className="aspect-square w-full overflow-hidden">
                            <img src={p.url_imagem} alt="Produto" className="h-full w-full object-cover transition-transform group-hover:scale-105" />
                          </div>
                          <div className="flex flex-col gap-3 p-4">
                            <input
                              type="text"
                              value={p.texto_base}
                              onChange={(e) => {
                                const newP = [...produtos];
                                newP[idx].texto_base = e.target.value;
                                setProdutos(newP);
                              }}
                              className="w-full rounded-lg bg-white/10 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                              placeholder="Descrição"
                            />
                            <input
                              type="text"
                              value={p.preco || ""}
                              onChange={(e) => {
                                const newP = [...produtos];
                                newP[idx].preco = e.target.value;
                                setProdutos(newP);
                              }}
                              className="w-full rounded-lg bg-white/10 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                              placeholder="Preço (Opcional)"
                            />
                            <div className="mt-2 flex gap-2">
                              <button
                                onClick={() => handleSaveProduto(p)}
                                className="flex-1 rounded-lg bg-white/10 py-2 text-sm font-semibold text-white hover:bg-white/20"
                              >
                                Salvar
                              </button>
                              <button
                                onClick={() => handleDeleteProduto(p.id)}
                                className="rounded-lg bg-red-500/20 px-4 py-2 text-sm font-semibold text-red-400 hover:bg-red-500/40"
                              >
                                Excluir
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === "posts_salvos" && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                  <h2 className="text-2xl font-bold text-white">Posts Salvos 🔖</h2>
                  
                  {postsSalvos.length === 0 ? (
                    <p className="text-center text-white/60 py-10">Você ainda não tem nenhum post salvo no histórico.</p>
                  ) : (
                    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3">
                      {postsSalvos.map((p) => {
                        const isExpanded = !!expandedPosts[p.id];
                        return (
                          <div key={p.id} className="flex flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/5 h-full">
                            {p.imagem_url && (
                              <div className="relative aspect-square w-full overflow-hidden bg-slate-950">
                                <img src={p.imagem_url} alt={p.titulo_interno} className="h-full w-full object-cover" />
                                <span className="absolute left-3 top-3 rounded-full bg-brand-600/80 px-3 py-1 text-xs font-semibold text-white backdrop-blur">
                                  {p.imagem_disponivel ? "✨ IA" : "📷 Foto"}
                                </span>
                              </div>
                            )}
                            <div className="flex flex-1 flex-col justify-between p-4 gap-4">
                              <div className="space-y-2">
                                <h3 className="text-lg font-bold text-white leading-snug">{p.titulo_interno}</h3>
                                <p className={`text-sm text-white/70 leading-relaxed whitespace-pre-wrap ${isExpanded ? "" : "line-clamp-4"}`}>{p.legenda_instagram}</p>
                                {p.legenda_instagram && p.legenda_instagram.length > 150 && (
                                  <button
                                    onClick={() => setExpandedPosts((prev) => ({ ...prev, [p.id]: !isExpanded }))}
                                    className="text-xs font-semibold text-brand-400 hover:text-brand-300 mt-1 block transition-colors"
                                  >
                                    {isExpanded ? "Ler menos" : "Ler mais"}
                                  </button>
                                )}
                                <div className="flex flex-wrap gap-1.5 pt-2">
                                  {p.hashtags.map((h) => (
                                    <span key={h} className="text-xs text-brand-300 font-semibold bg-brand-900/30 px-2 py-0.5 rounded-full">#{h}</span>
                                  ))}
                                </div>
                              </div>
                              <div className="mt-auto flex gap-2">
                                <button
                                  onClick={() => handleCopyLegendaSalva(p)}
                                  className="flex-1 rounded-lg bg-brand-600 py-2.5 text-sm font-bold text-white hover:bg-brand-500 transition-colors"
                                >
                                  {copiedPostId === p.id ? "✓ Copiado" : "📋 Copiar Legenda"}
                                </button>
                                <button
                                  onClick={() => handleDeletePostSalvo(p.id)}
                                  className="rounded-lg bg-red-500/20 px-3 py-2.5 text-sm font-semibold text-red-400 hover:bg-red-500/40 transition-colors"
                                  title="Excluir do Histórico"
                                >
                                  🗑️
                                </button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </motion.div>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
