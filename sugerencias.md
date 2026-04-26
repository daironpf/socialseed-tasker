Para transformar **Tasker** en una plataforma de grado empresarial que una Fortune 100 amaría, necesitamos pasar de un "gestor de tareas" a un **"Grafo de Operaciones de Ingeniería"**. 

He diseñado esta lista de **Issues** técnicos siguiendo tu estructura actual. Estos deben ser implementados en tu API para que el **Aura Agent** tenga los datos necesarios para razonar sobre el sistema completo.

---

### Phase 1: Core Graph Refactoring (The Foundation)
Antes de añadir nuevas funciones, debemos convertir las referencias de ID en relaciones de primer nivel.

* **Issue 1: Migración de IDs a Relaciones Semánticas**
    * **Context:** Eliminar `component_id` de las propiedades de `Issue` y crear relaciones físicas en Neo4j.
    * **Acceptance Criteria:** - Implementar relación `(Issue)-[:BELONGS_TO]->(Component)`.
        - Implementar relación `(Issue)-[:BLOCKS]->(Issue)` para dependencias.
    * **API Goal:** El endpoint `POST /issues` debe aceptar un `component_id` y crear el link automáticamente en el grafo.

* **Issue 2: Implementación de Grafo de Dependencias de Componentes**
    * **Context:** Los componentes no están aislados.
    * **Acceptance Criteria:**
        - Crear relación `(Component)-[:DEPENDS_ON]->(Component)`.
    - **API Goal:** `POST /components/{id}/dependencies` para mapear la arquitectura del sistema.

---

### Phase 2: Enterprise Strategy & Value (The "Why")
Para que los directivos sean "felices", necesitan ver el retorno de inversión y el alineamiento.

* **Issue 3: Nodo de Epics y Objetivos de Negocio (OKRs)**
    * **Context:** Agrupar tareas en iniciativas mayores.
    * **Acceptance Criteria:**
        - Nuevo Label: `Epic` y `Objective`.
        - Relaciones: `(Issue)-[:PART_OF]->(Epic)-[:CONTRIBUTES_TO]->(Objective)`.
    * **API Goal:** CRUD de Epics y capacidad de vincular múltiples Issues en una sola transacción.

* **Issue 4: Atribución de Costos y Esfuerzo**
    * **Context:** Las empresas Fortune 100 necesitan trackear el "Capitalized Software Development".
    * **Properties to add:** `estimated_hours`, `hourly_rate_tier`, `actual_hours`.
    * **API Goal:** Endpoint `/analytics/cost-per-component` que use Cypher para sumar el esfuerzo de todos los Issues hijos.

---

### Phase 3: Infrastructure & Traceability (The "Where")
Conectar el código con la realidad de los servidores.

* **Issue 5: Trazabilidad de Despliegues (Environments)**
    * **Context:** Saber exactamente qué tarea está en qué servidor.
    * **Labels:** `Environment` (Prod, Staging), `Deployment`.
    * **Acceptance Criteria:**
        - Relación `(Issue)-[:RELEASED_IN]->(Deployment)-[:TO]->(Environment)`.
    * **API Goal:** Un webhook que, al terminar un CI/CD, cree el nodo `Deployment` y lo vincule a los `Issues` incluidos en el commit.

---

### Phase 4: Artificial Intelligence Context (The "Agent")
Preparar el terreno para que el curso de Aura Agent que estás haciendo brille.

* **Issue 6: Vector Indexing para "Reasoning Logs"**
    * **Context:** Tu esquema ya tiene `reasoning_logs`. Necesitamos que sean buscables.
    * **Acceptance Criteria:**
        - Configurar un índice de vectores en Neo4j Aura sobre las propiedades `description` y `reasoning_logs`.
    * **API Goal:** Endpoint `/ai/search-context` que devuelva nodos basados en similitud semántica.

---

### Resumen del Esquema de Interacción en el API

Para que esto sea funcional, tu API debe exponer estos contratos:

| Endpoint | Acción en el Grafo | Valor Empresarial |
| :--- | :--- | :--- |
| `POST /issues/{id}/block/{target_id}` | Crea `[:BLOCKS]` | Gestión de riesgos y cuellos de botella. |
| `GET /components/{id}/impact-analysis` | Cypher: Travesía de relaciones | "Si esto falla, ¿qué se rompe?" |
| `PATCH /issues/{id}/status` | Actualiza `status` y `updated_at` | Visibilidad en tiempo real para stakeholders. |
| `POST /objectives` | Crea nodo raíz de valor | Alineación estratégica de la ingeniería. |