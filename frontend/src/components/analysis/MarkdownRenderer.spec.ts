import { describe, it, expect } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import MarkdownRenderer from '@/components/analysis/MarkdownRenderer.vue'
import { mountComponent } from '@/test/mount'

const CONTENT = ['- [ ] install dependencies', '- [x] run tests', '- [ ] deploy'].join('\n')

async function mountRenderer(props: Record<string, unknown>) {
  const { wrapper } = mountComponent(MarkdownRenderer, { props })
  await flushPromises()
  return wrapper
}

describe('MarkdownRenderer', () => {
  it('renders disabled checkboxes by default (non-interactive)', async () => {
    const wrapper = await mountRenderer({ content: CONTENT })

    const boxes = wrapper.findAll<HTMLInputElement>('input[type="checkbox"]')
    expect(boxes).toHaveLength(3)
    expect(boxes.every((b) => b.attributes('disabled') !== undefined)).toBe(true)
    expect(boxes[0].element.checked).toBe(false)
    expect(boxes[1].element.checked).toBe(true)
  })

  it('renders enabled checkboxes when interactive', async () => {
    const wrapper = await mountRenderer({ content: CONTENT, interactive: true })

    const boxes = wrapper.findAll<HTMLInputElement>('input[type="checkbox"]')
    expect(boxes).toHaveLength(3)
    expect(boxes.some((b) => b.attributes('disabled') !== undefined)).toBe(false)
  })

  it('applies override state on top of markdown markers', async () => {
    const wrapper = await mountRenderer({
      content: CONTENT,
      interactive: true,
      checked: { 'install dependencies': true, 'run tests': false },
    })

    const boxes = wrapper.findAll<HTMLInputElement>('input[type="checkbox"]')
    expect(boxes[0].element.checked).toBe(true)
    expect(boxes[1].element.checked).toBe(false)
    expect(boxes[2].element.checked).toBe(false)
  })

  it('emits toggle with the normalized item key on click', async () => {
    const wrapper = await mountRenderer({ content: CONTENT, interactive: true })

    await wrapper.findAll<HTMLInputElement>('input[type="checkbox"]')[0].trigger('click')

    expect(wrapper.emitted('toggle')).toHaveLength(1)
    expect(wrapper.emitted('toggle')![0]).toEqual(['install dependencies', true])
  })

  it('emits unchecking for an overridden checked item', async () => {
    const wrapper = await mountRenderer({
      content: CONTENT,
      interactive: true,
      checked: { 'run tests': true },
    })

    await wrapper.findAll<HTMLInputElement>('input[type="checkbox"]')[1].trigger('click')

    expect(wrapper.emitted('toggle')![0]).toEqual(['run tests', false])
  })

  it('normalizes item keys with trim and lowercase', async () => {
    const wrapper = await mountRenderer({
      content: '- [ ]   Deploy   STAGE  ',
      interactive: true,
    })

    await wrapper.find('input[type="checkbox"]').trigger('click')

    expect(wrapper.emitted('toggle')![0]).toEqual(['deploy stage', true])
  })

  it('escapes markup inside task text', async () => {
    const wrapper = await mountRenderer({
      content: '- [ ] verify <script>alert(1)</script>',
      interactive: true,
    })

    expect(wrapper.find('script').exists()).toBe(false)
    expect(wrapper.text()).toContain('verify <script>alert(1)</script>')

    await wrapper.find('input[type="checkbox"]').trigger('click')
    expect(wrapper.emitted('toggle')![0][0]).toBe('verify <script>alert(1)</script>')
  })
})
