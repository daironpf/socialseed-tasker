import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mountComponent } from '@/test/mount'
import McpSetupPanel from '@/components/setup/McpSetupPanel.vue'

const API_KEY = 'tasker_sk_live_abc123_secret'
const writeText = vi.fn().mockResolvedValue(undefined)

function mountPanel(mcpPort = 0) {
  const { wrapper } = mountComponent(McpSetupPanel, {
    props: { apiKey: API_KEY, mcpPort },
  })
  return wrapper
}

describe('McpSetupPanel', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    writeText.mockClear()
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders the master API key', () => {
    const wrapper = mountPanel()
    expect(wrapper.find('[data-testid="setup-ai-key"]').text()).toBe(API_KEY)
  })

  it('builds an MCP snippet pointing to /mcp with the X-API-Key header', () => {
    const wrapper = mountPanel(8888)
    const snippet = wrapper.find('[data-testid="setup-mcp-snippet"]').text()
    expect(snippet).toContain('mcpServers')
    expect(snippet).toContain('/mcp')
    expect(snippet).toContain(':8888/mcp')
    expect(snippet).toContain('X-API-Key')
    expect(snippet).toContain(API_KEY)
  })

  it('uses the configured port when the field is edited', async () => {
    const wrapper = mountPanel()
    const portInput = wrapper.find<HTMLInputElement>('[data-testid="setup-panel-mcp-port"]')
    expect(portInput.element.value).toBe('')

    await portInput.setValue('9100')
    const snippet = wrapper.find('[data-testid="setup-mcp-snippet"]').text()
    expect(snippet).toContain(':9100/mcp')
    expect(snippet).not.toContain(':0/mcp')
  })

  it('copies the master API key with visual feedback', async () => {
    const wrapper = mountPanel()
    const button = wrapper.find('[data-testid="setup-copy-key"]')
    expect(button.text()).not.toBe('Copied!')

    await button.trigger('click')
    expect(writeText).toHaveBeenCalledWith(API_KEY)
    expect(wrapper.find('[data-testid="setup-copy-key"]').text()).toBe('Copied!')

    vi.advanceTimersByTime(2100)
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="setup-copy-key"]').text()).not.toBe('Copied!')
  })

  it('copies the rendered snippet', async () => {
    const wrapper = mountPanel(8888)
    await wrapper.find('[data-testid="setup-copy-snippet"]').trigger('click')

    expect(writeText).toHaveBeenCalledTimes(1)
    const copied = writeText.mock.calls[0][0] as string
    expect(copied).toContain('"url"')
    expect(copied).toContain(':8888/mcp')
    expect(copied).toContain(API_KEY)
    expect(wrapper.find('[data-testid="setup-copy-snippet"]').text()).toBe('Copied!')
  })
})
