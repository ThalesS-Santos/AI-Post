import asyncio
import uuid
import datetime
import json
from pathlib import Path
from functools import lru_cache
from google import genai
from supabase import create_client, Client
from ..core.config import get_settings

# Arquivo do banco de dados local para catálogo de produtos local
DB_FILE = Path(__file__).resolve().parents[2] / "db.json"

def _load_local_db() -> dict:
    if not DB_FILE.exists():
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump({"embeddings_marca": []}, f)
        return {"embeddings_marca": []}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"embeddings_marca": []}

def _save_local_db(data: dict):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@lru_cache()
def _get_client() -> Client:
    s = get_settings()
    return create_client(s.SUPABASE_URL, s.SUPABASE_SERVICE_ROLE_KEY)


async def buscar_produtos_similares(
    cliente_id: str,
    vetor_query: list[float],
    limite: int = 3,
) -> list[dict]:
    # Mantido para compatibilidade, lê do catálogo local
    db = _load_local_db()
    records = db.get("embeddings_marca", [])
    
    filtered = [
        r for r in records 
        if r.get("cliente_id") == cliente_id and r.get("tipo") == "produto"
    ]
    return filtered[:limite]


async def salvar_embedding(
    cliente_id: str,
    tipo: str,
    texto_base: str,
    url_imagem: str,
    vetor: list[float],
    preco: str = "",
    metadata: dict = None,
) -> dict:
    if metadata is None:
        metadata = {}
    
    settings = get_settings()
    client_dev = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    # Se for cadastro de regra_marca, cria/atualiza no Supabase e cria o RAG no Gemini
    if tipo == "regra_marca":
        store_name = metadata.get("file_search_store_name")
        if not store_name:
            try:
                store_display_name = f"store-{cliente_id}"
                file_search_store = client_dev.file_search_stores.create(
                    config={
                        'display_name': store_display_name
                    }
                )
                store_name = file_search_store.name
                metadata["file_search_store_name"] = store_name
            except Exception as e:
                print(f"[Database] Erro ao criar File Search Store: {e}")
                
        if store_name:
            try:
                temp_file = Path(__file__).resolve().parents[2] / f"brand_rules_{cliente_id}.txt"
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(texto_base)
                
                operation = client_dev.file_search_stores.upload_to_file_search_store(
                    file=str(temp_file),
                    file_search_store_name=store_name,
                    config={'display_name': 'brand_rules.txt'}
                )
                while not operation.done:
                    await asyncio.sleep(1)
                    operation = client_dev.operations.get(operation)
                
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as e:
                print(f"[Database] Erro ao fazer upload de regras RAG: {e}")

        # Salva/Atualiza diretrizes da empresa no Supabase Live
        client = _get_client()
        existing = await buscar_regra_marca(cliente_id)
        if existing:
            res = await asyncio.to_thread(
                lambda: client.table("embeddings_marca")
                .update({
                    "texto_base": texto_base,
                    "url_imagem": url_imagem,
                    "metadata": metadata,
                    "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                })
                .eq("id", existing["id"])
                .execute()
            )
            return res.data[0]
        else:
            res = await asyncio.to_thread(
                lambda: client.table("embeddings_marca")
                .insert({
                    "cliente_id": cliente_id,
                    "tipo": "regra_marca",
                    "texto_base": texto_base,
                    "url_imagem": url_imagem,
                    "metadata": metadata
                })
                .execute()
            )
            return res.data[0]
            
    # Se for produto, as imagens e descrições NÃO vão para o Supabase. Salva localmente e sobe para o Gemini RAG.
    elif tipo == "produto":
        # 1. Sobe as mídias para a Store do Gemini RAG
        marca = await buscar_regra_marca(cliente_id)
        if marca:
            store_name = marca.get("metadata", {}).get("file_search_store_name")
            if store_name:
                try:
                    # Sobe o arquivo descritivo de texto
                    product_desc_file = Path(__file__).resolve().parents[2] / f"product_desc_{uuid.uuid4()}.txt"
                    with open(product_desc_file, "w", encoding="utf-8") as f:
                        f.write(f'[produto: "{texto_base}", preco: "{preco}"]')
                    
                    op_text = client_dev.file_search_stores.upload_to_file_search_store(
                        file=str(product_desc_file),
                        file_search_store_name=store_name,
                        config={'display_name': f"product_{texto_base[:20]}.txt"}
                    )
                    while not op_text.done:
                        await asyncio.sleep(1)
                        op_text = client_dev.operations.get(op_text)
                    
                    if product_desc_file.exists():
                        product_desc_file.unlink()
                        
                    # Sobe a imagem real do produto
                    if url_imagem:
                        try:
                            import httpx
                            async with httpx.AsyncClient(timeout=15.0) as http_client:
                                r = await http_client.get(url_imagem)
                                r.raise_for_status()
                                dados_img = r.content
                            
                            temp_img_file = Path(__file__).resolve().parents[2] / f"product_img_{uuid.uuid4()}.jpg"
                            with open(temp_img_file, "wb") as f:
                                f.write(dados_img)
                            
                            op_img = client_dev.file_search_stores.upload_to_file_search_store(
                                file=str(temp_img_file),
                                file_search_store_name=store_name,
                                config={'display_name': f"image_{texto_base[:20]}.jpg"}
                            )
                            while not op_img.done:
                                await asyncio.sleep(1)
                                op_img = client_dev.operations.get(op_img)
                                
                            if temp_img_file.exists():
                                temp_img_file.unlink()
                        except Exception as e:
                            print(f"[Database] Erro ao subir imagem do produto no RAG: {e}")
                except Exception as e:
                    print(f"[Database] Erro ao subir produto no RAG: {e}")

        # 2. Salva o catálogo de produtos apenas no db.json local
        db = _load_local_db()
        new_record = {
            "id": str(uuid.uuid4()),
            "cliente_id": cliente_id,
            "tipo": "produto",
            "texto_base": texto_base,
            "url_imagem": url_imagem,
            "preco": preco,
            "metadata": metadata or {},
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        db["embeddings_marca"].append(new_record)
        _save_local_db(db)
        return new_record


async def listar_produtos(cliente_id: str) -> list[dict]:
    # Retorna do catálogo local
    db = _load_local_db()
    records = db.get("embeddings_marca", [])
    filtered = [
        {
            "id": r["id"],
            "texto_base": r["texto_base"],
            "url_imagem": r["url_imagem"],
            "preco": r.get("preco", "")
        }
        for r in records
        if r.get("cliente_id") == cliente_id and r.get("tipo") == "produto"
    ]
    filtered.reverse()
    return filtered


async def buscar_produto_por_id(cliente_id: str, produto_id: str) -> dict | None:
    # Retorna do catálogo local
    db = _load_local_db()
    for r in db.get("embeddings_marca", []):
        if r.get("cliente_id") == cliente_id and r.get("id") == produto_id:
            return {
                "id": r["id"],
                "texto_base": r["texto_base"],
                "url_imagem": r["url_imagem"],
                "preco": r.get("preco", "")
            }
    return None


async def atualizar_produto(cliente_id: str, produto_id: str, texto_base: str, preco: str, vetor: list[float] | None = None) -> dict | None:
    # Atualiza no catálogo local
    db = _load_local_db()
    for r in db.get("embeddings_marca", []):
        if r.get("cliente_id") == cliente_id and r.get("id") == produto_id:
            r["texto_base"] = texto_base
            r["preco"] = preco
            r["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            _save_local_db(db)
            return r
    return None


async def deletar_produto(cliente_id: str, produto_id: str) -> bool:
    # Deleta do catálogo local
    db = _load_local_db()
    records = db.get("embeddings_marca", [])
    initial_len = len(records)
    
    # Remove o arquivo de imagem local associado
    for r in records:
        if r.get("cliente_id") == cliente_id and r.get("id") == produto_id:
            url_img = r.get("url_imagem", "")
            if url_img:
                filename = url_img.split("/static/uploads/")[-1]
                upload_dir = Path(__file__).resolve().parents[1] / "static" / "uploads"
                local_file_path = upload_dir / filename
                try:
                    if local_file_path.exists():
                        local_file_path.unlink()
                except Exception:
                    pass
            break
            
    db["embeddings_marca"] = [
        r for r in records
        if not (r.get("cliente_id") == cliente_id and r.get("id") == produto_id)
    ]
    
    if len(db["embeddings_marca"]) < initial_len:
        _save_local_db(db)
        return True
    return False


async def buscar_regra_marca(cliente_id: str) -> dict | None:
    # Regras de marca são lidas do Supabase Live
    client = _get_client()
    res = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .select("id, texto_base, url_imagem, metadata")
        .eq("cliente_id", cliente_id)
        .eq("tipo", "regra_marca")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    data = res.data or []
    return data[0] if data else None


async def atualizar_regra_marca(cliente_id: str, marca_id: str, texto_base: str, metadata: dict, vetor: list[float] | None = None) -> dict | None:
    # Atualiza as regras de marca no Gemini RAG Store
    store_name = metadata.get("file_search_store_name")
    if store_name:
        try:
            settings = get_settings()
            client_dev = genai.Client(api_key=settings.GEMINI_API_KEY)
            temp_file = Path(__file__).resolve().parents[2] / f"brand_rules_{cliente_id}.txt"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(texto_base)
            
            client_dev.file_search_stores.upload_to_file_search_store(
                file=str(temp_file),
                file_search_store_name=store_name,
                config={'display_name': 'brand_rules.txt'}
            )
        except Exception as e:
            print(f"[Database] Erro ao atualizar RAG de regras: {e}")

    # Atualiza as regras no Supabase Live
    client = _get_client()
    res = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .update({
            "texto_base": texto_base,
            "metadata": metadata,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
        .eq("id", marca_id)
        .eq("cliente_id", cliente_id)
        .execute()
    )
    data = res.data or []
    return data[0] if data else None


async def atualizar_logo_marca(cliente_id: str, url_logo: str) -> dict | None:
    # Atualiza a logo no Supabase Live
    marca = await buscar_regra_marca(cliente_id)
    if not marca:
        return None
    client = _get_client()
    res = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .update({
            "url_imagem": url_logo,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
        .eq("id", marca["id"])
        .execute()
    )
    data = res.data or []
    return data[0] if data else None


async def fazer_upload_storage(
    bucket: str,
    caminho: str,
    dados: bytes,
    content_type: str = "image/jpeg",
) -> str:
    # Salva as imagens localmente na pasta static/uploads/ (não poluímos o Storage do Supabase)
    upload_dir = Path(__file__).resolve().parents[1] / "static" / "uploads"
    safe_caminho = caminho.replace("/", "_")
    target_file = upload_dir / safe_caminho
    target_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(target_file, "wb") as f:
        f.write(dados)
        
    return f"http://localhost:8000/static/uploads/{safe_caminho}"


async def garantir_rag_store(cliente_id: str) -> str:
    # Busca se já tem alguma regra de marca cadastrada no Supabase Live
    marca = await buscar_regra_marca(cliente_id)
    if marca:
        store_name = marca.get("metadata", {}).get("file_search_store_name")
        if store_name:
            return store_name
            
    # Se não tem store_name, vamos criar a RAG store
    settings = get_settings()
    client_dev = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    store_name = None
    try:
        store_display_name = f"store-{cliente_id}"
        file_search_store = client_dev.file_search_stores.create(
            config={
                'display_name': store_display_name
            }
        )
        store_name = file_search_store.name
    except Exception as e:
        print(f"[Database] Erro ao criar File Search Store no login/status: {e}")
        store_name = f"fileSearchStores/mock-store-{cliente_id}"
        
    if marca:
        # Atualiza a marca existente no Supabase com o store_name
        meta = marca.get("metadata") or {}
        meta["file_search_store_name"] = store_name
        
        client = _get_client()
        await asyncio.to_thread(
            lambda: client.table("embeddings_marca")
            .update({
                "metadata": meta,
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })
            .eq("id", marca["id"])
            .execute()
        )
    else:
        # Cria um registro de marca placeholder contendo apenas o store_name no metadata no Supabase
        client = _get_client()
        await asyncio.to_thread(
            lambda: client.table("embeddings_marca")
            .insert({
                "cliente_id": cliente_id,
                "tipo": "regra_marca",
                "texto_base": "",
                "url_imagem": "",
                "vetor_embedding": None,
                "preco": "",
                "metadata": {"file_search_store_name": store_name}
            })
            .execute()
        )
        
    return store_name
