<template>
  <div class="page-root">
    <main class="app-shell">
      <header class="hero">
        <div class="logo-box">🤖</div>
        <div>
          <p class="kicker">Agentic Literature Review</p>
          <h1>Research Console</h1>
          <p class="subtitle">
            Submit a topic, follow the six-step backend pipeline in real time,
            and render the final literature review markdown.
          </p>
        </div>
      </header>

      <section class="status-strip" role="status" aria-live="polite">
        <div class="health-pill" :class="healthClass">
          <span class="health-dot" />
          <span class="health-label">{{ healthLabel }}</span>
        </div>
        <p class="status-text" v-if="errorMessage">{{ errorMessage }}</p>
        <p class="status-text" v-else-if="isCancelled">
          Research run cancelled.
        </p>
        <p class="status-text status-warning" v-else-if="warningMessage">
          {{ warningMessage }}
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
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useResearch } from "~/composables/useResearch";

const config = useRuntimeConfig();
const apiBaseUrl = config.public.apiBaseUrl;
const backendHealthy = ref<boolean | null>(null);
const isCheckingHealth = ref(false);

let healthPollTimer: ReturnType<typeof setInterval> | null = null;

const healthLabel = computed(() => {
  if (backendHealthy.value === true) {
    return "Backend online";
  }
  if (backendHealthy.value === false) {
    return "Backend offline";
  }
  return "Checking backend";
});

const healthClass = computed(() => {
  if (backendHealthy.value === true) {
    return "is-online";
  }
  if (backendHealthy.value === false) {
    return "is-offline";
  }
  return "is-checking";
});

const checkBackendHealth = async () => {
  if (isCheckingHealth.value) {
    return;
  }
  isCheckingHealth.value = true;

  try {
    const response = await fetch(`${apiBaseUrl}/health`, {
      method: "GET",
      cache: "no-store",
    });
    if (!response.ok) {
      backendHealthy.value = false;
      return;
    }

    const payload = (await response.json()) as { status?: string };
    backendHealthy.value = payload.status === "ok";
  } catch {
    backendHealthy.value = false;
  } finally {
    isCheckingHealth.value = false;
  }
};

const {
  topic,
  isRunning,
  isCancelled,
  currentStep,
  totalSteps,
  latestMessage,
  markdown,
  errorMessage,
  warningMessage,
  statusHistory,
  validationError,
  canSubmit,
  progressPercent,
  startResearch,
  cancelResearch,
  resetResearch,
} = useResearch();

onMounted(() => {
  checkBackendHealth();
  healthPollTimer = setInterval(() => {
    checkBackendHealth();
  }, 5000);
});

onBeforeUnmount(() => {
  if (healthPollTimer) {
    clearInterval(healthPollTimer);
    healthPollTimer = null;
  }
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

.logo-box {
  font-size: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 4rem;
  height: 4rem;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
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

.status-strip {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  background: linear-gradient(
    145deg,
    rgba(255, 255, 255, 0.9),
    rgba(250, 252, 255, 0.84)
  );
  border: 1px solid rgba(18, 40, 70, 0.13);
  border-radius: 999px;
  padding: 0.45rem 0.7rem;
}

.health-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.42rem;
  border-radius: 999px;
  padding: 0.3rem 0.55rem;
  font-size: 0.82rem;
  font-weight: 700;
  border: 1px solid transparent;
}

.health-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
}

.health-pill.is-online {
  color: #166534;
  background: rgba(187, 247, 208, 0.42);
  border-color: rgba(34, 197, 94, 0.35);
}

.health-pill.is-online .health-dot {
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
}

.health-pill.is-offline {
  color: #991b1b;
  background: rgba(254, 202, 202, 0.45);
  border-color: rgba(239, 68, 68, 0.35);
}

.health-pill.is-offline .health-dot {
  background: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
}

.health-pill.is-checking {
  color: #1e3a8a;
  background: rgba(191, 219, 254, 0.45);
  border-color: rgba(59, 130, 246, 0.35);
}

.health-pill.is-checking .health-dot {
  background: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.status-text {
  margin: 0;
  color: #314661;
  font-size: 0.84rem;
}

.status-warning {
  color: #8a4b00;
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
  }

  .grid-top {
    grid-template-columns: 1fr;
  }

  .status-strip {
    border-radius: 14px;
  }
}
</style>
