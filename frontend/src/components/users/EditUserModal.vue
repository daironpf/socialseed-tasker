<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    @click.self="close"
  >
    <div class="w-full max-w-lg bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
      <div class="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-xl dark:bg-blue-900/30">
            {{ user?.avatar || '👤' }}
          </div>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ t('users.editUser') }}
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ form.username }}
            </p>
          </div>
        </div>
        <button
          @click="close"
          class="rounded-lg p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="p-4 space-y-4 max-h-[60vh] overflow-y-auto">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('users.username') }}
          </label>
          <input
            v-model="form.username"
            type="text"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('users.email') }}
          </label>
          <input
            v-model="form.email"
            type="email"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('users.role') }}
          </label>
          <select
            v-model="form.role"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          >
            <option v-for="role in visibleRoles" :key="role" :value="role">{{ roleLabel(role) }}</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('users.skills') }}
          </label>
          <div class="flex flex-wrap gap-2 mb-2">
            <span
              v-for="skill in form.skills"
              :key="skill"
              class="flex items-center gap-1 rounded-md bg-blue-100 px-2 py-1 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
            >
              {{ skill }}
              <button
                @click="removeSkill(skill)"
                :disabled="skillsBusy"
                class="ml-1 hover:text-blue-900 disabled:opacity-50 dark:hover:text-blue-200"
              >
                ×
              </button>
            </span>
          </div>
          <div class="flex gap-2">
            <input
              v-model="newSkill"
              @keyup.enter="addSkill"
              type="text"
              :placeholder="t('users.addSkill')"
              :disabled="skillsBusy"
              class="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-60 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            />
            <button
              type="button"
              :aria-label="t('users.addSkills')"
              :disabled="skillsBusy"
              @click="pickerOpen = true"
              class="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              +
            </button>
          </div>
          <div v-if="skillPicker.length" class="mt-2 flex flex-wrap items-center gap-1.5">
            <span class="text-[11px] text-gray-400 dark:text-gray-500">{{ t('users.skillSuggestions') }}:</span>
            <button
              v-for="s in skillPicker"
              :key="s.id"
              type="button"
              @click="pickSkill(s)"
              :disabled="skillsBusy"
              class="rounded-full border border-gray-200 px-2 py-0.5 text-[11px] text-gray-600 hover:border-blue-400 hover:text-blue-600 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:border-blue-500 dark:hover:text-blue-400"
            >
              + {{ s.name }}
            </button>
          </div>
          <p class="mt-1 text-[11px] text-gray-400 dark:text-gray-500">{{ t('users.skillNewHint') }}</p>
          <p v-if="skillsError" class="mt-1 text-[11px] text-rose-600 dark:text-rose-400">
            {{ skillsErrorText }}
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('users.avatar') }}
          </label>
          <div class="flex gap-2">
            <button
              v-for="avatar in avatarOptions"
              :key="avatar"
              @click="form.avatar = avatar"
              class="h-10 w-10 rounded-lg border-2 flex items-center justify-center text-xl transition-colors"
              :class="form.avatar === avatar ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30' : 'border-gray-200 hover:border-gray-300 dark:border-gray-700'"
            >
              {{ avatar }}
            </button>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-end gap-3 border-t border-gray-200 dark:border-gray-700 p-4">
        <button
          @click="close"
          class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          {{ t('users.cancel') }}
        </button>
        <button
          @click="save"
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          {{ t('users.saveChanges') }}
        </button>
      </div>
    </div>

    <!-- Floating multi-select picker opened by "+" (issue #577) -->
    <SkillPickerModal
      :show="pickerOpen"
      mode="human"
      :selected="form.skills"
      @close="pickerOpen = false"
      @apply="applyPickedSkills"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { isMockMode } from '@/api/client'
import { fetchSkills, resetCatalogsCache, type SkillCatalogItem } from '@/api/catalogsApi'
import { addUserSkill, removeUserSkill, fetchUserSkills, type UserSkill } from '@/api/userSkillsApi'
import SkillPickerModal from '@/components/users/SkillPickerModal.vue'
import { useUsersStore } from '@/stores/usersStore'
import type { User } from '@/types'

const { t } = useI18n()

interface Props {
  show: boolean
  user: User | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: User): void
}>()

