# download embedding models 
from sentence_transformers import SentenceTransformer

print("Downloading BAAI/bge-m3...")

model = SentenceTransformer('BAAI/bge-m3')

print("Download complete!")