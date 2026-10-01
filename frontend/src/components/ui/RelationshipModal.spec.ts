import { describe, it, expect } from 'vitest'
import RelationshipModal from '@/components/ui/RelationshipModal.vue'
import { mountComponent } from '@/test/mount'
import type { PolicyViolationDetail } from '@/types'

function mountModal(props: Record<string, unknown>) {
  const { wrapper } = mountComponent(RelationshipModal, {
    props: { show: true, fromLabel: 'Issue A', toLabel: 'Issue B', ...props },
  })
  return wrapper
}

const HARD_VIOLATION: PolicyViolationDetail = {
  code: 'POLICY_VIOLATION',
  message: 'Adding dependency a -> b creates a dependency chain of depth 2, exceeding max_depth 1',
  constraint: 'Max depth 1',
  rule_type: 'max_depth',
  severity: 'hard',
  suggestion: 'Restructure dependencies to reduce depth',
}

describe('RelationshipModal', () => {
  it('renders no violation panel when there is no error', () => {
    const wrapper = mountModal({ error: null })

    expect(wrapper.find('[data-testid="violation-panel"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Issue A')
    expect(wrapper.text()).toContain('Issue B')
  })

  it('renders an inline HARD violation with constraint and suggestion', () => {
    const wrapper = mountModal({ error: HARD_VIOLATION })

    const panel = wrapper.find('[data-testid="violation-panel"]')
    expect(panel.exists()).toBe(true)
    expect(panel.text()).toContain('Architectural policy violation')
    expect(panel.text()).toContain('HARD')
    expect(wrapper.find('[data-testid="violation-message"]').text()).toContain('exceeding max_depth 1')
    expect(panel.text()).toContain('Constraint: Max depth 1')
    expect(wrapper.find('[data-testid="violation-suggestion"]').text()).toContain(
      'Restructure dependencies to reduce depth',
    )
  })

  it('renders the policy name when the violation comes from the policy engine', () => {
    const wrapper = mountModal({
      error: {
        code: 'POLICY_VIOLATION',
        message: 'Operation blocked by policy',
        policy_name: 'Frontend never depends on backend',
        rule_type: 'forbidden_label_dependency',
        severity: 'hard',
        suggestion: 'Remove the dependency',
      } satisfies PolicyViolationDetail,
    })

    expect(wrapper.find('[data-testid="violation-panel"]').text()).toContain(
      'Policy: Frontend never depends on backend',
    )
  })

  it('renders the circular dependency message for CIRCULAR_DEPENDENCY errors', () => {
    const wrapper = mountModal({
      error: {
        code: 'CIRCULAR_DEPENDENCY',
        message: "Adding dependency from 'a' to 'b' would create a cycle: b -> a",
        cycle_path: ['b', 'a'],
      } satisfies PolicyViolationDetail,
    })

    const panel = wrapper.find('[data-testid="violation-panel"]')
    expect(panel.text()).toContain('Cannot create: circular dependency detected')
    expect(panel.text()).toContain("would create a cycle: b -> a")
  })

  it('emits create with the selected relationship type', async () => {
    const wrapper = mountModal({ error: null })

    const confirm = wrapper.findAll('button').find((b) => b.text().trim() === 'Create')
    expect(confirm).toBeTruthy()
    await confirm!.trigger('click')

    expect(wrapper.emitted('create')).toHaveLength(1)
    expect(wrapper.emitted('create')![0]).toEqual(['DEPENDS_ON'])
  })
})
