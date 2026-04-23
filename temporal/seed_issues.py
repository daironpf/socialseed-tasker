import httpx
import random
import time

API_URL = "http://localhost:8000/api/v1"

COMPONENTS = {
    "Frontend": "d5c478d8-2fab-44c9-8e95-385a56c585da",
    "Backend": "b03954a3-4305-4a5a-8371-249d4cdbebbc",
    "Database": "eb558ddd-885d-4812-bdb5-e7dbf10cad6a",
    "Auth": "d7c8da07-75e2-4e1e-bf6e-6fad003309e0"
}

PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

ISSUES_DATA = [
    # Auth
    {"title": "Implement JWT logic", "comp": "Auth", "priority": "CRITICAL"},
    {"title": "Setup OAuth2 with Google", "comp": "Auth", "priority": "HIGH"},
    {"title": "User registration endpoint", "comp": "Auth", "priority": "CRITICAL"},
    {"title": "Password reset flow", "comp": "Auth", "priority": "MEDIUM"},
    {"title": "Email verification service", "comp": "Auth", "priority": "MEDIUM"},
    
    # Database
    {"title": "Design user schema", "comp": "Database", "priority": "CRITICAL"},
    {"title": "Design product schema", "comp": "Database", "priority": "CRITICAL"},
    {"title": "Design order schema", "comp": "Database", "priority": "CRITICAL"},
    {"title": "Setup database migrations", "comp": "Database", "priority": "HIGH"},
    {"title": "Optimize search indexes", "comp": "Database", "priority": "MEDIUM"},
    
    # Backend
    {"title": "Product CRUD API", "comp": "Backend", "priority": "HIGH"},
    {"title": "Search product endpoint", "comp": "Backend", "priority": "HIGH"},
    {"title": "Cart management logic", "comp": "Backend", "priority": "HIGH"},
    {"title": "Checkout process API", "comp": "Backend", "priority": "CRITICAL"},
    {"title": "Payment gateway integration", "comp": "Backend", "priority": "CRITICAL"},
    {"title": "Order history endpoint", "comp": "Backend", "priority": "MEDIUM"},
    {"title": "Admin dashboard API", "comp": "Backend", "priority": "MEDIUM"},
    {"title": "Image upload service", "comp": "Backend", "priority": "MEDIUM"},
    {"title": "Inventory management logic", "comp": "Backend", "priority": "HIGH"},
    {"title": "Review and rating system", "comp": "Backend", "priority": "LOW"},
    
    # Frontend
    {"title": "Setup React project", "comp": "Frontend", "priority": "HIGH"},
    {"title": "Home page layout", "comp": "Frontend", "priority": "MEDIUM"},
    {"title": "Product listing page", "comp": "Frontend", "priority": "HIGH"},
    {"title": "Product detail view", "comp": "Frontend", "priority": "MEDIUM"},
    {"title": "Shopping cart UI", "comp": "Frontend", "priority": "HIGH"},
    {"title": "Checkout form", "comp": "Frontend", "priority": "CRITICAL"},
    {"title": "User login page", "comp": "Frontend", "priority": "HIGH"},
    {"title": "User profile dashboard", "comp": "Frontend", "priority": "MEDIUM"},
    {"title": "Search bar component", "comp": "Frontend", "priority": "MEDIUM"},
    {"title": "Notification system", "comp": "Frontend", "priority": "LOW"},
    {"title": "Order confirmation page", "comp": "Frontend", "priority": "MEDIUM"},
    {"title": "Responsive header/footer", "comp": "Frontend", "priority": "LOW"},
    {"title": "Filter and sort component", "comp": "Frontend", "priority": "MEDIUM"},
    {"title": "Review form UI", "comp": "Frontend", "priority": "LOW"},
    {"title": "Admin: Product management UI", "comp": "Frontend", "priority": "MEDIUM"},
    
    # Generic / More Issues to reach 50
    {"title": "CI/CD Pipeline setup", "comp": "Backend", "priority": "HIGH"},
    {"title": "Unit tests for Auth", "comp": "Auth", "priority": "HIGH"},
    {"title": "Integration tests for Orders", "comp": "Backend", "priority": "HIGH"},
    {"title": "Performance benchmarking", "comp": "Database", "priority": "MEDIUM"},
    {"title": "Error logging setup", "comp": "Backend", "priority": "MEDIUM"},
    {"title": "Sitemap generation", "comp": "Frontend", "priority": "LOW"},
    {"title": "SEO optimization", "comp": "Frontend", "priority": "LOW"},
    {"title": "Multi-currency support", "comp": "Backend", "priority": "MEDIUM"},
    {"title": "Localization (i18n)", "comp": "Frontend", "priority": "MEDIUM"},
    {"title": "API Documentation (Swagger)", "comp": "Backend", "priority": "MEDIUM"},
    {"title": "Dockerize microservices", "comp": "Backend", "priority": "HIGH"},
    {"title": "Prometheus/Grafana setup", "comp": "Backend", "priority": "LOW"},
    {"title": "Redis caching layer", "comp": "Database", "priority": "MEDIUM"},
    {"title": "Stripe Webhook handler", "comp": "Backend", "priority": "HIGH"},
    {"title": "Wishlist functionality", "comp": "Frontend", "priority": "LOW"}
]

def create_issue(data):
    issue_payload = {
        "title": data["title"],
        "description": f"Detailed task for {data['title']}",
        "priority": data["priority"],
        "component_id": COMPONENTS[data["comp"]],
        "labels": [data["comp"].lower(), "ecommerce"]
    }
    response = httpx.post(f"{API_URL}/issues", json=issue_payload)
    if response.status_code == 201:
        return response.json()["data"]["id"]
    else:
        print(f"Error creating issue {data['title']}: {response.text}")
        return None

def main():
    print(f"Creating {len(ISSUES_DATA)} issues...")
    issue_ids = []
    for item in ISSUES_DATA:
        issue_id = create_issue(item)
        if issue_id:
            issue_ids.append(issue_id)
            print(f"Created: {item['title']} -> {issue_id}")
        time.sleep(0.1) # Small delay to be gentle

    print("\nLinking dependencies...")
    # Add some logical dependencies
    # 1. Product CRUD depends on Product Schema
    # 2. Checkout API depends on Payment Gateway
    # 3. Frontend Home depends on Product CRUD API
    
    # Let's find some IDs
    # (Simplified for the script)
    
    # Example: link last 10 issues to some previous ones
    for i in range(10):
        target = issue_ids[i]
        dependency = issue_ids[i+20]
        httpx.post(f"{API_URL}/issues/{target}/dependencies", json={"depends_on_id": dependency})
        print(f"Linked {target} to depend on {dependency}")

if __name__ == "__main__":
    main()
