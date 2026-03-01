import os
import chromadb
from sentence_transformers import SentenceTransformer

# -----------------------------
# Persistent DB Setup
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chroma_db")

chroma_client = chromadb.PersistentClient(path=DB_PATH)

collection = chroma_client.get_or_create_collection(
    name="reqmind_knowledge"
)

# -----------------------------
# Embedding Model
# -----------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")


# -----------------------------
# Create Embeddings
# -----------------------------

def create_embeddings():

    if collection.count() > 0:
        print("⚠️ Embeddings already exist. Skipping creation.")
        return

    print("Loading from: knowledge_base")

    documents = []
    ids = []

    for filename in os.listdir("knowledge_base"):
        if filename.endswith(".txt"):
            with open(os.path.join("knowledge_base", filename), "r", encoding="utf-8") as f:
                content = f.read()
                documents.append(content)
                ids.append(filename)

    print("Files found:", ids)

    if not documents:
        print("⚠️ No documents found.")
        return

    embeddings = model.encode(documents).tolist()

    collection.add(
        documents=documents,
        embeddings=embeddings,
        ids=ids
    )

    print("✅ Documents embedded and stored in ChromaDB.")


# -----------------------------
# Retrieve Context
# -----------------------------

def retrieve_context(query):

    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=3
    )

    if not results["documents"] or not results["documents"][0]:
        return {"context": "", "similarity_score": 0}

    documents = results["documents"][0]
    distances = results["distances"][0]

    if distances:
        avg_distance = sum(distances) / len(distances)

        similarity_score = 1 - (avg_distance / 2)
        similarity_score = max(0, min(similarity_score, 1))
        similarity_score = round(similarity_score * 100, 2)
    else:
        similarity_score = 0

    context = "\n\n".join(documents)

    return {
        "context": context,
        "similarity_score": similarity_score
    }