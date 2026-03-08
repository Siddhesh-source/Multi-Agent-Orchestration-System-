from memory.chroma_store import chroma_store

# Get all memories
all_data = chroma_store.collection.get(
    limit=20,
    include=["documents", "metadatas"]
)

print(f'Total memories in ChromaDB: {chroma_store.count()}\n')

for i, doc_id in enumerate(all_data['ids']):
    meta = all_data['metadatas'][i]
    doc = all_data['documents'][i][:80]
    
    print(f'Memory {i+1}:')
    print(f'  ID: {doc_id}')
    print(f'  task_id in metadata: {meta.get("task_id", "MISSING")}')
    print(f'  task_description: {meta.get("task_description", "MISSING")[:50]}...')
    print(f'  Document: {doc}...')
    print()
