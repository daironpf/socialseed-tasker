# 75-add-component-lookup-by-name-endpoint

## Problema identificado
El sistema no permite buscar componentes por nombre. Un agente de IA que quiere crear un issue con un nombre de componente conocido (ej: "backend") no tiene forma de obtener el ID correspondiente sin listar todos los componentes y buscar manualmente.

## Evidencia
```bash
# El agente sabe que quiere usar el componente "ecommerce-core" pero no conoce su UUID
# No hay endpoint para buscar por nombre:
curl -s "http://localhost:8000/api/v1/components?name=ecommerce-core"
# Devuelve todos los componentes, no filtra por nombre

# Debe listar todos y buscar manualmente:
curl -s "http://localhost:8000/api/v1/components"
# Luego parsear para encontrar el ID correcto
```

## Impacto negativo
- El agente debe obtener todos los componentes y filtrar manualmente
- Ineficiente para proyectos con muchos componentes
- El agente no puede trabajar de forma natural con nombres de componentes

## Propuesta de solución
1. Añadir parámetro de query `name` al endpoint GET /components
2. Crear endpoint dedicado GET /components/by-name/{name}
3. Indexar por nombre en Neo4j para búsquedas eficientes