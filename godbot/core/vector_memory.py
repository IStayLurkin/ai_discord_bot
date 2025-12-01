# GodBot core vector memory module
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    
    class VectorMemory:
        def __init__(self):
            self.db = chromadb.Client()
            self.collection = self.db.get_or_create_collection("memory")
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        
        def add(self, user, text):
            emb = self.embedder.encode([text])[0].tolist()
            self.collection.add(
                documents=[text],
                embeddings=[emb],
                ids=[user + "_" + str(hash(text))]
            )
        
        def search(self, query, n=5):
            emb = self.embedder.encode([query])[0].tolist()
            res = self.collection.query(query_embeddings=[emb], n_results=n)
            if res["documents"] and len(res["documents"]) > 0:
                return res["documents"][0]
            return []
except:
    # Fallback if ChromaDB not installed
    class VectorMemory:
        def __init__(self):
            pass
        def add(self, user, text):
            pass
        def search(self, query, n=5):
            return []