const form = ref({
  username: '',
  email: '',
  role: 'developer',
  avatar: '👤',
  skills: [] as string[],
})

const newSkill = ref('')
const pickerOpen = ref(false)

const BASE_ROLES = ['lead-developer', 'developer', 'designer', 'manager', 'qa']
const REAL_ROLES = ['ADMIN', 'DEVELOPER', 'VIEWER']

// Real mode offers the seeded RBAC vocabulary; mock keeps the dataset roles.
// The user's current role is appended when it falls outside the base list (#556).
const visibleRoles = computed(() => {
  const base = isMockMode() ? BASE_ROLES : REAL_ROLES
  return base.includes(form.value.role) ? base : [...base, form.value.role]
})

function roleLabel(role: string): string {
  const labels: Record<string, string> = {
    ADMIN: t('users.adminRole'),
    DEVELOPER: t('users.developer'),
    VIEWER: t('users.viewerRole'),
    'lead-developer': t('users.leadDeveloper'),
    developer: t('users.developer'),
    designer: t('users.designer'),
    manager: t('users.manager'),
    qa: t('users.qa'),
  }
  return labels[role] || role
}

const avatarOptions = ['👤', '👩‍💻', '👨‍💻', '🧑‍💻', '👩‍🔬', '👨‍🔬', '👩‍🎨', '👨‍🎨', '👩‍💼', '👨‍💼', '🧑‍💼']

watch(() => props.user, (user) => {
  if (user) {
    form.value = {
      username: user.username,
      email: user.email,
      role: user.role,
      avatar: user.avatar,
      skills: [...user.skills],
    }
  }
}, { immediate: true })

// Skill picker (#576 UX fix): the native <datalist> never opens on the "+"
// button, only while typing in the input, so the catalog is rendered as
// visible clickable chips instead. Real mode reads GET /skills; mock derives
// the vocabulary from the skills already present on the mock users.
const skillSuggestions = ref<SkillCatalogItem[]>([])
const usersStore = useUsersStore()

async function loadSkillSuggestions() {
  if (isMockMode()) return
  try {
    skillSuggestions.value = await fetchSkills()
  } catch {
    // Picker degrades to free text without suggestions (#572).
  }
}

const skillPicker = computed(() => {
  const taken = new Set(form.value.skills.map(s => s.toLowerCase()))
  const query = newSkill.value.trim().toLowerCase()
  const pool = isMockMode()
    ? Array.from(new Set(usersStore.users.flatMap(u => u.skills))).map(name => ({ id: name.toLowerCase(), name }))
    : skillSuggestions.value.map(s => ({ id: s.id, name: s.name }))
  return pool
    .filter(s => !taken.has(s.name.toLowerCase()))
    .filter(s => !query || s.name.toLowerCase().includes(query))
    .slice(0, 12)
})

function pickSkill(s: { id: string; name: string }) {
  newSkill.value = s.name
  void addSkill()
}

// Real mode manages skills directly against /users/{id}/skills (#576): the
// chips read from user_skills, + assigns (find-or-create by name) and ×
// unlinks immediately, so no full PUT replace is needed. Mock keeps the
// local chips applied on save via the in-memory store.
const skillsBusy = ref(false)
const skillsError = ref<'add' | 'remove' | null>(null)
const assignedSkills = ref<UserSkill[]>([])

const skillsErrorText = computed(() =>
  skillsError.value === 'remove' ? t('users.skillRemoveError') : t('users.skillAddError'),
)

