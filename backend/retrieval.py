# # import os
# # import re
# # from pathlib import Path
# # from typing import List, Dict, Any, Optional
# # from dotenv import load_dotenv

# # load_dotenv()

# # MIN_RELEVANCE_THRESHOLD = 0.5
# # DATA_DIR = Path(__file__).parent / "data"

# # SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
# # SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# # supabase_client = None
# # if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL.startswith("http"):
# #     try:
# #         from supabase import create_client
# #         supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
# #     except Exception as e:
# #         print(f"[Retrieval] Supabase init warning: {e}. Falling back to local search.")
# #         supabase_client = None


# # def load_local_knowledge_base() -> List[Dict[str, Any]]:
# #     """
# #     Loads all document chunks from backend/data/ for offline / local fallback search.
# #     Parses domain and source_title from filename patterns like 'domain__title.txt' or 'domain__title.txt.txt'.
# #     """
# #     chunks = []
# #     if not DATA_DIR.exists():
# #         return chunks

# #     for file_path in DATA_DIR.glob("*.txt*"):
# #         filename = file_path.name
# #         # Remove trailing .txt or .txt.txt
# #         clean_name = re.sub(r'(\.txt)+$', '', filename)
# #         parts = clean_name.split("__")
# #         domain = parts[0].strip().lower() if len(parts) > 1 else "general"
# #         raw_title = parts[1].replace("_", " ").title() if len(parts) > 1 else clean_name.replace("_", " ").title()
        
# #         try:
# #             content = file_path.read_text(encoding="utf-8").strip()
# #             if not content:
# #                 continue
            
# #             # Simple chunking: 500 characters / paragraphs
# #             paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
# #             for p in paragraphs:
# #                 chunks.append({
# #                     "content": p,
# #                     "domain": domain,
# #                     "source_title": raw_title,
# #                     "filename": filename
# #                 })
# #         except Exception as e:
# #             print(f"[Retrieval] Error reading {filename}: {e}")

# #     return chunks


# # LOCAL_CHUNKS = load_local_knowledge_base()


# # def calculate_local_similarity(query: str, chunk_text: str, domain: Optional[str], chunk_domain: str) -> float:
# #     """
# #     Calculates a hybrid keyword relevance score between query and chunk_text.
# #     """
# #     query_terms = set(re.findall(r'\w+', query.lower()))
# #     if not query_terms:
# #         return 0.0

# #     text_lower = chunk_text.lower()
# #     matches = sum(1 for term in query_terms if term in text_lower)
    
# #     score = matches / max(len(query_terms), 1)

# #     # Domain bonus
# #     if domain and domain.lower() == chunk_domain.lower():
# #         score *= 1.25

# #     return min(score, 1.0)


# # def search(query: str, domain: Optional[str] = None, k: int = 5) -> List[Dict[str, Any]]:
# #     """
# #     Performs hybrid search for a query with optional domain filtering.
# #     Returns list of dicts: [{'content': str, 'domain': str, 'source_title': str, 'score': float}]
# #     """
# #     query = query.strip()
# #     if not query:
# #         return []

# #     # 1. Try Supabase hybrid search if client available
# #     if supabase_client:
# #         try:
# #             # Generate query embedding if OpenAI available
# #             embedding = None
# #             openai_key = os.getenv("OPENAI_API_KEY", "").strip()
# #             if openai_key:
# #                 from langchain_openai import OpenAIEmbeddings
# #                 embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
# #                 embedding = embeddings_model.embed_query(query)
            
# #             if embedding:
# #                 res = supabase_client.rpc(
# #                     "hybrid_search",
# #                     {
# #                         "query_text": query,
# #                         "query_embedding": embedding,
# #                         "match_count": k,
# #                         "filter_domain": domain if domain and domain != "all" else None
# #                     }
# #                 ).execute()
                
# #                 if res and res.data:
# #                     results = []
# #                     for row in res.data:
# #                         score = float(row.get("rrf_score", row.get("similarity", 0.0)))
# #                         results.append({
# #                             "content": row.get("content", ""),
# #                             "domain": row.get("domain", ""),
# #                             "source_title": row.get("source_title", "General Advice"),
# #                             "score": score
# #                         })
# #                     return results
# #         except Exception as e:
# #             print(f"[Retrieval] Supabase hybrid search failed: {e}. Using local fallback search.")

# #     # 2. Local Fallback Search
# #     scored_chunks = []
# #     for chunk in LOCAL_CHUNKS:
# #         if domain and domain != "all" and chunk["domain"] != domain.lower():
# #             continue
        
# #         sim = calculate_local_similarity(query, chunk["content"], domain, chunk["domain"])
# #         if sim > 0.05:  # filter negligible overlaps
# #             scored_chunks.append({
# #                 "content": chunk["content"],
# #                 "domain": chunk["domain"],
# #                 "source_title": chunk["source_title"],
# #                 "score": sim
# #             })

# #     scored_chunks.sort(key=lambda x: x["score"], reverse=True)
# #     return scored_chunks[:k]


