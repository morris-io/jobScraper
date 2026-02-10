import chromadb
from chromadb.utils import embedding_functions
import os

client = chromadb.PersistentClient(path="./job_search_db")

emb_fn = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="michael_job_matches",
    embedding_function=emb_fn
)

def add_job(job_id, title, company, description):
    collection.add(
        documents=[description],
        metadatas=[{"title": title, "company": company}],
        ids=[job_id]
    )
    print(f"Added {title} at {company} to the database.")

def get_matches(resume_text, n_results=5):
    results = collection.query(
        query_texts=[resume_text],
        n_results=n_results
    )
    return results

if __name__ == "__main__":
    print("Vector Database Ready.")