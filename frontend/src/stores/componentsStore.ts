import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/componentsApi'
import type { Component, ComponentCreateRequest } from '@/types'

export const useComponentsStore = defineStore('components', () => {
  const components = ref<Component[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  function getComponentById(id: string): Component | undefined {
    return components.value.find((c) => c.id === id)
  }

  function componentsByProject(project: string) {
    return components.value.filter((c) => c.project === project)
  }

  async function fetchComponents(project?: string) {
    loading.value = true
    error.value = null
    try {
      components.value = await api.fetchComponents(project)
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function fetchComponent(id: string): Promise<Component | null> {
    try {
      return await api.fetchComponent(id)
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function createComponent(body: ComponentCreateRequest): Promise<Component | null> {
    try {
      const comp = await api.createComponent(body)
      components.value.push(comp)
      return comp
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function updateComponent(
    id: string,
    body: Partial<ComponentCreateRequest>,
  ): Promise<Component | null> {
    try {
      const updated = await api.updateComponent(id, body)
      const idx = components.value.findIndex((c) => c.id === id)
      if (idx !== -1) components.value[idx] = updated
      return updated
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function deleteComponent(id: string, force = false): Promise<boolean> {
    try {
      await api.deleteComponent(id, force)
      components.value = components.value.filter((c) => c.id !== id)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    }
  }

  return {
    components,
    loading,
    error,
    getComponentById,
    componentsByProject,
    fetchComponents,
    fetchComponent,
    createComponent,
    updateComponent,
    deleteComponent,
  }
})
