import { describe, it, expect } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import TaskChecklist from '@/components/analysis/TaskChecklist.vue'
import { mountComponent } from '@/test/mount'

const CONTENT = ['- [ ] install dependencies', '- [x] run tests'].join('\n')

async function mountChecklist(props: Record<string, unknown>) {
  const { wrapper } = mountComponent(TaskChecklist, { props })
  await flushPromises()
  return wrapper
}

describe('TaskChecklist', () => {
  it('renders the progress counter with overrides applied', async () => {
    const wrapper = await mountChecklist({ content: CONTENT })

    expect(wrapper.text()).toContain('Checked 1 of 2')

    const withOverride = await mountChecklist({
      content: CONTENT,
      checked: { 'install dependencies': true, 'run tests': false },
    })
    expect(withOverride.text()).toContain('Checked 1 of 2')
  })

  it('hides the counter when there are no checklist items', async () => {
    const wrapper = await mountChecklist({ content: 'Just a plain progress note' })

    expect(wrapper.text()).not.toContain('Checked')
    expect(wrapper.find('input[type="checkbox"]').exists()).toBe(false)
  })

  it('renders enabled checkboxes and re-emits toggle events', async () => {
    const wrapper = await mountChecklist({
      content: CONTENT,
      checked: { 'install dependencies': true },
    })

    const boxes = wrapper.findAll<HTMLInputElement>('input[type="checkbox"]')
    expect(boxes).toHaveLength(2)
    expect(boxes.every((b) => b.attributes('disabled') !== undefined)).toBe(false)
    expect(boxes[0].element.checked).toBe(true)

    await boxes[1].trigger('click')
    expect(wrapper.emitted('toggle')).toHaveLength(1)
    expect(wrapper.emitted('toggle')![0]).toEqual(['run tests', false])
  })
})
