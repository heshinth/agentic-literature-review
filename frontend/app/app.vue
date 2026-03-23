<template>
  <div class="page-root">
    <main class="app-shell">
      <header class="hero">
        <div>
          <p class="kicker">Agentic Literature Review</p>
          <h1>Research Console</h1>
          <p class="subtitle">
            Submit a topic, follow the six-step backend pipeline in real time,
            and render the final literature review markdown.
          </p>
        </div>
        <p class="api-target">API target {{ apiBaseUrl }}</p>
      </header>

      <section class="status-strip" role="status" aria-live="polite">
        <h2>4. Error and System Status</h2>
        <p class="status-text" v-if="errorMessage">{{ errorMessage }}</p>
        <p class="status-text" v-else-if="isCancelled">
          Research run cancelled.
        </p>
        <p class="status-text" v-else-if="isRunning">
          Streaming events from backend...
        </p>
        <p class="status-text" v-else>Ready.</p>
      </section>

      <section class="grid-top">
        <ResearchForm
          :topic="topic"
          :validation-error="validationError"
          :can-submit="canSubmit"
          :is-running="isRunning"
          :is-cancelled="isCancelled"
          @update:topic="topic = $event"
          @submit="startResearch"
          @cancel="cancelResearch"
          @reset="resetResearch"
        />

        <ResearchProgress
          :current-step="currentStep"
          :total-steps="totalSteps"
          :latest-message="latestMessage"
          :progress-percent="progressPercent"
          :status-history="statusHistory"
        />
      </section>

      <ReviewMarkdown :markdown="markdown" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount } from "vue";
import { useResearch } from "~/composables/useResearch";

const config = useRuntimeConfig();
const apiBaseUrl = config.public.apiBaseUrl;

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

:global(body) {
  margin: 0;
  font-family: "Space Grotesk", "Avenir Next", "Segoe UI", sans-serif;
}

.page-root {
  min-height: 100vh;
  padding: 2rem 1rem 2.5rem;
  background:
    radial-gradient(
      circle at 11% 14%,
      rgba(255, 223, 186, 0.72),
      transparent 34%
    ),
    radial-gradient(
      circle at 87% 12%,
      rgba(179, 230, 255, 0.54),
      transparent 30%
    ),
    radial-gradient(
      circle at 86% 88%,
      rgba(183, 249, 227, 0.46),
      transparent 36%
    ),
    linear-gradient(152deg, #f6f7f2 0%, #edf4ff 46%, #f7efe3 100%);
  color: #11213a;
}

.app-shell {
  width: min(1080px, 100%);
  margin: 0 auto;
  display: grid;
  gap: 1rem;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  background: linear-gradient(
    152deg,
    rgba(255, 255, 255, 0.9),
    rgba(241, 249, 255, 0.84)
  );
  border: 1px solid rgba(17, 33, 58, 0.16);
  border-radius: 22px;
  padding: 1.25rem;
  backdrop-filter: blur(4px);
  box-shadow: 0 14px 30px rgba(17, 26, 43, 0.09);
}

.kicker {
  margin: 0;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  font-weight: 700;
  color: #92400e;
}

h1 {
  margin: 0.35rem 0 0.4rem;
  font-size: clamp(1.8rem, 4vw, 2.9rem);
  line-height: 1.1;
}

.subtitle {
  margin: 0;
  max-width: 62ch;
  color: #22314d;
}

.api-target {
  margin: 0;
  border: 1px solid rgba(15, 50, 90, 0.2);
  background: #f6fbff;
  border-radius: 999px;
  padding: 0.45rem 0.75rem;
  color: #133869;
  font-size: 0.83rem;
  font-weight: 600;
}

.status-strip {
  background: linear-gradient(
    145deg,
    rgba(255, 255, 255, 0.9),
    rgba(250, 252, 255, 0.84)
  );
  border: 1px solid rgba(18, 40, 70, 0.13);
  border-radius: 14px;
  padding: 0.9rem 1rem;
}

.status-strip h2 {
  margin: 0;
  font-size: 0.94rem;
  letter-spacing: 0.03em;
}

.status-text {
  margin: 0.35rem 0 0;
  color: #314661;
  font-size: 0.9rem;
}

.grid-top {
  display: grid;
  grid-template-columns: minmax(300px, 1fr) minmax(300px, 1fr);
  gap: 1rem;
}

@media (max-width: 720px) {
  .page-root {
    padding: 1rem 0.75rem 2rem;
  }

  .hero {
    padding: 1rem;
    flex-direction: column;
    align-items: flex-start;
  }

  .api-target {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .grid-top {
    grid-template-columns: 1fr;
  }
}
</style>
