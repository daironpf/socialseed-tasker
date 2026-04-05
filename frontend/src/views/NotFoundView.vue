<template>
  <div class="flex items-center justify-center min-h-screen">
    <div class="text-center">
      <h1 class="text-4xl font-bold text-gray-900 dark:text-gray-100">404</h1>
      <p class="mt-2 text-gray-500 dark:text-gray-400">Page not found</p>
      <RouterLink to="/board" class="mt-4 inline-block text-brand-600 hover:text-brand-700 dark:text-brand-400">
        Go to Board
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>
