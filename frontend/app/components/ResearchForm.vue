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
    150deg,
    rgba(255, 255, 255, 0.78),
    rgba(244, 250, 255, 0.7)
  );
  border: 1px solid rgba(17, 31, 56, 0.14);
  border-radius: 1.28rem;
  padding: 1.1rem;
  box-shadow: 0 14px 26px rgba(17, 31, 56, 0.08);
  backdrop-filter: blur(8px);
}

.card-head {
  margin-bottom: 0.92rem;
}

.eyebrow {
  margin: 0;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.17em;
  color: #cf6129;
  font-weight: 700;
  font-family: "Space Grotesk", "Manrope", sans-serif;
}

h2 {
  margin: 0.3rem 0 0;
  font-family: "Sora", "Manrope", sans-serif;
  font-size: clamp(1.14rem, 2vw, 1.4rem);
  letter-spacing: -0.02em;
}

.topic-form {
  display: grid;
  gap: 0.78rem;
  min-width: 0;
}

label {
  font-size: 0.88rem;
  font-weight: 700;
  color: rgba(17, 31, 56, 0.9);
}

textarea {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  display: block;
  border: 1px solid rgba(17, 31, 56, 0.2);
  border-radius: 0.88rem;
  padding: 0.84rem 0.88rem;
  resize: vertical;
  min-height: 108px;
  font: inherit;
  color: rgba(17, 31, 56, 0.95);
  background: rgba(255, 255, 255, 0.82);
  transition:
    box-shadow 180ms ease,
    border-color 180ms ease,
    background-color 180ms ease;
}

textarea:focus-visible {
  outline: none;
  border-color: rgba(15, 143, 124, 0.62);
  box-shadow: 0 0 0 4px rgba(15, 143, 124, 0.18);
  background: rgba(255, 255, 255, 0.92);
}

.warning {
  margin: 0;
  color: #a93f1f;
  font-size: 0.86rem;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.58rem;
}

.btn {
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 0.56rem 1rem;
  font-weight: 700;
  font-size: 0.84rem;
  letter-spacing: 0.01em;
  cursor: pointer;
  transition:
    transform 140ms ease,
    opacity 140ms ease,
    box-shadow 140ms ease,
    background-color 140ms ease;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.btn:not(:disabled):hover {
  transform: translateY(-1px) scale(1.01);
}

.btn-primary {
  color: #f7fbff;
  background: linear-gradient(92deg, #0f5f96 0%, #0f8f7c 100%);
  box-shadow: 0 8px 16px rgba(15, 95, 150, 0.24);
}

.btn-ghost {
  color: #194168;
  border-color: rgba(25, 65, 104, 0.22);
  background: rgba(248, 252, 255, 0.76);
}

.btn-muted {
  color: #444b61;
  border-color: rgba(68, 75, 97, 0.2);
  background: rgba(248, 248, 252, 0.72);
}

@media (max-width: 850px) {
  .card {
    padding: 0.95rem;
  }
}
</style>