async function loadAssignedSkills() {
  if (isMockMode() || !props.user) return
  try {
    assignedSkills.value = await fetchUserSkills(props.user.id)
    form.value.skills = assignedSkills.value.map(item => item.name)
  } catch {
    // Degrade to the card's skills already copied into the form.
  }
}

watch(() => props.show, visible => {
  if (visible) {
    loadSkillSuggestions()
    void loadAssignedSkills()
  }
}, { immediate: true })

async function addSkill() {
  const skill = newSkill.value.trim()
  if (!skill) return
  if (!isMockMode() && props.user) {
    skillsBusy.value = true
    skillsError.value = null
    try {
      const item = await addUserSkill(props.user.id, skill)
      if (!assignedSkills.value.some(entry => entry.skill_id === item.skill_id)) {
        assignedSkills.value.push(item)
      }
      form.value.skills = assignedSkills.value.map(entry => entry.name).sort((a, b) => a.localeCompare(b))
      newSkill.value = ''
      resetCatalogsCache()
      void loadSkillSuggestions()
    } catch {
      skillsError.value = 'add'
    } finally {
      skillsBusy.value = false
    }
    return
  }
  if (!form.value.skills.includes(skill)) {
    form.value.skills.push(skill)
    newSkill.value = ''
  }
}

async function removeSkill(skill: string) {
  if (!isMockMode() && props.user) {
    skillsBusy.value = true
    skillsError.value = null
    try {
      const item = assignedSkills.value.find(entry => entry.name === skill)
      if (item) await removeUserSkill(props.user.id, item.skill_id)
      assignedSkills.value = assignedSkills.value.filter(entry => entry.name !== skill)
      form.value.skills = form.value.skills.filter(s => s !== skill)
    } catch {
      skillsError.value = 'remove'
    } finally {
      skillsBusy.value = false
    }
    return
  }
  form.value.skills = form.value.skills.filter(s => s !== skill)
}

// Apply the selection coming from the floating picker (#577): only the delta
// travels to POST/DELETE /users/{id}/skills, so untouched assignments never
// move. Mock keeps the local chips applied on save.
async function applyPickedSkills(names: string[]) {
  if (isMockMode() || !props.user) {
    form.value.skills = names
    return
  }
  const current = [...form.value.skills]
  const nextLower = new Set(names.map(name => name.toLowerCase()))
  const added = names.filter(name => !current.some(entry => entry.toLowerCase() === name.toLowerCase()))
  const removed = current.filter(entry => !nextLower.has(entry.toLowerCase()))

  skillsBusy.value = true
  skillsError.value = null
  try {
    for (const name of added) {
      const item = await addUserSkill(props.user.id, name)
      if (!assignedSkills.value.some(entry => entry.skill_id === item.skill_id)) {
        assignedSkills.value.push(item)
      }
    }
  } catch {
    skillsError.value = 'add'
  }
  if (!skillsError.value) {
    try {
      for (const name of removed) {
        const item = assignedSkills.value.find(
          entry => entry.name.toLowerCase() === name.toLowerCase(),
        )
        if (item) {
          await removeUserSkill(props.user.id, item.skill_id)
          assignedSkills.value = assignedSkills.value.filter(entry => entry.skill_id !== item.skill_id)
        }
      }
    } catch {
      skillsError.value = 'remove'
    }
  }
  // Rebuild from the assignments the server actually holds (partial failures
  // revert the chips that were not applied) and refresh the catalog chips.
  form.value.skills = assignedSkills.value.map(entry => entry.name).sort((a, b) => a.localeCompare(b))
  resetCatalogsCache()
  void loadSkillSuggestions()
  skillsBusy.value = false
}

function close() {
  emit('close')
}

function save() {
  // Only emit: the parent (UsersView) closes the modal after a successful
  // save so errors keep the form open (#566/#567). Closing unconditionally
  // here hid failed saves (e.g. a 429) behind an already-dismissed window.
  if (props.user) {
    emit('save', {
      ...props.user,
      ...form.value,
    })
  }
}
</script>
