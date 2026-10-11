import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountComponent } from '@/test/mount'
import WorkflowLibrary from '@/components/agents/WorkflowLibrary.vue'
import {
  fetchWorkflows,
  fetchWorkflow,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
} from '@/api/workflowsApi'
import type { Workflow } from '@/api/workflowsApi'

vi.mock('@/api/workflowsApi', () => ({
  fetchWorkflows: vi.fn(),
  fetchWorkflow: vi.fn(),
  createWorkflow: vi.fn(),
  updateWorkflow: vi.fn(),
  deleteWorkflow: vi.fn(),
}))

vi.mock('@/components/analysis/MarkdownRenderer.vue', () => ({
  default: {
    name: 'MarkdownRenderer',
    props: { content: { type: String, required: true } },
    template: '<div class="md-stub">{{ content }}</div>',
  },
}))

const BUILTIN: Workflow = {
  slug: 'commit-push',
  name: 'Prepare for Commit',
  description: 'Requires user approval.',
  source: 'builtin',
  created_by: null,
  content_md: null,
}

const CUSTOM: Workflow = {
  slug: 'my-flow',
  name: 'My Flow',
  description: 'Custom steps.',
  source: 'custom',
  created_by: 'admin',
  content_md: null,
}

const CUSTOM_FULL: Workflow = {
  ...CUSTOM,
  content_md: '# My Flow\n\nship it',
}

describe('WorkflowLibrary (issue #575)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists builtin and custom workflows with edit/delete only on custom', async () => {
    vi.mocked(fetchWorkflows).mockResolvedValue([BUILTIN, CUSTOM])

    const { wrapper } = mountComponent(WorkflowLibrary)
    await flushPromises()

    expect(fetchWorkflows).toHaveBeenCalledWith(undefined)
    expect(wrapper.text()).toContain('Prepare for Commit')
    expect(wrapper.text()).toContain('My Flow')
    expect(wrapper.text()).toContain('commit-push')
    expect(wrapper.text()).toContain('Builtin')
    expect(wrapper.text()).toContain('Custom')

    const deleteButtons = wrapper.findAll('button').filter(b => b.text() === 'Delete')
    expect(deleteButtons).toHaveLength(1)
  })

  it('fetches the full definition and renders its markdown on open', async () => {
    vi.mocked(fetchWorkflows).mockResolvedValue([CUSTOM])
    vi.mocked(fetchWorkflow).mockResolvedValue(CUSTOM_FULL)

    const { wrapper } = mountComponent(WorkflowLibrary)
    await flushPromises()

    await wrapper.find('li > div > button').trigger('click')
    await flushPromises()

    expect(fetchWorkflow).toHaveBeenCalledWith('my-flow')
    expect(wrapper.find('.md-stub').text()).toContain('# My Flow')
  })

  it('shows the empty state', async () => {
    vi.mocked(fetchWorkflows).mockResolvedValue([])

    const { wrapper } = mountComponent(WorkflowLibrary)
    await flushPromises()

    expect(wrapper.text()).toContain('No workflows yet.')
  })

  it('shows the error state and retries on demand', async () => {
    vi.mocked(fetchWorkflows).mockRejectedValueOnce(new Error('boom'))
    vi.mocked(fetchWorkflows).mockResolvedValueOnce([BUILTIN])

    const { wrapper } = mountComponent(WorkflowLibrary)
    await flushPromises()

    expect(wrapper.text()).toContain('Could not load the workflow library.')

    const retry = wrapper.findAll('button').find(b => b.text() === 'Retry')
    await retry!.trigger('click')
    await flushPromises()

    expect(fetchWorkflows).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('Prepare for Commit')
  })

  it('reloads with the source filter when it changes', async () => {
    vi.mocked(fetchWorkflows).mockResolvedValue([BUILTIN])

    const { wrapper } = mountComponent(WorkflowLibrary)
    await flushPromises()

    await wrapper.find('select').setValue('custom')
    await flushPromises()

    expect(fetchWorkflows).toHaveBeenLastCalledWith('custom')
  })

  it('creates a custom workflow from the form', async () => {
    vi.mocked(fetchWorkflows).mockResolvedValue([CUSTOM])
    vi.mocked(createWorkflow).mockResolvedValue({ ...CUSTOM, slug: 'brand-new' })

    const { wrapper } = mountComponent(WorkflowLibrary)
    await flushPromises()

    const newButton = wrapper.findAll('button').find(b => b.text() === 'New workflow')
    await newButton!.trigger('click')

    const inputs = wrapper.findAll('input')
    await inputs[0].setValue('brand-new')
    await inputs[1].setValue('Brand New')
    const textareas = wrapper.findAll('textarea')
    await textareas[0].setValue('# Brand New\n\nbody')

    const form = wrapper.find('form')
    await form.trigger('submit')
    await flushPromises()

    expect(createWorkflow).toHaveBeenCalledWith({
      slug: 'brand-new',
      name: 'Brand New',
      description: null,
      content_md: '# Brand New\n\nbody',
    })
    expect(wrapper.text()).toContain('Workflow created.')
  })

  it('surfaces a 409 conflict when the slug is already taken', async () => {
    vi.mocked(fetchWorkflows).mockResolvedValue([])
    vi.mocked(createWorkflow).mockRejectedValue(
      Object.assign(new Error('slug already exists'), { status: 409 }),
    )

    const { wrapper } = mountComponent(WorkflowLibrary)
    await flushPromises()

    await wrapper.findAll('button').find(b => b.text() === 'New workflow')!.trigger('click')
    await wrapper.findAll('input')[0].setValue('commit-push')
    await wrapper.findAll('input')[1].setValue('Dup')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Slug already taken or the workflow is builtin.')
  })

  it('updates a custom workflow via the edit form', async () => {
    vi.mocked(fetchWorkflows).mockResolvedValue([CUSTOM])
    vi.mocked(fetchWorkflow).mockRejectedValue(new Error('no detail needed'))
    vi.mocked(updateWorkflow).mockResolvedValue({ ...CUSTOM, name: 'Renamed' })

    const { wrapper } = mountComponent(WorkflowLibrary)
    await flushPromises()

    const edit = wrapper.findAll('button').find(b => b.text() === 'Edit')
    await edit!.trigger('click')

    await wrapper.findAll('input')[1].setValue('Renamed')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(updateWorkflow).toHaveBeenCalledWith('my-flow', {
      name: 'Renamed',
      description: 'Custom steps.',
      content_md: null,
    })
    expect(wrapper.text()).toContain('Workflow updated.')
  })

  it('deletes a custom workflow and reloads the list', async () => {
    vi.mocked(fetchWorkflows).mockResolvedValue([CUSTOM])
    vi.mocked(deleteWorkflow).mockResolvedValue()

    const { wrapper } = mountComponent(WorkflowLibrary)
    await flushPromises()

    const deleteButton = wrapper.findAll('button').find(b => b.text() === 'Delete')
    await deleteButton!.trigger('click')
    await flushPromises()

    expect(deleteWorkflow).toHaveBeenCalledWith('my-flow')
    expect(wrapper.text()).toContain('Workflow deleted.')
    expect(fetchWorkflows).toHaveBeenCalledTimes(2)
  })
})
