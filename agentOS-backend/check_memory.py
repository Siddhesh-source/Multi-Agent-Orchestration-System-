from memory.chroma_store import chroma_store

print(f'Total memories: {chroma_store.count()}')
memories = chroma_store.get_all(50)
print('\nRecent memories:')
for m in memories[:10]:
    task_id = m.get('task_id', m.get('id', 'no-id'))
    desc = m.get('task_description', 'no-desc')[:60]
    print(f'  - {task_id}: {desc}...')
