import httpx, time, sys

API = 'http://localhost:8888'

# 1. Create component
r = httpx.post(f'{API}/api/v1/components', json={'name': 'Blog Platform', 'project': 'my-project', 'description': 'Blog platform component', 'labels': ['blog']}, timeout=10)
comp = r.json().get('data', {})
cid = comp.get('id', '')
print(f'Component: {str(cid)[:8]} ({r.status_code})', flush=True)

# 2. Create 50 issues
created = []
for i in range(1, 51):
    payload = {'title': f'Blog issue {i}', 'description': f'Issue #{i}', 'priority': 'MEDIUM', 'component_id': cid, 'labels': ['blog']}
    for attempt in range(3):
        r = httpx.post(f'{API}/api/v1/issues', json=payload, timeout=10)
        if r.status_code in (200, 201):
            iid = r.json().get('data', {}).get('id', '')
            created.append(iid)
            break
        elif r.status_code == 429:
            print(f'  429 on {i}, retrying...', flush=True)
            time.sleep(3)
    else:
        print(f'  FAIL {i}', flush=True)
    if i % 10 == 0:
        print(f'  {i}/50 created', flush=True)
    time.sleep(0.3)
print(f'Issues: {len(created)}/50', flush=True)

# 3. Create 5 linear deps
for i in range(5):
    payload = {'depends_on_id': created[i+1]}
    r = httpx.post(f'{API}/api/v1/issues/{created[i]}/dependencies', json=payload, timeout=10)
    print(f'  Dep {i+1}: {r.status_code}', flush=True)

# 4. Circular dep test
payload = {'depends_on_id': created[0]}
r = httpx.post(f'{API}/api/v1/issues/{created[4]}/dependencies', json=payload, timeout=10)
print(f'Circular: {r.status_code} (expect 409)', flush=True)

# 5. issue list performance
t0 = time.time()
r = httpx.get(f'{API}/api/v1/issues?limit=50', timeout=30)
items = r.json().get('data', {}).get('items', [])
t = time.time() - t0
print(f'List 50 issues: {t:.1f}s ({len(items)} items)', flush=True)

print('DONE', flush=True)
