import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountComponent } from '@/test/mount'
import AgentSkillsView from '@/views/AgentSkillsView.vue'
import {
  fetchAgentSkills,
  createAgentSkill,
  updateAgentSkill,
  deleteAgentSkill,
  importAgentSkill,
  importAgentSkillFromUrl,
} from '@/api/agentSkillsApi'

const mockState = vi.hoisted(() => ({ mockMode: false }))

vi.mock('@/api/client', () => ({
  isMockMode: () => mockState.mockMode,
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}))
vi.mock('@/api/agentSkillsApi', () => ({
  fetchAgentSkills: vi.fn().mockResolvedValue([]),
  createAgentSkill: vi.fn(),
  updateAgentSkill: vi.fn(),
  deleteAgentSkill: vi.fn().mockResolvedValue(undefined),
  importAgentSkill: vi.fn(),
  importAgentSkillFromUrl: vi.fn(),
}))

const CATALOG = [
  {
    id: 'code-reviewer',
    name: 'Code Reviewer',
    behavior: '# Code Reviewer\n\nAlways prefer readable code over clever code.',
  },
  {
    id: 'security-analyst',
    name: 'Security Analyst',
    behavior: 'Assume hostile input.',
  },
]

function pickFile(wrapper: ReturnType<typeof mountComponent>['wrapper'], file: File) {
  const input = wrapper.find('input[type="file"]')
  Object.defineProperty(input.element, 'files', { value: [file] })
  return input.trigger('change')
}

