<template>
  <div class="page-root">
    <main class="app-shell">
      <header class="hero">
        <p class="kicker">Agentic Literature Review</p>
        <h1>Research Console</h1>
        <p class="subtitle">
          Submit a topic, follow the six-step backend pipeline in real time, and
          view the generated literature review.
        </p>
        <p class="api-target">API target: {{ apiBaseUrl }}</p>
      </header>

      <section class="panel panel-form">
        <h2>1. Topic Input</h2>
        <p class="panel-note">
          Enter a topic and start a streaming research run.
        </p>
        <form @submit.prevent="startResearch">
          <label for="topic">Research topic</label>
          <textarea
            id="topic"
            rows="4"
            placeholder="Example: retrieval-augmented generation for biomedical QA"
            v-model="topic"
            :disabled="isRunning"
          />
          <p v-if="validationError" class="form-warning">
            {{ validationError }}
          </p>
          <div class="actions-row">
            <button type="submit" :disabled="!canSubmit">
              {{ isRunning ? "Running..." : "Start Research" }}
            </button>
            <button
              type="button"
              :disabled="!isRunning"
              @click="cancelResearch"
            >
              Cancel
            </button>
            <button
              type="button"
              class="btn-reset"
              :disabled="isRunning && !isCancelled"
              @click="resetResearch"
            >
              Reset
            </button>
          </div>
        </form>
      </section>

      <section class="panel panel-progress">
        <h2>2. Live Progress</h2>
        <p class="panel-note">{{ latestMessage }}</p>
        <div class="progress-wrap" aria-hidden="true">
          <div class="progress-bar" :style="{ width: `${progressPercent}%` }" />
        </div>
        <p class="progress-meta">
          Step {{ currentStep || 0 }} / {{ totalSteps }}
        </p>
        <ol class="step-list">
          <li
            v-for="step in pipelineSteps"
            :key="step.index"
            :class="{
              done: currentStep > step.index,
              active: currentStep === step.index,
            }"
          >
            {{ step.label }}
          </li>
        </ol>

        <ul class="event-list" v-if="statusHistory.length">
          <li
            v-for="entry in statusHistory"
            :key="`${entry.timestamp}-${entry.step}`"
          >
            [{{ entry.step }}/{{ entry.total }}] {{ entry.message }}
          </li>
        </ul>
      </section>

      <section class="panel panel-result">
        <h2>3. Generated Review</h2>
        <p class="panel-note">Final markdown payload from the result event.</p>
        <article class="result-placeholder" v-if="markdown">
          <pre>{{ markdown }}</pre>
        </article>
        <article class="result-placeholder" v-else>
          <h3>Output will appear here</h3>
          <p>
            Run a research topic to receive streamed progress and final output.
          </p>
        </article>
      </section>

      <section class="panel panel-status" role="status" aria-live="polite">
        <h2>4. Error and System Status</h2>
        <p class="panel-note" v-if="errorMessage">{{ errorMessage }}</p>
        <p class="panel-note" v-else-if="isCancelled">
          Research run cancelled.
        </p>
        <p class="panel-note" v-else-if="isRunning">
          Streaming events from backend...
        </p>
        <p class="panel-note" v-else>Ready.</p>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount } from "vue";
import { useResearch } from "~/composables/useResearch";

const config = useRuntimeConfig();
const apiBaseUrl = config.public.apiBaseUrl;

const pipelineSteps = [
  { index: 1, label: "Generating search queries" },
  { index: 2, label: "Searching and deduplicating papers" },
  { index: 3, label: "Downloading and extracting PDFs" },
  { index: 4, label: "Creating sparse embeddings" },
  { index: 5, label: "Storing vectors in Qdrant" },
  { index: 6, label: "Running retrieval and generating review" },
];

const {
  topic,
  isRunning,
  isCancelled,
  currentStep,
  totalSteps,
  latestMessage,
  markdown,
  errorMessage,
  statusHistory,
  validationError,
  canSubmit,
  progressPercent,
  startResearch,
  cancelResearch,
  resetResearch,
} = useResearch();

onBeforeUnmount(() => {
  cancelResearch();
});
</script>

<style scoped>
:global(html, body, #__nuxt) {
  min-height: 100%;
}