# import os
# import re
# from pathlib import Path
# from typing import List, Dict, Any, Optional
# from dotenv import load_dotenv

# load_dotenv()

# MIN_RELEVANCE_THRESHOLD = 0.35  # tune after testing — was unused before
# LOCAL_FALLBACK_MIN_SCORE = 0.15  # was 0.05, too permissive
# DATA_DIR = Path(__file__).parent / "data"

# SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
# SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# # --- domain auto-detection, used when caller doesn't already know the domain ---
# DOMAIN_KEYWORDS = {
#     "startups": ["startup", "founder", "funding", "pitch", "incubator", "prototype", "vc", "investor"],
#     "freelancing": ["freelanc", "client", "gig", "hourly", "upwork", "fiverr"],
#     "schemes": ["scheme", "dpiit", "government", "grant", "registration", "udyam", "msme"],
#     "local_business": ["bakery", "shop", "local business", "retail", "cafe", "store"],
#     "roadmap": ["roadmap", "skill", "learn", "career path"],
#     "failures": ["failed", "failure", "shut down", "postmortem", "went wrong"],
# }

# def detect_domain(query: str) -> Optional[str]:
#     query_lower = query.lower()
#     for domain, keywords in DOMAIN_KEYWORDS.items():
#         if any(kw in query_lower for kw in keywords):
#             return domain
#     return None
# # --- end addition ---

# supabase_client = None
# if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL.startswith("http"):
#     try:
#         from supabase import create_client
#         supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
#     except Exception as e:
#         print(f"[Retrieval] Supabase init warning: {e}. Falling back to local search.")
#         supabase_client = None


# def load_local_knowledge_base() -> List[Dict[str, Any]]:
#     chunks = []
#     if not DATA_DIR.exists():
#         return chunks
#     for file_path in DATA_DIR.glob("*.txt*"):
#         filename = file_path.name
#         clean_name = re.sub(r'(\.txt)+$', '', filename)
#         parts = clean_name.split("__")
#         domain = parts[0].strip().lower() if len(parts) > 1 else "general"
#         raw_title = parts[1].replace("_", " ").title() if len(parts) > 1 else clean_name.replace("_", " ").title()
#         try:
#             content = file_path.read_text(encoding="utf-8").strip()
#             if not content:
#                 continue
#             paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
#             for p in paragraphs:
#                 chunks.append({
#                     "content": p,
#                     "domain": domain,
#                     "source_title": raw_title,
#                     "filename": filename
#                 })
#         except Exception as e:
#             print(f"[Retrieval] Error reading {filename}: {e}")
#     return chunks


# LOCAL_CHUNKS = load_local_knowledge_base()


# def calculate_local_similarity(query: str, chunk_text: str, domain: Optional[str], chunk_domain: str) -> float:
#     query_terms = set(re.findall(r'\w+', query.lower()))
#     if not query_terms:
#         return 0.0
#     text_lower = chunk_text.lower()
#     matches = sum(1 for term in query_terms if term in text_lower)
#     score = matches / max(len(query_terms), 1)
#     if domain and domain.lower() == chunk_domain.lower():
#         score *= 1.25
#     elif domain and domain.lower() != chunk_domain.lower():
#         score *= 0.3  # NEW: penalize cross-domain matches instead of ignoring domain mismatch
#     return min(score, 1.0)


# def search(query: str, domain: Optional[str] = None, k: int = 3) -> List[Dict[str, Any]]:
#     query = query.strip()
#     if not query:
#         return []

#     # NEW: auto-detect domain if caller didn't provide one
#     if domain is None:
#         domain = detect_domain(query)

#     results = []

#     if supabase_client:
#         try:
#             embedding = None
#             openai_key = os.getenv("OPENAI_API_KEY", "").strip()
#             if openai_key:
#                 from langchain_openai import OpenAIEmbeddings
#                 embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
#                 embedding = embeddings_model.embed_query(query)
#             if embedding:
#                 res = supabase_client.rpc(
#                     "hybrid_search",
#                     {
#                         "query_text": query,
#                         "query_embedding": embedding,
#                         "match_count": k,
#                         "filter_domain": domain if domain and domain != "all" else None
#                     }
#                 ).execute()
#                 if res and res.data:
#                     for row in res.data:
#                         score = float(row.get("rrf_score", row.get("similarity", 0.0)))
#                         results.append({
#                             "content": row.get("content", ""),
#                             "domain": row.get("domain", ""),
#                             "source_title": row.get("source_title", "General Advice"),
#                             "score": score
#                         })
#         except Exception as e:
#             print(f"[Retrieval] Supabase hybrid search failed: {e}. Using local fallback search.")

#     if not results:
#         scored_chunks = []
#         for chunk in LOCAL_CHUNKS:
#             if domain and domain != "all" and chunk["domain"] != domain.lower():
#                 continue
#             sim = calculate_local_similarity(query, chunk["content"], domain, chunk["domain"])
#             if sim > LOCAL_FALLBACK_MIN_SCORE:
#                 scored_chunks.append({
#                     "content": chunk["content"],
#                     "domain": chunk["domain"],
#                     "source_title": chunk["source_title"],
#                     "score": sim
#                 })
#         scored_chunks.sort(key=lambda x: x["score"], reverse=True)
#         results = scored_chunks[:k]