describe('AgentSkillsView (issue #610)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockState.mockMode = false
    vi.mocked(fetchAgentSkills).mockResolvedValue(CATALOG)
  })

  it('lists the catalog and reads the full behavior of a selected skill', async () => {
    const { wrapper } = mountComponent(AgentSkillsView)
    await flushPromises()

    expect(fetchAgentSkills).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Code Reviewer')
    expect(wrapper.text()).toContain('Security Analyst')
    expect(wrapper.text()).toContain('Select a skill from the list')

    const rows = wrapper.findAll('ul button')
    await rows[0].trigger('click')

    expect(wrapper.text()).toContain('# Code Reviewer')
    expect(wrapper.text()).toContain('Always prefer readable code')
  })

  it('filters the catalog with the search input', async () => {
    const { wrapper } = mountComponent(AgentSkillsView)
    await flushPromises()

    await wrapper.find('input[placeholder="Search skills..."]').setValue('security')
    await flushPromises()

    expect(wrapper.text()).toContain('Security Analyst')
    expect(wrapper.text()).not.toContain('Code Reviewer')
  })

  it('creates a skill through POST and refreshes the list', async () => {
    vi.mocked(createAgentSkill).mockResolvedValue({
      id: 'qa-bot',
      name: 'QA Bot',
      behavior: 'Test everything twice.',
    })
    const { wrapper } = mountComponent(AgentSkillsView)
    await flushPromises()

    await wrapper.findAll('button').find(b => b.text() === 'New skill')!.trigger('click')
    await wrapper.find('input[placeholder="Skill name"]').setValue('QA Bot')
    await wrapper.find('textarea').setValue('Test everything twice.')
    await wrapper.findAll('button').find(b => b.text() === 'Save')!.trigger('click')
    await flushPromises()

    expect(createAgentSkill).toHaveBeenCalledWith('QA Bot', 'Test everything twice.')
    expect(wrapper.text()).toContain('Skill saved.')
    expect(wrapper.text()).toContain('QA Bot')
  })

  it('edits a selected skill through PUT with name and behavior', async () => {
    vi.mocked(updateAgentSkill).mockResolvedValue({
      id: 'security-analyst',
      name: 'Sec Analyst',
      behavior: 'Assume hostile input, always.',
    })
    const { wrapper } = mountComponent(AgentSkillsView)
    await flushPromises()

    await wrapper.findAll('ul button').find(b => b.text().includes('Security Analyst'))!.trigger('click')
    await wrapper.findAll('button').find(b => b.text() === 'Edit')!.trigger('click')
    await wrapper.find('input[placeholder="Skill name"]').setValue('Sec Analyst')
    await wrapper.find('textarea').setValue('Assume hostile input, always.')
    await wrapper.findAll('button').find(b => b.text() === 'Save')!.trigger('click')
    await flushPromises()

    expect(updateAgentSkill).toHaveBeenCalledWith('security-analyst', {
      name: 'Sec Analyst',
      behavior: 'Assume hostile input, always.',
    })
    expect(wrapper.text()).toContain('Sec Analyst')
  })

  it('deletes a skill only after confirming', async () => {
    const { wrapper } = mountComponent(AgentSkillsView)
    await flushPromises()

    await wrapper.findAll('ul button').find(b => b.text().includes('Code Reviewer'))!.trigger('click')
    await wrapper.findAll('button').find(b => b.text() === 'Delete')!.trigger('click')
    expect(deleteAgentSkill).not.toHaveBeenCalled()

    await wrapper.findAll('button').find(b => b.text() === 'Confirm')!.trigger('click')
    await flushPromises()

    expect(deleteAgentSkill).toHaveBeenCalledWith('code-reviewer')
    expect(wrapper.text()).toContain('Skill deleted.')
    expect(wrapper.text()).not.toContain('Code Reviewer')
  })

  it('imports a .md file and selects the imported skill', async () => {
    vi.mocked(importAgentSkill).mockResolvedValue({
      id: 'data-quality-bot',
      name: 'Data Quality Bot',
      behavior: '# Data Quality Bot\n\nFlag every NULL.',
    })
    const { wrapper } = mountComponent(AgentSkillsView)
    await flushPromises()

    await pickFile(wrapper, new File(['# Data Quality Bot\n\nFlag every NULL.'], 'data-quality-bot.md', { type: 'text/markdown' }))
    await flushPromises()

    expect(importAgentSkill).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Skill "Data Quality Bot" imported.')
    expect(wrapper.text()).toContain('# Data Quality Bot')
  })

  it('surfaces a conflict message when the import hits a duplicate name', async () => {
    vi.mocked(importAgentSkill).mockRejectedValue(Object.assign(new Error('conflict'), { status: 409 }))
    const { wrapper } = mountComponent(AgentSkillsView)
    await flushPromises()

    await pickFile(wrapper, new File(['# Code Reviewer'], 'dup.md', { type: 'text/markdown' }))
    await flushPromises()

    expect(wrapper.text()).toContain('A skill with that name already exists.')
  })

  it('imports a skill from a GitHub URL through the URL form', async () => {
    vi.mocked(importAgentSkillFromUrl).mockResolvedValue({
      id: 'url-skill',
      name: 'URL Skill',
      behavior: '# URL Skill\n\nFrom a repository.',
    })
    const { wrapper } = mountComponent(AgentSkillsView)
    await flushPromises()

    await wrapper.findAll('button').find(b => b.text() === 'Import URL')!.trigger('click')
    await wrapper
      .find('input[type="url"]')
      .setValue('https://github.com/acme/skills/blob/main/url-skill.md')
    await wrapper.findAll('button').find(b => b.text() === 'Import')!.trigger('click')
    await flushPromises()

    expect(importAgentSkillFromUrl).toHaveBeenCalledWith(
      'https://github.com/acme/skills/blob/main/url-skill.md',
    )
    expect(wrapper.text()).toContain('Skill "URL Skill" imported.')
    expect(wrapper.text()).toContain('# URL Skill')
    expect(wrapper.find('input[type="url"]').exists()).toBe(false)
  })

  it('shows the backend detail on a 422 URL rejection and keeps the form open', async () => {
    vi.mocked(importAgentSkillFromUrl).mockRejectedValue(
      Object.assign(new Error('url must point to a .md, .markdown or .txt file'), { status: 422 }),
    )
    const { wrapper } = mountComponent(AgentSkillsView)
    await flushPromises()

    await wrapper.findAll('button').find(b => b.text() === 'Import URL')!.trigger('click')
    await wrapper.find('input[type="url"]').setValue('https://github.com/acme/repo/blob/main/x.pdf')
    await wrapper.findAll('button').find(b => b.text() === 'Import')!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('url must point to a .md, .markdown or .txt file')
    expect(wrapper.find('input[type="url"]').exists()).toBe(true)
  })

  it('surfaces a fetch failure when the URL is unreachable (502)', async () => {
    vi.mocked(importAgentSkillFromUrl).mockRejectedValue(
      Object.assign(new Error('could not fetch the URL'), { status: 502 }),
    )
    const { wrapper } = mountComponent(AgentSkillsView)
    await flushPromises()

    await wrapper.findAll('button').find(b => b.text() === 'Import URL')!.trigger('click')
    await wrapper.find('input[type="url"]').setValue('https://raw.githubusercontent.com/a/b/main/x.md')
    await wrapper.findAll('button').find(b => b.text() === 'Import')!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Could not download the URL.')
  })
})
