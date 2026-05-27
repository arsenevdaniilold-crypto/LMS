<template>
  <div class="container page">
    <div class="title-kicker">Настройки пользователя</div>
    <h1 class="page-title">Профиль</h1>
    <div class="title-line"></div>

    <div v-if="!auth.user" class="card muted">Загрузка…</div>

    <div v-else class="profile-grid reveal">
      <!-- Avatar card -->
      <div class="card avatar-card">
        <div class="avatar-preview">
          <img
            v-if="previewSrc"
            :src="previewSrc"
            :alt="auth.user.username"
            class="avatar-img"
          />
          <span v-else class="avatar-initial">
            {{ (auth.user.username || '?').charAt(0).toUpperCase() }}
          </span>
        </div>

        <div class="profile-name">{{ auth.user.username }}</div>
        <div class="profile-email muted">{{ auth.user.email }}</div>

        <div class="badges" v-if="auth.user.is_admin" style="margin-top: 14px; justify-content: center">
          <span class="badge badge-admin">администратор</span>
        </div>

        <div class="avatar-actions">
          <label class="btn-primary upload-btn">
            <input
              type="file"
              accept="image/png,image/jpeg"
              @change="onPickFile"
              :disabled="uploading"
            />
            {{ uploading ? 'Загружаем…' : 'Загрузить фото' }}
          </label>
          <button
            v-if="auth.user.avatar_url"
            class="btn-soft"
            :disabled="uploading"
            @click="onDeleteAvatar"
          >
            Удалить
          </button>
        </div>
        <p class="muted upload-hint">JPG или PNG, до 5 МБ</p>

        <!-- External URL alternative -->
        <div class="avatar-url-block">
          <div class="form-group" style="margin-bottom: 8px; text-align: left">
            <label>URL аватара (внешний)</label>
            <input v-model="avatarUrl" placeholder="https://..." :disabled="avatarSaving" />
          </div>
          <p class="muted url-hint">альтернатива загрузке файла</p>
          <button
            class="btn-ghost url-apply-btn"
            :disabled="avatarSaving || avatarUrl === (auth.user.avatar_url || '')"
            @click="onSaveAvatarUrl"
          >
            {{ avatarSaving ? 'Сохраняем…' : 'Применить URL' }}
          </button>
        </div>

        <p v-if="uploadError" class="error-text">{{ uploadError }}</p>
      </div>

      <!-- Info form -->
      <div class="card info-card">
        <h2 class="section-title">Основные данные</h2>

        <div class="form-group">
          <label>Email</label>
          <input :value="auth.user.email" disabled />
        </div>

        <div class="form-group">
          <label>Имя пользователя</label>
          <input v-model="username" :class="{ 'has-error': usernameError }" />
          <div v-if="usernameError" class="error-text">{{ usernameError }}</div>
        </div>

        <div v-if="error" class="error-text">{{ error }}</div>
        <div v-if="success" class="success-text">{{ success }}</div>

        <button class="btn-primary" :disabled="saving" @click="onSave">
          {{ saving ? 'Сохраняем…' : 'Сохранить изменения' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useAuthStore } from '@/shared/stores/authStore'
import { updateMe, uploadAvatar, deleteAvatar } from '@/shared/api/users'
import { extractError } from '@/shared/api/errors'

const auth = useAuthStore()
const username = ref('')
const avatarUrl = ref('')
const usernameError = ref('')
const error = ref('')
const success = ref('')
const saving = ref(false)

const uploading = ref(false)
const uploadError = ref('')
const localPreview = ref<string | null>(null)
const avatarSaving = ref(false)

watch(
  () => auth.user,
  (u) => {
    if (u) {
      username.value = u.username
      avatarUrl.value = u.avatar_url || ''
    }
  },
  { immediate: true },
)

const previewSrc = computed(() => {
  // local preview (just-picked file, not yet uploaded) takes priority
  if (localPreview.value) return localPreview.value
  return auth.user?.avatar_url || null
})

async function onPickFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  uploadError.value = ''
  // Show local preview immediately for instant feedback
  localPreview.value = URL.createObjectURL(file)

  uploading.value = true
  try {
    await uploadAvatar(file)
    await auth.fetchMe()  // refresh global user (updates topbar avatar in realtime)
    // Now avatar.url is the new presigned URL — drop local preview
    if (localPreview.value) {
      URL.revokeObjectURL(localPreview.value)
      localPreview.value = null
    }
    success.value = 'Фото обновлено'
    setTimeout(() => (success.value = ''), 2500)
  } catch (e) {
    uploadError.value = extractError(e)
    // Revert local preview on error
    if (localPreview.value) {
      URL.revokeObjectURL(localPreview.value)
      localPreview.value = null
    }
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function onDeleteAvatar() {
  if (!confirm('Удалить фото профиля?')) return
  uploadError.value = ''
  uploading.value = true
  try {
    await deleteAvatar()
    await auth.fetchMe()
    avatarUrl.value = ''
  } catch (e) {
    uploadError.value = extractError(e)
  } finally {
    uploading.value = false
  }
}

async function onSave() {
  error.value = ''
  success.value = ''
  usernameError.value = ''
  const name = username.value.trim()
  if (name.length < 2 || name.length > 100) {
    usernameError.value = 'От 2 до 100 символов'
    return
  }
  saving.value = true
  try {
    await updateMe({ username: name })
    await auth.fetchMe()
    success.value = 'Сохранено'
    setTimeout(() => (success.value = ''), 2500)
  } catch (e) {
    error.value = extractError(e)
  } finally {
    saving.value = false
  }
}

async function onSaveAvatarUrl() {
  uploadError.value = ''
  avatarSaving.value = true
  try {
    await updateMe({ avatar_url: avatarUrl.value.trim() || null })
    await auth.fetchMe()
    success.value = 'Аватар обновлён'
    setTimeout(() => (success.value = ''), 2500)
  } catch (e) {
    uploadError.value = extractError(e)
  } finally {
    avatarSaving.value = false
  }
}
</script>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 24px;
  align-items: start;
}

/* ---------- Avatar card ---------- */
.avatar-card {
  text-align: center;
  padding: 32px 24px;
}
.avatar-preview {
  width: 140px;
  height: 140px;
  margin: 0 auto 18px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: var(--shadow);
  position: relative;
}
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-initial {
  font-family: var(--font-display);
  font-size: 60px;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.profile-name {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 4px;
}
.profile-email {
  font-size: 14px;
}

.avatar-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-top: 22px;
}
.upload-btn {
  position: relative;
  overflow: hidden;
  cursor: pointer;
}
.upload-btn input[type="file"] {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  width: 100%;
  height: 100%;
}
.upload-hint {
  font-size: 12.5px;
  margin-top: 10px;
}

/* External-URL block — sits inside avatar card, separated by a hairline */
.avatar-url-block {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--color-border);
}
.url-hint {
  font-size: 12px;
  text-align: left;
  margin-top: 4px;
  margin-bottom: 12px;
}
.url-apply-btn {
  width: 100%;
  font-size: 13px;
  padding: 10px 14px;
}

/* ---------- Info card ---------- */
.info-card {
  padding: 32px 30px;
}
.section-title {
  margin-bottom: 22px;
}
.hint {
  font-size: 12.5px;
  margin-top: 6px;
}
.success-text {
  color: var(--color-success);
  background: var(--color-success-soft);
  padding: 10px 14px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 14px;
}

/* ---------- Responsive ---------- */
@media (max-width: 900px) {
  .profile-grid { grid-template-columns: 1fr; }
}
</style>
