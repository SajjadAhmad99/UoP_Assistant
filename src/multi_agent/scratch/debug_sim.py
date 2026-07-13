from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np

model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

q1 = "Who is the Vice Chancellor of University of Peshawar?"
q2 = "Who is the current VC of UoP?"

emb1 = np.array(model.embed_query(q1))
emb2 = np.array(model.embed_query(q2))

sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
print(f"Similarity: {sim}")
