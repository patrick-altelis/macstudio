from config import MAX_CHUNK_SIZE

def split_text(text):
    words = text.split()
    chunks = []
    current_chunk = []
    for word in words:
        current_chunk.append(word)
        if len(' '.join(current_chunk)) > MAX_CHUNK_SIZE:
            chunks.append(' '.join(current_chunk[:-1]))
            current_chunk = [word]
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks
