
import httpx
import json

API_URL = "http://localhost:8000/api/v1"

def check_health():
    print("Checking API Health...")
    try:
        r = httpx.get(f"http://localhost:8000/health")
        print(f"Health Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"Health Check Failed: {e}")

    print("\nChecking Components...")
    try:
        r = httpx.get(f"{API_URL}/components")
        data = r.json().get("data", {})
        components = data.get("items", [])
        print(f"Found {len(components)} components")
        comp_ids = {c['id']: c['name'] for c in components}
        for cid, name in comp_ids.items():
            print(f"  - {name}: {cid}")
    except Exception as e:
        print(f"Components Check Failed: {e}")
        return

    print("\nChecking Issues...")
    try:
        r = httpx.get(f"{API_URL}/issues?limit=100")
        data = r.json().get("data", {})
        issues = data.get("items", [])
        pagination = data.get("pagination", {})
        print(f"Found {len(issues)} issues (Total in DB: {pagination.get('total')})")
        
        if issues:
            first = issues[0]
            print(f"First issue: {first['title']} (ID: {first['id']}, Status: {first['status']}, Component: {first['component_id']})")
            
            missing_comps = 0
            for i in issues:
                if i['component_id'] not in comp_ids:
                    missing_comps += 1
            
            if missing_comps > 0:
                print(f"WARNING: {missing_comps} issues have component_id not found in components list!")
            else:
                print("All issues have valid component_ids.")
                
            status_counts = {}
            for i in issues:
                s = i['status']
                status_counts[s] = status_counts.get(s, 0) + 1
            print(f"Status distribution: {status_counts}")
            
    except Exception as e:
        print(f"Issues Check Failed: {e}")

if __name__ == "__main__":
    check_health()
