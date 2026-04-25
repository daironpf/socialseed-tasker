import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/board' },
    { path: '/board', name: 'Board', component: () => import('@/views/BoardView.vue') },
    { path: '/list', name: 'List', component: () => import('@/views/ListView.vue') },
    { path: '/graph', name: 'Graph', component: () => import('@/views/GraphView.vue') },
    { path: '/components', name: 'Components', component: () => import('@/views/ComponentsView.vue') },
    { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/NotFoundView.vue') },
  ],
})

router.afterEach(() => {
  window.scrollTo(0, 0)
})

export default router
