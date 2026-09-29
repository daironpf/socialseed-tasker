<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('mcp.title') }}</h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ t('mcp.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-3">
        <span
          v-if="mcpStore.source === 'live'"
          class="inline-flex items-center gap-1.5 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-700 dark:bg-green-900/30 dark:text-green-400"
        >
          <span class="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse"></span>
          {{ t('mcp.dataLive') }}
        </span>
        <span
          v-else
          class="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
        >
          {{ t('mcp.dataMock') }}
        </span>
        <div class="flex items-center gap-2">
          <span
            class="h-2.5 w-2.5 rounded-full"
            :class="mcpStore.streamConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'"
          ></span>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ mcpStore.streamConnected ? t('mcp.streamLive') : t('mcp.streamOff') }}
          </span>
        </div>
        <button
          class="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="toggleStream"
        >
          {{ mcpStore.streamConnected ? t('mcp.stopStream') : t('mcp.startStream') }}
        </button>
        <button
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
          @click="mcpStore.fetchSessions()"
        >
          {{ t('mcp.refresh') }}
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="mcpStore.loading" class="flex items-center justify-center py-20">
      <LoadingSpinner />
    </div>

    <template v-else>
      <!-- Metrics Cards -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('mcp.totalSessions') }}</span>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <svg class="h-4 w-4 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </span>
          </div>
          <p class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{{ mcpStore.metrics.totalSessions }}</p>
          <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ t('mcp.allConnections') }}</p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('mcp.activeSessions') }}</span>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30">
              <svg class="h-4 w-4 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a5 5 0 010-7.07m7.072 0a5 5 0 010 7.07M13 12a1 1 0 11-2 0 1 1 0 012 0z" />
              </svg>
            </span>
          </div>
          <p class="mt-2 text-3xl font-bold text-green-600 dark:text-green-400">{{ mcpStore.metrics.activeSessions }}</p>
          <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ t('mcp.currentlyConnected') }}</p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('mcp.contextConsumed') }}</span>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30">
              <svg class="h-4 w-4 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
            </span>
          </div>
          <p class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{{ mcpStore.formatBytes(mcpStore.metrics.totalContextConsumed) }}</p>
          <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ t('mcp.acrossAllSessions') }}</p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('mcp.cypherQueries') }}</span>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <svg class="h-4 w-4 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c-1.306 0-2.417.835-2.83 2M9 14a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </span>
          </div>
          <p class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{{ mcpStore.metrics.totalCypherQueries.toLocaleString() }}</p>
          <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ t('mcp.avgPerMin', { rate: mcpStore.metrics.avgQueriesPerMin.toFixed(1) }) }}</p>
        </div>
      </div>

      <!-- Backend error -->
      <div
        v-if="mcpStore.error"
        role="alert"
        class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300"
      >
        <span class="font-semibold">{{ t('common.error') }}:</span> {{ mcpStore.error }}
      </div>

      <!-- MCP Servers -->
      <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('mcp.servers') }}</h3>
          <span class="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-semibold text-gray-600 dark:bg-gray-700 dark:text-gray-300">
            {{ mcpStore.servers.length }}
          </span>
        </div>
        <div v-if="mcpStore.servers.length === 0" class="px-6 py-8 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('mcp.noServers') }}</p>
        </div>
        <div v-else class="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="server in mcpStore.servers"
            :key="server.id"
            class="rounded-lg border border-gray-200 p-3 dark:border-gray-700"
          >
            <div class="flex items-center justify-between gap-2">
              <p class="truncate text-sm font-semibold text-gray-900 dark:text-white">{{ server.name }}</p>
              <span
                class="rounded-full px-2 py-0.5 text-[10px] font-bold"
                :class="server.status === 'online'
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'"
              >
                {{ server.status }}
              </span>
            </div>
            <p class="mt-0.5 truncate font-mono text-[10px] text-gray-500 dark:text-gray-400">
              {{ server.url ?? server.transport }}
            </p>
            <div class="mt-2 flex flex-wrap gap-1">
              <span
                v-for="tool in server.tools.slice(0, 4)"
                :key="tool"
                class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-400"
              >
                {{ tool }}
              </span>
              <span
                v-if="server.tools.length > 4"
                class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500 dark:bg-gray-700 dark:text-gray-400"
              >
                +{{ server.tools.length - 4 }}
              </span>
            </div>
            <p class="mt-2 text-[10px] text-gray-400 dark:text-gray-500">
              {{ t('mcp.lastSeen') }}: {{ formatTimestamp(server.lastSeen) }}
            </p>
          </div>
        </div>
      </div>

      <!-- Tool Calls: live feed + per-tool latency metrics -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- Tool call feed -->
        <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
            <div class="flex items-center gap-2">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('mcp.toolCalls') }}</h3>
              <span
                v-if="mcpStore.source === 'live' && mcpStore.streamConnected"
                class="h-2 w-2 rounded-full bg-green-500 animate-pulse"
              ></span>
            </div>
            <span class="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-semibold text-gray-600 dark:bg-gray-700 dark:text-gray-300">
              {{ mcpStore.toolCalls.length }}
            </span>
          </div>
          <div v-if="mcpStore.toolCalls.length === 0" class="px-6 py-8 text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('mcp.noToolCalls') }}</p>
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100 dark:border-gray-700">
                  <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.tool') }}</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.status') }}</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.duration') }}</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.startedAt') }}</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.actions') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50 dark:divide-gray-700/50">
                <tr
                  v-for="call in mcpStore.toolCalls.slice(0, 20)"
                  :key="call.id"
                  class="transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/30"
                >
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                      <span class="font-mono text-xs font-semibold text-gray-900 dark:text-white">{{ call.tool }}</span>
                      <span
                        v-if="call.rerunOf"
                        class="rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-bold text-purple-700 dark:bg-purple-900/30 dark:text-purple-400"
                        :title="t('mcp.rerunOf')"
                      >
                        &#8635;
                      </span>
                    </div>
                    <p v-if="call.server" class="text-[10px] text-gray-400 dark:text-gray-500">{{ call.server }}</p>
                  </td>
                  <td class="px-4 py-3">
                    <span
                      class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                      :class="mcpStore.getCallStatusColor(call.status)"
                    >
                      {{ t(`mcp.callStatuses.${call.status}`) }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-right">
                    <span
                      class="text-sm"
                      :class="call.durationMs !== null && call.durationMs > 800
                        ? 'font-semibold text-amber-600 dark:text-amber-400'
                        : 'text-gray-700 dark:text-gray-300'"
                    >
                      {{ call.durationMs !== null ? `${call.durationMs} ms` : '-' }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
                    {{ formatTimestamp(call.startedAt) }}
                  </td>
                  <td class="px-4 py-3">
                    <div class="flex items-center justify-end gap-1">
                      <button
                        class="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                        :aria-label="t('mcp.viewPayload')"
                        :title="t('mcp.viewPayload')"
                        @click="openPayload(call)"
                      >
                        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      </button>
                      <button
                        class="rounded-lg p-1.5 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20 disabled:opacity-50"
                        :aria-label="t('mcp.rerun')"
                        :title="t('mcp.rerun')"
                        :disabled="rerunningId !== null"
                        @click="handleRerun(call.id)"
                      >
                        <svg
                          class="h-4 w-4"
                          :class="{ 'animate-spin': rerunningId === call.id }"
                          fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                        >
                          <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Per-tool latency metrics -->
        <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          <div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('mcp.latency') }}</h3>
          </div>
          <div v-if="mcpStore.toolMetrics.length === 0" class="px-6 py-8 text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('mcp.noToolCalls') }}</p>
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100 dark:border-gray-700">
                  <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.tool') }}</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.calls') }}</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.successes') }}</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.errors') }}</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.avg') }}</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.max') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50 dark:divide-gray-700/50">
                <tr
                  v-for="metric in mcpStore.toolMetrics"
                  :key="metric.tool"
                  class="transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/30"
                >
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                      <span class="font-mono text-xs font-semibold text-gray-900 dark:text-white">{{ metric.tool }}</span>
                      <span
                        v-if="metric.slow"
                        class="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                      >
                        {{ t('mcp.slow') }}
                      </span>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ metric.calls }}</td>
                  <td class="px-4 py-3 text-right text-sm text-green-600 dark:text-green-400">{{ metric.successes }}</td>
                  <td class="px-4 py-3 text-right text-sm" :class="metric.errors > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'">
                    {{ metric.errors }}
                  </td>
                  <td class="px-4 py-3 text-right text-sm" :class="metric.slow ? 'font-semibold text-amber-600 dark:text-amber-400' : 'text-gray-700 dark:text-gray-300'">
                    {{ metric.avgMs }} ms
                  </td>
                  <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ metric.maxMs }} ms</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Sessions Matrix -->
      <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('mcp.sessionMatrix') }}</h3>
          <div class="flex items-center gap-2">
            <button
              v-for="filter in statusFilters"
              :key="filter.value"
              class="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
              :class="activeFilter === filter.value
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'"
              @click="activeFilter = filter.value"
            >
              {{ filter.label }}
              <span
                v-if="filter.count > 0"
                class="ml-1 rounded-full bg-gray-200 px-1.5 text-[10px] dark:bg-gray-600"
              >{{ filter.count }}</span>
            </button>
          </div>
        </div>

        <div v-if="filteredSessions.length === 0" class="px-6 py-12 text-center">
          <svg class="mx-auto h-12 w-12 text-gray-500 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          <p class="mt-3 text-sm text-gray-500 dark:text-gray-400">{{ t('mcp.noSessions') }}</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100 dark:border-gray-700">
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.client') }}</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.status') }}</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.uptime') }}</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.context') }}</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.queries') }}</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.tools') }}</th>
                <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.actions') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50 dark:divide-gray-700/50">
              <tr
                v-for="session in filteredSessions"
                :key="session.id"
                class="transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/30"
              >
                <!-- Client -->
                <td class="px-6 py-4">
                  <div class="flex items-center gap-3">
                    <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 text-lg dark:bg-gray-700">
                      {{ mcpStore.getClientIcon(session.clientType) }}
                    </div>
                    <div>
                      <p class="text-sm font-semibold text-gray-900 dark:text-white">{{ session.clientName }}</p>
                      <p class="text-xs text-gray-500 dark:text-gray-400">{{ session.id }}</p>
                    </div>
                  </div>
                </td>

                <!-- Status -->
                <td class="px-6 py-4">
                  <span
                    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                    :class="mcpStore.getStatusColor(session.status)"
                  >
                    <span
                      class="mr-1.5 h-1.5 w-1.5 rounded-full"
                      :class="{
                        'bg-green-500': session.status === 'active',
                        'bg-amber-500': session.status === 'paused',
                        'bg-red-500': session.status === 'revoked',
                        'bg-gray-400': session.status === 'idle',
                      }"
                    ></span>
                    {{ t(`mcp.statuses.${session.status}`) }}
                  </span>
                </td>

                <!-- Uptime -->
                <td class="px-6 py-4">
                  <span class="text-sm text-gray-700 dark:text-gray-300">{{ mcpStore.formatUptime(session.uptime) }}</span>
                </td>

                <!-- Context -->
                <td class="px-6 py-4">
                  <div class="w-32">
                    <div class="flex items-center justify-between text-xs">
                      <span class="text-gray-700 dark:text-gray-300">{{ mcpStore.formatBytes(session.contextConsumed) }}</span>
                      <span class="text-gray-500 dark:text-gray-400">{{ Math.round((session.contextConsumed / session.contextLimit) * 100) }}%</span>
                    </div>
                    <div class="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-600">
                      <div
                        class="h-full rounded-full transition-all duration-500"
                        :class="getContextBarColor(session)"
                        :style="{ width: `${(session.contextConsumed / session.contextLimit) * 100}%` }"
                      ></div>
                    </div>
                  </div>
                </td>

                <!-- Cypher Queries -->
                <td class="px-6 py-4">
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">{{ session.cypherQueries.toLocaleString() }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">
                      {{ session.status === 'active' ? `${session.cypherQueriesPerMin} ${t('mcp.perMin')}` : t('mcp.idle') }}
                    </p>
                  </div>
                </td>

                <!-- Tools -->
                <td class="px-6 py-4">
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="tool in session.toolsUsed.slice(0, 3)"
                      :key="tool"
                      class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-400"
                    >
                      {{ tool }}
                    </span>
                    <span
                      v-if="session.toolsUsed.length > 3"
                      class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500 dark:bg-gray-700 dark:text-gray-400"
                    >
                      +{{ session.toolsUsed.length - 3 }}
                    </span>
                  </div>
                </td>

                <!-- Actions -->
                <td class="px-6 py-4">
                  <div class="flex items-center justify-end gap-1">
                    <button
                      v-if="session.status === 'active'"
                      class="rounded-lg p-1.5 text-amber-600 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20"
                      :aria-label="t('mcp.pause')"
                      :title="t('mcp.pause')"
                      @click="handlePause(session.id)"
                    >
                      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                    <button
                      v-if="session.status === 'paused'"
                      class="rounded-lg p-1.5 text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/20"
                      :aria-label="t('mcp.resume')"
                      :title="t('mcp.resume')"
                      @click="handleResume(session.id)"
                    >
                      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                    <button
                      v-if="session.status !== 'revoked'"
                      class="rounded-lg p-1.5 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                      :aria-label="t('mcp.revoke')"
                      :title="t('mcp.revoke')"
                      @click="handleRevoke(session.id)"
                    >
                      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Confirm Modal -->
    <div
      v-if="confirmModal.show"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="confirmModal.show = false"
    >
      <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ confirmModal.title }}</h3>
        <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">{{ confirmModal.message }}</p>
        <div class="mt-6 flex justify-end gap-3">
          <button
            class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            @click="confirmModal.show = false"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            class="rounded-lg px-4 py-2 text-sm font-medium text-white"
            :class="confirmModal.danger ? 'bg-red-600 hover:bg-red-700' : 'bg-amber-600 hover:bg-amber-700'"
            @click="confirmModal.onConfirm(); confirmModal.show = false"
          >
            {{ confirmModal.confirmLabel }}
          </button>
        </div>
      </div>
    </div>
    <!-- Payload Inspection Modal -->
    <div
      v-if="selectedCall"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="selectedCall = null"
    >
      <div class="w-full max-w-xl rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800" role="dialog" :aria-label="t('mcp.payload')">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ t('mcp.payload') }}
            <span class="ml-2 font-mono text-sm text-blue-600 dark:text-blue-400">{{ selectedCall.tool }}</span>
          </h3>
          <span
            class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
            :class="mcpStore.getCallStatusColor(selectedCall.status)"
          >
            {{ t(`mcp.callStatuses.${selectedCall.status}`) }}
          </span>
        </div>

        <div class="mt-4 space-y-3">
          <div>
            <p class="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
              {{ t('mcp.argumentsLabel') }}
            </p>
            <pre class="max-h-48 overflow-x-auto whitespace-pre-wrap rounded-lg bg-gray-50 p-3 font-mono text-xs text-gray-700 dark:bg-gray-900 dark:text-gray-300">{{ formatPayload(selectedCall.arguments) }}</pre>
          </div>
          <div v-if="selectedCall.resultSummary">
            <p class="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
              {{ t('mcp.resultLabel') }}
            </p>
            <pre class="max-h-32 overflow-x-auto whitespace-pre-wrap rounded-lg bg-green-50 p-3 font-mono text-xs text-green-800 dark:bg-green-900/20 dark:text-green-300">{{ selectedCall.resultSummary }}</pre>
          </div>
          <div v-if="selectedCall.error">
            <p class="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
              {{ t('mcp.errorLabel') }}
            </p>
            <pre class="max-h-32 overflow-x-auto whitespace-pre-wrap rounded-lg bg-red-50 p-3 font-mono text-xs text-red-700 dark:bg-red-900/20 dark:text-red-300">{{ selectedCall.error }}</pre>
          </div>
          <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>{{ t('mcp.startedAt') }}: {{ formatTimestamp(selectedCall.startedAt) }}</span>
            <span v-if="selectedCall.durationMs !== null">{{ t('mcp.duration') }}: {{ selectedCall.durationMs }} ms</span>
          </div>
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <button
            class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            @click="selectedCall = null"
          >
            {{ t('common.close') }}
          </button>
          <button
            class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
            :disabled="rerunningId !== null"
            @click="handleRerun(selectedCall.id)"
          >
            <span v-if="rerunningId === selectedCall.id" class="flex items-center gap-1.5">
              <span class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
              {{ t('mcp.rerunning') }}
            </span>
            <span v-else>{{ t('mcp.rerun') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMcpStore } from '@/stores/mcpStore'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import type { MCPSessionStatus, MCPToolCall } from '@/types/mcp'

const { t } = useI18n()
const mcpStore = useMcpStore()

const activeFilter = ref<'all' | MCPSessionStatus>('all')
const selectedCall = ref<MCPToolCall | null>(null)
const rerunningId = ref<string | null>(null)

const confirmModal = ref<{
  show: boolean
  title: string
  message: string
  confirmLabel: string
  danger: boolean
  onConfirm: () => void
}>({
  show: false,
  title: '',
  message: '',
  confirmLabel: '',
  danger: false,
  onConfirm: () => {},
})

const statusFilters = computed(() => [
  { value: 'all' as const, label: t('mcp.filterAll'), count: mcpStore.sessions.length },
  { value: 'active' as const, label: t('mcp.filterActive'), count: mcpStore.activeSessions.length },
  { value: 'paused' as const, label: t('mcp.filterPaused'), count: mcpStore.pausedSessions.length },
  { value: 'idle' as const, label: t('mcp.filterIdle'), count: mcpStore.idleSessions.length },
  { value: 'revoked' as const, label: t('mcp.filterRevoked'), count: mcpStore.revokedSessions.length },
])

const filteredSessions = computed(() => {
  if (activeFilter.value === 'all') return mcpStore.sessions
  return mcpStore.sessions.filter(s => s.status === activeFilter.value)
})

function getContextBarColor(session: { contextConsumed: number; contextLimit: number }): string {
  const pct = (session.contextConsumed / session.contextLimit) * 100
  if (pct >= 90) return 'bg-red-500'
  if (pct >= 70) return 'bg-amber-500'
  return 'bg-blue-500'
}

function handlePause(id: string) {
  confirmModal.value = {
    show: true,
    title: t('mcp.pauseSessionTitle'),
    message: t('mcp.pauseSessionMessage'),
    confirmLabel: t('mcp.pauseSessionConfirm'),
    danger: false,
    onConfirm: () => mcpStore.pauseSession(id),
  }
}

function handleResume(id: string) {
  mcpStore.resumeSession(id)
}

function handleRevoke(id: string) {
  confirmModal.value = {
    show: true,
    title: t('mcp.revokeSessionTitle'),
    message: t('mcp.revokeSessionMessage'),
    confirmLabel: t('mcp.revokeSessionConfirm'),
    danger: true,
    onConfirm: () => mcpStore.revokeSession(id),
  }
}

function toggleStream() {
  if (mcpStore.streamConnected) {
    mcpStore.stopStream()
  } else {
    mcpStore.startStream()
  }
}

function formatTimestamp(ts: string): string {
  if (!ts) return '-'
  const date = new Date(ts)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString()
}

function formatPayload(args: Record<string, unknown>): string {
  try {
    return JSON.stringify(args, null, 2)
  } catch {
    return String(args)
  }
}

function openPayload(call: MCPToolCall) {
  selectedCall.value = call
}

async function handleRerun(callId: string) {
  if (rerunningId.value) return
  rerunningId.value = callId
  try {
    const rerun = await mcpStore.rerunToolCall(callId)
    if (rerun && selectedCall.value && selectedCall.value.id === callId) {
      selectedCall.value = rerun
    }
  } finally {
    rerunningId.value = null
  }
}

onMounted(async () => {
  await mcpStore.fetchSessions()
  mcpStore.startStream()
})

onUnmounted(() => {
  mcpStore.stopStream()
})
</script>
