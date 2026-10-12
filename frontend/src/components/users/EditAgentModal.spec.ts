import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountComponent } from '@/test/mount'
import EditAgentModal from '@/components/users/EditAgentModal.vue'
import { fetchTools, fetchSkills } from '@/api/catalogsApi'
import { fetchAgentSkills } from '@/api/agentSkillsApi'
import { apiMode } from '@/api/client'
import { AGENT_TOOLS } from '@/types/agentStudio'

vi.mock('@/api/catalogsApi', () => ({
  fetchTools: vi.fn(),
  fetchSkills: vi.fn().mockResolvedValue([]),
  resetCatalogsCache: vi.fn(),
}))
vi.mock('@/api/agentSkillsApi', () => ({
  fetchAgentSkills: vi.fn().mockResolvedValue([]),
  createAgentSkill: vi.fn(),
}))

const CATALOG = [
  { id: 'code_search', name: 'Code search', description: 'Search the codebase' },
  { id: 'shell', name: 'Shell', description: null },
]

const AGENT = {
  id: 'uid-bot',
  username: 'bot-qa',
  email: 'bot@socialseed.com',
  model: 'gpt-4o',
  tools: ['code_search'],
  skills: ['testing'],
  write_access: [],
  avatar: '🤖',
}

function toolButtons(wrapper: ReturnType<typeof mountComponent>['wrapper']) {
  return wrapper.findAll('button').filter(b => CATALOG.some(t => b.text() === t.id) || AGENT_TOOLS.some(t => b.text() === t))
}

describe('EditAgentModal tools catalog (issue #572)', () => {
  let previousMode: typeof apiMode.value

  beforeEach(() => {
    previousMode = apiMode.value
    vi.clearAllMocks()
  })

  afterEach(() => {
    apiMode.value = previousMode
  })

  it('renders tools from GET /tools in real mode and sends the selection in the payload', async () => {
    apiMode.value = 'real'
    vi.mocked(fetchTools).mockResolvedValue(CATALOG)

    const { wrapper } = mountComponent(EditAgentModal, {
      props: { show: true, agent: AGENT },
    })
    await flushPromises()

    const labels = toolButtons(wrapper).map(b => b.text())
    expect(fetchTools).toHaveBeenCalledTimes(1)
    expect(labels).toContain('code_search')
    expect(labels).toContain('shell')

    // the stored selection paints as checked (canonical slug match, #572)
    const checked = toolButtons(wrapper).filter(b => b.classes().includes('border-blue-500'))
    expect(checked.map(b => b.text())).toEqual(['code_search'])

    // toggle 'shell' on and save: both canonical slugs travel in the payload
    const shell = toolButtons(wrapper).find(b => b.text() === 'shell')
    await shell!.trigger('click')
    const save = wrapper.findAll('button').find(b => b.text() === 'Save Changes')
    await save!.trigger('click')

    expect(wrapper.emitted('save')![0][0]).toMatchObject({ tools: ['code_search', 'shell'] })
  })

  it('falls back to AGENT_TOOLS in mock mode without calling the endpoint', async () => {
    apiMode.value = 'mock'

    const { wrapper } = mountComponent(EditAgentModal, {
      props: { show: true, agent: { ...AGENT, tools: [] } },
    })
    await flushPromises()

    expect(fetchTools).not.toHaveBeenCalled()
    const labels = toolButtons(wrapper).map(b => b.text())
    for (const tool of AGENT_TOOLS) {
      expect(labels).toContain(tool)
    }
  })

  it('degrades to AGENT_TOOLS when GET /tools fails (503 keeps the picker usable)', async () => {
    apiMode.value = 'real'
    vi.mocked(fetchTools).mockRejectedValue(new Error('PostgreSQL not configured'))

    const { wrapper } = mountComponent(EditAgentModal, {
      props: { show: true, agent: { ...AGENT, tools: [] } },
    })
    await flushPromises()

    const labels = toolButtons(wrapper).map(b => b.text())
    for (const tool of AGENT_TOOLS) {
      expect(labels).toContain(tool)
    }
  })

  it('requests the catalog on every open (the TTL cache lives in catalogsApi, #572)', async () => {
    apiMode.value = 'real'
    vi.mocked(fetchTools).mockResolvedValue(CATALOG)

    const { wrapper } = mountComponent(EditAgentModal, {
      props: { show: false, agent: AGENT },
    })
    expect(fetchTools).not.toHaveBeenCalled()

    await wrapper.setProps({ show: true })
    await flushPromises()
    await wrapper.setProps({ show: false })
    await wrapper.setProps({ show: true })
    await flushPromises()

    expect(fetchTools).toHaveBeenCalledTimes(2)
  })

  it('replaces the skills through the floating agent picker (issue #577)', async () => {
    apiMode.value = 'real'
    vi.mocked(fetchAgentSkills).mockResolvedValue([
      { id: 'code-reviewer', name: 'Code Reviewer', behavior: 'Review carefully.' },
      { id: 'docs-writer', name: 'Docs Writer', behavior: 'Write clear docs.' },
    ])

    const { wrapper } = mountComponent(EditAgentModal, {
      props: { show: true, agent: AGENT },
    })
    await flushPromises()

    // The free-text skill input is gone: only "+" opens the picker.
    expect(wrapper.find('input[placeholder="Add skill..."]').exists()).toBe(false)
    await wrapper.findAll('button').find(b => b.attributes('aria-label') === 'Add skills')!.trigger('click')
    await flushPromises()

    expect(fetchAgentSkills).toHaveBeenCalledTimes(1)
    expect(fetchSkills).not.toHaveBeenCalled() // never the human catalog
    const boxes = wrapper.findAll('input[type="checkbox"]')
    expect(boxes).toHaveLength(2)

    await boxes[0].setValue(true)
    await wrapper.findAll('button').find(b => b.text() === 'Apply')!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Code Reviewer')
    const save = wrapper.findAll('button').find(b => b.text() === 'Save Changes')
    await save!.trigger('click')

    expect(wrapper.emitted('save')![0][0]).toMatchObject({
      skills: ['testing', 'Code Reviewer'],
    })
  })
})