#     # NEW: the fix that was missing entirely — enforce the real cutoff
#     results = [r for r in results if r["score"] >= MIN_RELEVANCE_THRESHOLD]

#     return results



import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

MIN_RELEVANCE_THRESHOLD = 0.35
LOCAL_FALLBACK_MIN_SCORE = 0.15
DATA_DIR = Path(__file__).parent / "data"

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# --- domain auto-detection ---
DOMAIN_KEYWORDS = {
    "startups": ["startup", "founder", "funding", "pitch", "incubator",
                 "prototype", "vc", "investor", "tech product", "software product",
                 "chatbot", "customer support", "delivery", "logistics", "route"],
    "freelancing": ["freelanc", "client", "gig", "hourly", "upwork", "fiverr",
                     "web developer", "web development", "genai", "llm developer"],
    "schemes": ["scheme", "dpiit", "government", "grant", "registration", "samridh"],
}
ROLE_KEYWORDS = {
    "web_developer": ["web developer", "web development", "website", "frontend", "react", "next.js"],
    "genai_developer": ["genai", "llm developer", "ai developer", "chatbot developer", "rag"],
}

def detect_role(query: str) -> Optional[str]:
    query_lower = query.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            return role
    return None
def detect_domain(query: str) -> Optional[str]:
    query_lower = query.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            return domain
    return None
# --- end domain detection ---

supabase_client = None
if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL.startswith("http"):
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[Retrieval] Supabase init warning: {e}. Falling back to local search.")
        supabase_client = None


def load_local_knowledge_base() -> List[Dict[str, Any]]:
    chunks = []
    if not DATA_DIR.exists():
        return chunks
    for file_path in DATA_DIR.glob("*.txt*"):
        filename = file_path.name
        clean_name = re.sub(r'(\.txt)+$', '', filename)
        parts = clean_name.split("__")
        domain = parts[0].strip().lower() if len(parts) > 1 else "general"
        raw_title = parts[1].replace("_", " ").title() if len(parts) > 1 else clean_name.replace("_", " ").title()
        try:
            content = file_path.read_text(encoding="utf-8").strip()
            if not content:
                continue
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            for p in paragraphs:
                chunks.append({
                    "content": p,
                    "domain": domain,
                    "source_title": raw_title,
                    "filename": filename
                })
        except Exception as e:
            print(f"[Retrieval] Error reading {filename}: {e}")
    return chunks


LOCAL_CHUNKS = load_local_knowledge_base()


def calculate_local_similarity(query: str, chunk_text: str, domain: Optional[str], chunk_domain: str) -> float:
    query_terms = set(re.findall(r'\w+', query.lower()))
    if not query_terms:
        return 0.0
    text_lower = chunk_text.lower()
    matches = sum(1 for term in query_terms if term in text_lower)
    score = matches / max(len(query_terms), 1)
    if domain and domain.lower() == chunk_domain.lower():
        score *= 1.25
    elif domain and domain.lower() != chunk_domain.lower():
        score *= 0.3  # penalize cross-domain matches
    return min(score, 1.0)


def search(query: str, domain: Optional[str] = None, k: int = 3) -> List[Dict[str, Any]]:
    query = query.strip()
    if not query:
        return []

    if domain is None:
        domain = detect_domain(query)

    results = []

    if supabase_client:
        try:
            embedding = None
            openai_key = os.getenv("OPENAI_API_KEY", "").strip()
            if openai_key:
                from langchain_openai import OpenAIEmbeddings
                embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
                embedding = embeddings_model.embed_query(query)
            if embedding:
                res = supabase_client.rpc(
                    "hybrid_search",
                    {
                        "query_text": query,
                        "query_embedding": embedding,
                        "match_count": k,
                        "filter_domain": domain if domain and domain != "all" else None
                    }
                ).execute()
                if res and res.data:
                    for row in res.data:
                        score = float(row.get("rrf_score", row.get("similarity", 0.0)))
                        results.append({
                            "content": row.get("content", ""),
                            "domain": row.get("domain", ""),
                            "source_title": row.get("source_title", "General Advice"),
                            "score": score
                        })
        except Exception as e:
            print(f"[Retrieval] Supabase hybrid search failed: {e}. Using local fallback search.")

    if not results:
        scored_chunks = []
        for chunk in LOCAL_CHUNKS:
            if domain and domain != "all" and chunk["domain"] != domain.lower():
                continue
            sim = calculate_local_similarity(query, chunk["content"], domain, chunk["domain"])
            if sim > LOCAL_FALLBACK_MIN_SCORE:
                scored_chunks.append({
                    "content": chunk["content"],
                    "domain": chunk["domain"],
                    "source_title": chunk["source_title"],
                    "score": sim
                })
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        results = scored_chunks[:k]

    # enforce the relevance floor — this was missing before
    results = [r for r in results if r["score"] >= MIN_RELEVANCE_THRESHOLD]

    return results