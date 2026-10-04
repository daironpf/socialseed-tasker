import { describe, it, expect, vi } from 'vitest'
import { mountComponent } from '@/test/mount'
import App from '@/App.vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import MobileDrawer from '@/components/layout/MobileDrawer.vue'
import TeamTicker from '@/components/dashboard/TeamTicker.vue'
import FloatingChat from '@/components/chat/FloatingChat.vue'
import LoginScreen from '@/components/auth/LoginScreen.vue'
import CommandPalette from '@/components/ui/CommandPalette.vue'
import KeyboardShortcutsHelp from '@/components/ui/KeyboardShortcutsHelp.vue'
import ToastContainer from '@/components/ui/ToastContainer.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/setup' }),
  useRouter: () => ({ push: vi.fn() }),
  RouterView: { template: '<div data-testid="router-view" />' },
  RouterLink: { template: '<a><slot /></a>' },
}))

describe('App on /setup', () => {
  it('renders a bare shell without sidebar, header, ticker, chat or login', () => {
    const { wrapper } = mountComponent(App)

    expect(wrapper.findComponent(Sidebar).exists()).toBe(false)
    expect(wrapper.findComponent(AppHeader).exists()).toBe(false)
    expect(wrapper.findComponent(MobileDrawer).exists()).toBe(false)
    expect(wrapper.findComponent(TeamTicker).exists()).toBe(false)
    expect(wrapper.findComponent(FloatingChat).exists()).toBe(false)
    expect(wrapper.findComponent(CommandPalette).exists()).toBe(false)
    expect(wrapper.findComponent(KeyboardShortcutsHelp).exists()).toBe(false)
    expect(wrapper.findComponent(LoginScreen).exists()).toBe(false)

    expect(wrapper.find('header').exists()).toBe(false)
    expect(wrapper.find('aside').exists()).toBe(false)
    expect(wrapper.find('.animate-marquee').exists()).toBe(false)

    expect(wrapper.find('[data-testid="router-view"]').exists()).toBe(true)
    expect(wrapper.findComponent(ToastContainer).exists()).toBe(true)
    expect(wrapper.find('a[href="#main-content"]').exists()).toBe(true)
  })
})
