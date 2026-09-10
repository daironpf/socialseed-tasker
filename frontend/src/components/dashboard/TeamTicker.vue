<template>
  <div class="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 overflow-hidden">
    <div class="relative flex overflow-x-hidden">
      <div class="animate-marquee flex whitespace-nowrap gap-3 items-center py-1 px-2">
        <div
          v-for="(member, i) in [...teamMembers, ...teamMembers]"
          :key="'a-' + i"
          class="flex items-center gap-1.5 shrink-0"
        >
          <span class="text-xs">{{ member.avatar }}</span>
          <span
            class="text-[11px] font-medium"
            :class="member.isActive ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'"
          >
            {{ member.username }}
          </span>
          <span
            v-if="member.isActive"
            class="relative flex h-1.5 w-1.5"
          >
            <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex h-1.5 w-1.5 rounded-full bg-green-500"></span>
          </span>
          <span v-if="i < teamMembers.length * 2 - 1" class="text-gray-300 dark:text-gray-600 mx-1">·</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useIssuesStore } from '@/stores/issuesStore'

const issuesStore = useIssuesStore()

const teamMembers = computed(() => {
  const members = [
    { id: 'human-001', username: 'Pedro', avatar: '👨‍💻' },
    { id: 'human-002', username: 'Juan', avatar: '👨‍💻' },
    { id: 'human-003', username: 'Manolo', avatar: '👨‍💻' },
    { id: 'agent-001', username: 'Architect', avatar: '🤖' },
    { id: 'agent-002', username: 'Frontend', avatar: '🤖' },
    { id: 'agent-003', username: 'Backend', avatar: '🤖' },
    { id: 'agent-004', username: 'QA', avatar: '🤖' },
    { id: 'agent-005', username: 'DevOps', avatar: '🤖' },
  ]

  const activeIssues = issuesStore.issues.filter(i => i.status === 'IN_PROGRESS')

  return members.map(m => ({
    ...m,
    isActive: activeIssues.length > 0 && (m.id === 'human-001' || m.id === 'human-002' || m.id === 'agent-001' || m.id === 'agent-003'),
  }))
})
</script>

<style scoped>
@keyframes marquee {
  0% { transform: translateX(0%); }
  100% { transform: translateX(-50%); }
}
.animate-marquee {
  animation: marquee 25s linear infinite;
}
.animate-marquee:hover {
  animation-play-state: paused;
}
</style>
