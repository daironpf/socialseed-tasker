<template>
  <div class="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 overflow-hidden">
    <div class="flex whitespace-nowrap overflow-hidden py-1 px-2">
      <div ref="track" class="flex shrink-0 animate-marquee gap-3 items-center min-w-max">
        <template v-for="member in teamMembers" :key="'a-' + member.id">
          <div class="flex items-center gap-1.5 shrink-0">
            <span class="text-xs">{{ member.avatar }}</span>
            <span
              class="text-[11px] font-medium"
              :class="member.isActive ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'"
            >
              {{ member.username }}
            </span>
            <span v-if="member.isActive" class="relative flex h-1.5 w-1.5">
              <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex h-1.5 w-1.5 rounded-full bg-green-500"></span>
            </span>
          </div>
          <span class="text-gray-300 dark:text-gray-600 mx-1">·</span>
        </template>
      </div>
      <div class="flex shrink-0 animate-marquee gap-3 items-center min-w-max ml-3">
        <template v-for="member in teamMembers" :key="'b-' + member.id">
          <div class="flex items-center gap-1.5 shrink-0">
            <span class="text-xs">{{ member.avatar }}</span>
            <span
              class="text-[11px] font-medium"
              :class="member.isActive ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'"
            >
              {{ member.username }}
            </span>
            <span v-if="member.isActive" class="relative flex h-1.5 w-1.5">
              <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex h-1.5 w-1.5 rounded-full bg-green-500"></span>
            </span>
          </div>
          <span class="text-gray-300 dark:text-gray-600 mx-1">·</span>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { fetchUsers } from '@/api/usersApi'

interface User {
  id: string
  username: string
  avatar: string
  type: string
  last_active?: string
}

const teamMembers = ref<{ id: string; username: string; avatar: string; isActive: boolean }[]>([])
const track = ref<HTMLElement | null>(null)
let interval: ReturnType<typeof setInterval> | null = null

async function loadUsers() {
  try {
    const users = await fetchUsers()
    const now = new Date()
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)

    teamMembers.value = (users as User[]).map(u => {
      let isActive = false
      if (u.last_active) {
        const lastActive = new Date(u.last_active)
        isActive = lastActive > oneDayAgo
      }
      return {
        id: u.id,
        username: u.username,
        avatar: u.avatar || '👤',
        isActive,
      }
    })
  } catch {
    // users fetch failed
  }
}

onMounted(() => {
  loadUsers()
  interval = setInterval(loadUsers, 10000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>

<style scoped>
@keyframes marquee {
  0% { transform: translateX(0%); }
  100% { transform: translateX(-100%); }
}
.animate-marquee {
  animation: marquee 20s linear infinite;
}
.animate-marquee:hover {
  animation-play-state: paused;
}
</style>
