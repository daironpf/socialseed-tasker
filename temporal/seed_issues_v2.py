import httpx
import random
import time

API_URL = "http://localhost:8000/api/v1"
HEADERS = {"X-API-Key": "test-token"}

PROJECTS = ["ecommerce-store", "demo-platform"]

COMPONENTS_DATA = [
    {"name": "Frontend", "project": "ecommerce-store"},
    {"name": "Backend", "project": "ecommerce-store"},
    {"name": "Database", "project": "ecommerce-store"},
    {"name": "Auth", "project": "ecommerce-store"},
    {"name": "API Gateway", "project": "demo-platform"},
    {"name": "Order Service", "project": "demo-platform"},
]

ISSUES_DATA = [
    # Auth (ecommerce-store)
    {"title": "Implement JWT logic", "comp": "Auth", "priority": "CRITICAL"},
    {"title": "Setup OAuth2 with Google", "comp": "Auth", "priority": "HIGH"},
    {"title": "User registration endpoint", "comp": "Auth", "priority": "CRITICAL"},
    {"title": "Password reset flow", "comp": "Auth", "priority": "MEDIUM"},
    {"title": "Email verification service", "comp": "Auth", "priority": "MEDIUM"},
    
    # Database (ecommerce-store)
    {"title": "Design user schema", "comp": "Database", "priority": "CRITICAL"},
    {"title": "Design product schema", "comp": "Database", "priority": "CRITICAL"},
    {"title": "Design order schema", "comp": "Database", "priority": "CRITICAL"},
    {"title": "Setup database migrations", "comp": "Database", "priority": "HIGH"},
    {"title": "Optimize search indexes", "comp": "Database", "priority": "MEDIUM"},
    
    # Backend (ecommerce-store)
    {"title": "Product CRUD API", "comp": "Backend", "priority": "HIGH"},
    {"title": "Search product endpoint", "comp": "Backend", "priority": "HIGH"},
    {"title": "Cart management logic", "comp": "Backend", "priority": "HIGH"},
    {"title": "Checkout process API", "comp": "Backend", "priority": "CRITICAL"},
    {"title": "Payment gateway integration", "comp": "Backend", "priority": "CRITICAL"},
    
    # Frontend (ecommerce-store)
    {"title": "Setup React project", "comp": "Frontend", "priority": "HIGH"},
    {"title": "Home page layout", "comp": "Frontend", "priority": "MEDIUM"},
    {"title": "Product listing page", "comp": "Frontend", "priority": "HIGH"},
    {"title": "Shopping cart UI", "comp": "Frontend", "priority": "HIGH"},
    {"title": "Checkout form", "comp": "Frontend", "priority": "CRITICAL"},
    
    # API Gateway (demo-platform)
    {"title": "Rate limiting implementation", "comp": "API Gateway", "priority": "HIGH"},
    {"title": "CORS configuration", "comp": "API Gateway", "priority": "MEDIUM"},
    {"title": "Request validation middleware", "comp": "API Gateway", "priority": "MEDIUM"},
    
    # Order Service (demo-platform)
    {"title": "Order fulfillment logic", "comp": "Order Service", "priority": "CRITICAL"},
    {"title": "Order status tracking", "comp": "Order Service", "priority": "HIGH"},
    {"title": "PDF invoice generation", "comp": "Order Service", "priority": "LOW"}
]

def main():
    component_map = {}
    print("Creating components...")
    for comp in COMPONENTS_DATA:
        res = httpx.post(f"{API_URL}/components", json=comp, headers=HEADERS)
        if res.status_code == 201:
            c_data = res.json()["data"]
            component_map[comp["name"]] = c_data["id"]
            print(f"Created component: {comp['name']} ({c_data['project']}) -> {c_data['id']}")
        else:
            print(f"Error creating component {comp['name']}: {res.text}")

    print("\nCreating issues...")
    issue_ids = []
    for item in ISSUES_DATA:
        if item["comp"] not in component_map:
            print(f"Skipping {item['title']} - component {item['comp']} not found")
            continue
            
        payload = {
            "title": item["title"],
            "description": f"Detailed task for {item['title']}",
            "priority": item["priority"],
            "component_id": component_map[item["comp"]],
            "labels": [item["comp"].lower(), "seed-v2"]
        }
        res = httpx.post(f"{API_URL}/issues", json=payload, headers=HEADERS)
        if res.status_code == 201:
            i_id = res.json()["data"]["id"]
            issue_ids.append(i_id)
            print(f"Created issue: {item['title']} -> {i_id}")
        else:
            print(f"Error creating issue {item['title']}: {res.text}")
        time.sleep(0.05)

    print("\nLinking dependencies...")
    # Add some logical dependencies to show in the graph
    # (Simplified for demonstration)
    if len(issue_ids) > 15:
        # Link some issues to simulate a graph
        links = [
            (0, 5), (0, 6), (1, 6), (2, 5), # Auth -> Database
            (10, 6), (11, 6), (12, 7), (13, 8), (14, 4), # Backend -> Database & Auth
            (15, 10), (17, 10), (18, 12), (19, 13), # Frontend -> Backend
            (20, 23), (21, 23), (22, 24) # API Gateway -> Order Service
        ]
        
        for source_idx, target_idx in links:
            if source_idx < len(issue_ids) and target_idx < len(issue_ids):
                source_id = issue_ids[source_idx]
                target_id = issue_ids[target_idx]
                res = httpx.post(f"{API_URL}/issues/{source_id}/dependencies", json={"depends_on_id": target_id}, headers=HEADERS)
                if res.status_code in [200, 201]:
                    print(f"Linked issue {source_idx} -> {target_idx}")
                else:
                    print(f"Failed to link {source_idx} -> {target_idx}: {res.text}")

    print(f"\nFinished! Created {len(issue_ids)} issues across {len(component_map)} components.")

if __name__ == "__main__":
    main()
