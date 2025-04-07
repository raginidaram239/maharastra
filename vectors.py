
import os
import faiss
import pickle
import numpy as np
import openai
import time
import fitz  # PyMuPDF
from dotenv import load_dotenv
import tiktoken


load_dotenv()


AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_DEPLOYMENT_EMBEDDINGS = os.getenv("AZURE_DEPLOYMENT_EMBEDDINGS")


FAISS_INDEX_PATH = "faiss_index.bin"
CHUNKS_FILE_PATH = "chunks.pkl"
EMBEDDINGS_FILE_PATH = "embeddings.pkl"
LOCAL_PDF_FILE_PATH = "input.pdf"

def setup_openai():
    openai.api_type = "azure"
    openai.api_base = AZURE_OPENAI_ENDPOINT
    openai.api_version = AZURE_OPENAI_API_VERSION
    openai.api_key = AZURE_OPENAI_API_KEY

def extract_text_blocks_by_headings(file_path):
    print(">> Extracting structured text from PDF...")
    try:
        doc = fitz.open(file_path)
        all_chunks = []
        current_chunk = ""

        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                block_text = ""
                max_font_size = 0

                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"].strip() + " "
                        max_font_size = max(max_font_size, span["size"])

                block_text = block_text.strip()

                
                if max_font_size > 12 and block_text and len(block_text.split()) < 15:
                    if current_chunk:
                        all_chunks.append(current_chunk.strip())
                    current_chunk = block_text + "\n"
                else:
                    current_chunk += block_text + " "

        if current_chunk:
            all_chunks.append(current_chunk.strip())

        return all_chunks
    except Exception as e:
        print(f"!! Error parsing PDF blocks: {e}")
        return []

def refine_chunks_with_token_limit(chunks, max_tokens=500, overlap=100):
    print(">> Refining chunks by token length...")
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    final_chunks = []
    for chunk in chunks:
        words = chunk.split()
        i = 0
        while i < len(words):
            sub_chunk_words = words[i:i + max_tokens]
            sub_text = ' '.join(sub_chunk_words)
            tokens = encoding.encode(sub_text)
            while len(tokens) > max_tokens:
                sub_chunk_words = sub_chunk_words[:-1]
                sub_text = ' '.join(sub_chunk_words)
                tokens = encoding.encode(sub_text)
            final_chunks.append(sub_text)
            i += max_tokens - overlap
    return final_chunks

def generate_embeddings(chunks, batch_size=10):
    print(">> Generating embeddings...")
    setup_openai()
    embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        try:
            response = openai.Embedding.create(
                deployment_id=AZURE_DEPLOYMENT_EMBEDDINGS,
                input=batch
            )
            batch_embeddings = [item["embedding"] for item in response["data"]]
            embeddings.extend(batch_embeddings)
            print(f"✓ Processed batch {i // batch_size + 1}")
            time.sleep(1)
        except Exception as e:
            print(f"!! Embedding error on batch {i // batch_size + 1}: {e}")
            time.sleep(10)
    return embeddings if embeddings else None

def save_faiss_index(chunks, embeddings):
    if not embeddings:
        print("!! No embeddings generated, skipping index save.")
        return
    try:
        embeddings_np = np.array(embeddings, dtype=np.float32)
        index = faiss.IndexFlatL2(embeddings_np.shape[1])
        index.add(embeddings_np)
        faiss.write_index(index, FAISS_INDEX_PATH)
        print(f"✓ FAISS index saved: {FAISS_INDEX_PATH}")
    except Exception as e:
        print(f"!! Failed to save FAISS index: {e}")
    try:
        with open(CHUNKS_FILE_PATH, "wb") as f:
            pickle.dump(chunks, f)
        print(f"✓ Chunks saved: {CHUNKS_FILE_PATH}")
    except Exception as e:
        print(f"!! Failed to save chunks: {e}")
    try:
        with open(EMBEDDINGS_FILE_PATH, "wb") as f:
            pickle.dump(embeddings, f)
        print(f"✓ Embeddings saved: {EMBEDDINGS_FILE_PATH}")
    except Exception as e:
        print(f"!! Failed to save embeddings: {e}")

def main():
    raw_chunks = extract_text_blocks_by_headings(LOCAL_PDF_FILE_PATH)
    if not raw_chunks:
        print("!! No content extracted from PDF.")
        return
    chunks = refine_chunks_with_token_limit(raw_chunks)
    print(f">> Total refined chunks: {len(chunks)}")
    embeddings = generate_embeddings(chunks)
    save_faiss_index(chunks, embeddings)
    print("✓✓ Indexing completed successfully.")

if __name__ == "__main__":
    main()
