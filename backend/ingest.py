import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    """Splits text into chunks of ~chunk_size characters with overlap."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + p
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # Start new chunk with overlap
            current_chunk = current_chunk[-overlap:] + "\n\n" + p if current_chunk else p

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def ingest():
    print("==================================================")
    print("LaunchPath Seed Data Ingestion Script")
    print("==================================================")

    if not DATA_DIR.exists():
        print(f"Error: Data directory not found at {DATA_DIR}")
        return

    files = list(DATA_DIR.glob("*.txt*"))
    print(f"Found {len(files)} seed files in {DATA_DIR}")

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[Notice] Supabase URL or Key missing in .env.")
        print("[Notice] Seed files will be processed locally by retrieval.py fallback mode.")
        print(f"Successfully validated {len(files)} seed files.")
        return

    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Clearing existing records in 'documents' table (DELETE FROM documents;)...")
        try:
            supabase.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            print("Successfully cleared 'documents' table.")
        except Exception as del_err:
            print(f"Warning clearing documents table: {del_err}")
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
        return

    embeddings_model = None
    if OPENAI_API_KEY:
        try:
            from langchain_openai import OpenAIEmbeddings
            embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
            print("Using OpenAI text-embedding-3-small embeddings model.")
        except Exception as e:
            print(f"Could not initialize OpenAI embeddings: {e}")

    total_chunks = 0
    for file_path in files:
        filename = file_path.name
        clean_name = re.sub(r'(\.txt)+$', '', filename)
        parts = clean_name.split("__")
        domain = parts[0].strip().lower() if len(parts) > 1 else "general"
        source_title = parts[1].replace("_", " ").title() if len(parts) > 1 else clean_name.replace("_", " ").title()

        content = file_path.read_text(encoding="utf-8").strip()
        chunks = chunk_text(content, chunk_size=500, overlap=50)

        print(f"Processing '{filename}' -> domain: '{domain}', title: '{source_title}', chunks: {len(chunks)}")

        for chunk in chunks:
            vector_data = None
            if embeddings_model:
                try:
                    vector_data = embeddings_model.embed_query(chunk)
                except Exception as ex:
                    print(f"  Warning embedding chunk: {ex}")

            payload = {
                "content": chunk,
                "domain": domain,
                "category": domain,
                "source_title": source_title,
                "source_url": None,
                "embedding": vector_data
            }

            try:
                supabase.table("documents").insert(payload).execute()
                total_chunks += 1
            except Exception as e:
                print(f"  Error inserting chunk to Supabase: {e}")

    print("==================================================")
    print(f"Ingestion finished! Inserted {total_chunks} chunks across {len(files)} files.")
    print("==================================================")


if __name__ == "__main__":
    ingest()
