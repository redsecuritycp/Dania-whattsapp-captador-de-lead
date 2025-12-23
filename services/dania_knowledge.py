"""
Búsqueda de info DANIA/Fortia desde hello.dania.ai
Reemplaza Tool_Milvus_DANIA de n8n
"""
import logging
import httpx
import os
from typing import Optional, Dict

logger = logging.getLogger(__name__)

JINA_API_KEY = os.environ.get("JINA_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

DANIA_PAGES = [
    "https://hello.dania.ai",
    "https://hello.dania.ai/servicios",
    "https://hello.dania.ai/nosotros",
    "https://hello.dania.ai/contacto",
    "https://hello.dania.ai/precios",
]

_dania_cache: Dict[str, str] = {}


async def fetch_dania_page_jina(url: str) -> Optional[str]:
    if not JINA_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"https://r.jina.ai/{url}", headers={"Authorization": f"Bearer {JINA_API_KEY}", "Accept": "text/plain"})
            if response.status_code == 200:
                return response.text[:15000]
        return None
    except:
        return None


async def search_dania_tavily(query: str) -> Optional[str]:
    if not TAVILY_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={"api_key": TAVILY_API_KEY, "query": f"site:hello.dania.ai {query}", "search_depth": "advanced", "include_answer": True, "include_raw_content": True, "max_results": 5}
            )
            if response.status_code == 200:
                data = response.json()
                parts = []
                if data.get("answer"):
                    parts.append(f"Resumen: {data['answer']}")
                for r in data.get("results", []):
                    if "dania" in r.get("url", "").lower():
                        parts.append(f"\n{r.get('title', '')}:\n{(r.get('raw_content') or r.get('content', ''))[:2000]}")
                if parts:
                    return "\n".join(parts)[:15000]
        return None
    except:
        return None


async def get_dania_knowledge_base() -> str:
    global _dania_cache
    if _dania_cache:
        return "\n\n".join(_dania_cache.values())
    all_content = []
    for url in DANIA_PAGES:
        content = await fetch_dania_page_jina(url)
        if content:
            _dania_cache[url] = content
            all_content.append(f"=== {url} ===\n{content}")
    return "\n\n".join(all_content) if all_content else ""


async def generate_dania_response(query: str, context: str) -> str:
    if not OPENAI_API_KEY or not context:
        return "No encontré información sobre eso en la documentación de Dania."
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": "Sos un asistente experto en DANIA y Fortia. Respondé SOLO con información del contexto. Usá voseo argentino. NO inventes."},
                        {"role": "user", "content": f"CONTEXTO:\n{context[:12000]}\n\nPREGUNTA:\n{query}"}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                }
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        return "Hubo un error al procesar tu consulta sobre Dania."
    except:
        return "Hubo un error al procesar tu consulta sobre Dania."


async def buscar_info_dania(query: str) -> Dict:
    logger.info(f"[DANIA] Buscando: {query}")
    try:
        tavily_content = await search_dania_tavily(query)
        if not tavily_content or len(tavily_content) < 200:
            jina_content = await get_dania_knowledge_base()
            context = jina_content if jina_content else tavily_content
        else:
            context = tavily_content
        if not context:
            return {"response": "No pude acceder a la información de Dania.", "source": "error", "query": query}
        response = await generate_dania_response(query, context)
        return {"response": response, "source": "hello.dania.ai", "query": query}
    except Exception as e:
        return {"response": "Hubo un error buscando información de Dania.", "source": "error", "query": query, "error": str(e)}