.page-root {
  min-height: 100vh;
  padding: 2rem 1rem 3rem;
  background:
    radial-gradient(
      circle at 12% 15%,
      rgba(255, 226, 179, 0.7),
      transparent 35%
    ),
    radial-gradient(
      circle at 85% 10%,
      rgba(153, 225, 255, 0.6),
      transparent 28%
    ),
    linear-gradient(145deg, #f6f7f2 0%, #f2f8ff 52%, #f6efe6 100%);
  color: #11213a;
}

.app-shell {
  width: min(980px, 100%);
  margin: 0 auto;
  display: grid;
  gap: 1rem;
}

.hero {
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(17, 33, 58, 0.15);
  border-radius: 18px;
  padding: 1.4rem;
  backdrop-filter: blur(5px);
}

.kicker {
  margin: 0;
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 700;
  color: #92400e;
}

h1 {
  margin: 0.35rem 0 0.35rem;
  font-size: clamp(1.8rem, 4vw, 2.7rem);
  line-height: 1.1;
}

.subtitle {
  margin: 0;
  max-width: 66ch;
  color: #2a3750;
}

.api-target {
  margin: 0.85rem 0 0;
  color: #183153;
  font-size: 0.9rem;
  font-weight: 600;
}

.panel {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(17, 33, 58, 0.12);
  border-radius: 14px;
  padding: 1.1rem;
}

.panel h2 {
  margin: 0;
  font-size: 1.08rem;
}

.panel-note {
  margin: 0.35rem 0 1rem;
  font-size: 0.92rem;
  color: #34425f;
}

label {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

textarea {
  width: 100%;
  border: 1px solid rgba(24, 49, 83, 0.22);
  border-radius: 10px;
  padding: 0.7rem 0.75rem;
  resize: vertical;
  font: inherit;
  color: inherit;
  background: #fffefb;
}

.actions-row {
  margin-top: 0.8rem;
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
}

button {
  border: 0;
  border-radius: 999px;
  padding: 0.55rem 0.95rem;
  font-weight: 600;
  color: #f4f7ff;
  background: linear-gradient(90deg, #294e80 0%, #175466 100%);
  opacity: 1;
  cursor: pointer;
}

button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-reset {
  color: #183153;
  border: 1px solid rgba(24, 49, 83, 0.2);
  background: #f2f7ff;
}

.form-warning {
  margin: 0.5rem 0 0;
  color: #9a3412;
  font-size: 0.88rem;
}

.progress-wrap {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: rgba(34, 59, 99, 0.15);
  overflow: hidden;
  margin-bottom: 0.9rem;
}

.progress-bar {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #d97706 0%, #0b7285 100%);
  transition: width 180ms ease;
}

.progress-meta {
  margin: 0 0 0.75rem;
  color: #2a3d60;
  font-size: 0.9rem;
}

.step-list {
  margin: 0;
  padding-left: 1.25rem;
  color: #203253;
  display: grid;
  gap: 0.3rem;
}

.step-list li.done {
  color: #1f6f3e;
}

.step-list li.active {
  color: #0b7285;
  font-weight: 700;
}

.event-list {
  margin: 0.9rem 0 0;
  padding: 0.7rem 0.85rem;
  list-style: none;
  border-radius: 10px;
  background: #f9fbff;
  border: 1px solid rgba(27, 60, 104, 0.18);
  display: grid;
  gap: 0.35rem;
  max-height: 180px;
  overflow: auto;
  font-size: 0.88rem;
  color: #2a3d60;
}

.result-placeholder {
  border: 1px dashed rgba(31, 57, 93, 0.28);
  border-radius: 10px;
  background: #fffdfa;
  padding: 0.85rem;
}

.result-placeholder h3 {
  margin: 0 0 0.45rem;
}

.result-placeholder p {
  margin: 0;
  color: #34425f;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family:
    ui-monospace,
    SFMono-Regular,
    Menlo,
    Monaco,
    Consolas,
    Liberation Mono,
    monospace;
  font-size: 0.9rem;
  line-height: 1.45;
}

@media (max-width: 720px) {
  .page-root {
    padding: 1rem 0.75rem 2rem;
  }

  .hero,
  .panel {
    padding: 0.95rem;
  }
}
</style>
