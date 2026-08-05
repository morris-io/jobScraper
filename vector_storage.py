import chromadb
from chromadb.utils import embedding_functions
import os

client = chromadb.PersistentClient(path="./job_search_db")

emb_fn = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="michael_job_matches",
    embedding_function=emb_fn
)

# FIXED: Added 'url' parameter and changed .add() to .upsert()
def add_job(job_id, title, company, description, url):
    collection.upsert(
        documents=[description],
        metadatas=[{"title": title, "company": company, "url": url}],
        ids=[job_id]
    )
    print(f"Saved: {title}")

def get_matches(resume_text, n_results=5):
    results = collection.query(
        query_texts=[resume_text],
        n_results=n_results
    )
    return results

if __name__ == "__main__":
    print("Vector Database Ready.")