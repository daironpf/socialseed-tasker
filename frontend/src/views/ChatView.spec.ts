import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import i18n from '@/i18n'
import ChatView from '@/views/ChatView.vue'
import { setApiMode } from '@/api/client'
import { useChatStore } from '@/stores/chatStore'

type ChatStore = ReturnType<typeof useChatStore>

const PII_TEXT = 'mi tarjeta es 4111111111111111, cuidado'

function mountChat(): { wrapper: VueWrapper; store: ChatStore } {
  const pinia = createPinia()
  setActivePinia(pinia)
  const store = useChatStore()
  store.selectConversation('conv-3')
  const wrapper = mount(ChatView, { global: { plugins: [pinia, i18n] } })
  return { wrapper, store }
}

function findPiiButton(label: string): HTMLButtonElement | undefined {
  const heading = Array.from(document.body.querySelectorAll('h3')).find(
    h => h.textContent?.trim() === 'Sensitive Data Detected',
  )
  const overlay = heading?.closest('div.fixed.inset-0')
  return Array.from(overlay?.querySelectorAll('button') ?? []).find(
    b => b.textContent?.trim() === label,
  )
}

describe('ChatView', () => {
  beforeEach(() => {
    setApiMode('mock')
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.restoreAllMocks()
    setApiMode('mock')
  })

  it('renders the active conversation with its history and input', () => {
    const { wrapper } = mountChat()
    expect(wrapper.find('textarea').exists()).toBe(true)
    expect(wrapper.find('.flex-1.overflow-y-auto').exists()).toBe(true)
    expect(wrapper.text()).toContain('alice')
    expect(wrapper.text()).toContain('Kanban drag-and-drop')
  })

  it('notifies typing while composing and sends on Enter with trimmed text', async () => {
    const { wrapper, store } = mountChat()
    const notify = vi.spyOn(store, 'notifyTyping')
    const send = vi.spyOn(store, 'sendMessage')
    const textarea = wrapper.find('textarea')

    await textarea.setValue('hola equipo')
    expect(notify).toHaveBeenCalled()

    await textarea.setValue('  hola equipo  ')
    await textarea.trigger('keydown.enter')
    expect(send).toHaveBeenCalledTimes(1)
    expect(send).toHaveBeenCalledWith('conv-3', 'hola equipo')
    expect((textarea.element as HTMLTextAreaElement).value).toBe('')
    expect(findPiiButton('Send Anyway')).toBeUndefined()
  })

  it('blocks critical PII on Enter and masks it before sending', async () => {
    const { wrapper, store } = mountChat()
    const send = vi.spyOn(store, 'sendMessage')
    const textarea = wrapper.find('textarea')

    await textarea.setValue(PII_TEXT)
    await textarea.trigger('keydown.enter')
    expect(send).not.toHaveBeenCalled()
    expect((textarea.element as HTMLTextAreaElement).value).toBe(PII_TEXT)

    const maskButton = findPiiButton('Mask & Send')
    expect(maskButton).toBeDefined()
    maskButton!.click()
    await nextTick()

    expect(send).toHaveBeenCalledTimes(1)
    const masked = send.mock.calls[0][1]
    expect(masked).toContain('[REDACTED_SECRET]')
    expect(masked).not.toContain('4111111111111111')
    expect((textarea.element as HTMLTextAreaElement).value).toBe('')
    expect(findPiiButton('Mask & Send')).toBeUndefined()
  })

  it('keeps the sensitive text in the box when the warning is cancelled', async () => {
    const { wrapper, store } = mountChat()
    const send = vi.spyOn(store, 'sendMessage')
    const textarea = wrapper.find('textarea')

    await textarea.setValue(PII_TEXT)
    await textarea.trigger('keydown.enter')
    expect(send).not.toHaveBeenCalled()

    const cancelButton = findPiiButton('Cancel')
    expect(cancelButton).toBeDefined()
    cancelButton!.click()
    await nextTick()

    expect(send).not.toHaveBeenCalled()
    expect((textarea.element as HTMLTextAreaElement).value).toBe(PII_TEXT)
    expect(findPiiButton('Cancel')).toBeUndefined()
  })

  it('forwards the raw text only after an explicit confirmation', async () => {
    const { wrapper, store } = mountChat()
    const send = vi.spyOn(store, 'sendMessage')
    const textarea = wrapper.find('textarea')

    await textarea.setValue(PII_TEXT)
    await textarea.trigger('keydown.enter')
    const confirmButton = findPiiButton('Send Anyway')
    expect(confirmButton).toBeDefined()
    confirmButton!.click()
    await nextTick()

    expect(send).toHaveBeenCalledTimes(1)
    expect(send.mock.calls[0][1]).toContain('4111111111111111')
    expect((textarea.element as HTMLTextAreaElement).value).toBe('')
  })
})
