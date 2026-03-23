<template>
  <section class="card form-card">
    <div class="card-head">
      <p class="eyebrow">Input</p>
      <h2>Start a Research Run</h2>
    </div>

    <form class="topic-form" @submit.prevent="emit('submit')">
      <label for="topic">Research topic</label>
      <textarea
        id="topic"
        :value="topic"
        rows="4"
        placeholder="Example: retrieval-augmented generation for biomedical QA"
        :disabled="isRunning"
        @input="onTopicInput"
      />

      <p v-if="validationError" class="warning">{{ validationError }}</p>

      <div class="actions">
        <button class="btn btn-primary" type="submit" :disabled="!canSubmit">
          {{ isRunning ? "Running..." : "Start Research" }}
        </button>
        <button
          class="btn btn-ghost"
          type="button"
          :disabled="!isRunning"
          @click="emit('cancel')"
        >
          Cancel
        </button>
        <button
          class="btn btn-muted"
          type="button"
          :disabled="isRunning && !isCancelled"
          @click="emit('reset')"
        >
          Reset
        </button>
      </div>
    </form>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  topic: string;
  validationError: string;
  canSubmit: boolean;
  isRunning: boolean;
  isCancelled: boolean;
}>();

const emit = defineEmits<{
  submit: [];
  cancel: [];
  reset: [];
  "update:topic": [value: string];
}>();

const onTopicInput = (event: Event) => {
  const target = event.target as HTMLTextAreaElement;
  emit("update:topic", target.value);
};
</script>

<style scoped>
.card {
  background: linear-gradient(
    160deg,
    rgba(255, 255, 255, 0.95),
    rgba(246, 250, 255, 0.86)
  );
  border: 1px solid rgba(26, 33, 52, 0.12);
  border-radius: 20px;
  padding: 1.15rem;
  box-shadow: 0 10px 26px rgba(17, 26, 43, 0.08);
}

.card-head {
  margin-bottom: 0.85rem;
}

.eyebrow {
  margin: 0;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #7a3f00;
  font-weight: 700;
}

h2 {
  margin: 0.25rem 0 0;
  font-size: clamp(1.1rem, 2vw, 1.35rem);
}

.topic-form {
  display: grid;
  gap: 0.7rem;
}

label {
  font-size: 0.9rem;
  font-weight: 700;
}

textarea {
  width: 100%;
  border: 1px solid rgba(22, 34, 57, 0.2);
  border-radius: 12px;
  padding: 0.75rem 0.8rem;
  resize: vertical;
  min-height: 92px;
  font: inherit;
  color: inherit;
  background: #fffefb;
}

textarea:focus-visible {
  outline: 2px solid rgba(0, 125, 128, 0.4);
  outline-offset: 1px;
}

.warning {
  margin: 0;
  color: #9a3412;
  font-size: 0.86rem;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.btn {
  border: 0;
  border-radius: 999px;
  padding: 0.56rem 0.96rem;
  font-weight: 700;
  font-size: 0.88rem;
  cursor: pointer;
  transition:
    transform 140ms ease,
    opacity 140ms ease;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.btn:not(:disabled):hover {
  transform: translateY(-1px);
}

.btn-primary {
  color: #f4faff;
  background: linear-gradient(90deg, #194f84 0%, #036f73 100%);
}

.btn-ghost {
  color: #0f2b4e;
  border: 1px solid rgba(15, 43, 78, 0.2);
  background: #f7fbff;
}

.btn-muted {
  color: #4f4f62;
  border: 1px solid rgba(79, 79, 98, 0.2);
  background: #f7f7fc;
}
</style>
