import { mount, type MountingOptions } from '@vue/test-utils'
import { createPinia } from 'pinia'
import type { Component } from 'vue'
import i18n from '@/i18n'

export function mountComponent(component: Component, options: MountingOptions<any, any> = {}) {
  const pinia = createPinia()
  const wrapper = mount(component, {
    attachTo: document.body,
    ...options,
    global: {
      plugins: [pinia, i18n],
      ...options.global,
      stubs: { RouterLink: true, ...(options.global?.stubs ?? {}) },
    },
  })
  return { wrapper, pinia }
}
