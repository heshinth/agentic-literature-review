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
            and render the final review.
          </p>
        </div>
      </header>

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
          :health-label="healthLabel"
          :health-class="healthClass"
          :status-message="statusMessage"
          :is-status-warning="isStatusWarning"
          :current-step="currentStep"
          :total-steps="totalSteps"
          :latest-message="latestMessage"
          :progress-percent="progressPercent"
          :status-history="statusHistory"
        />
      </section>

      <section ref="resultSectionRef" class="result-anchor">
        <ReviewMarkdown :markdown="markdown" />
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import { useResearch } from "~/composables/useResearch";

const config = useRuntimeConfig();
const apiBaseUrl = config.public.apiBaseUrl;
const backendHealthy = ref<boolean | null>(null);
const isCheckingHealth = ref(false);
const resultSectionRef = ref<HTMLElement | null>(null);

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

const statusMessage = computed(() => {
  if (errorMessage.value) {
    return errorMessage.value;
  }
  if (isCancelled.value) {
    return "Research run cancelled.";
  }
  if (warningMessage.value) {
    return warningMessage.value;
  }
  if (isRunning.value) {
    return "Streaming events from backend...";
  }
  return "Ready.";
});

const isStatusWarning = computed(() => {
  return Boolean(
    errorMessage.value || warningMessage.value || isCancelled.value,
  );
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

watch(isRunning, async (running, wasRunning) => {
  if (running || !wasRunning || !markdown.value) {
    return;
  }

  await nextTick();
  resultSectionRef.value?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
});

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
  font-family: "Manrope", "Segoe UI", sans-serif;
  color: #111f38;
}

.page-root {
  --bg-ink: #111f38;
  --surface-strong: rgba(255, 255, 255, 0.76);
  --surface-soft: rgba(255, 255, 255, 0.56);
  --line-soft: rgba(17, 31, 56, 0.14);
  --accent-orange: #d35c21;
  --accent-teal: #0f8f7c;
  min-height: 100vh;
  position: relative;
  overflow-x: clip;
  overflow-y: visible;
  padding: 2.5rem 1.1rem 2.8rem;
  background:
    radial-gradient(
      circle at 16% 12%,
      rgba(255, 183, 110, 0.55),
      transparent 33%
    ),
    radial-gradient(
      circle at 84% 6%,
      rgba(128, 216, 255, 0.45),
      transparent 35%
    ),
    radial-gradient(
      circle at 86% 78%,
      rgba(154, 238, 212, 0.36),
      transparent 40%
    ),
    linear-gradient(145deg, #f6f0e8 0%, #e8f2fb 44%, #e9f6ef 100%);
  color: var(--bg-ink);
}

.page-root::before,
.page-root::after {
  content: "";
  position: absolute;
  border-radius: 999px;
  pointer-events: none;
}

.page-root::before {
  width: min(48vw, 430px);
  height: min(48vw, 430px);
  left: -10%;
  bottom: -22%;
  background: radial-gradient(
    circle,
    rgba(255, 255, 255, 0.62),
    rgba(255, 255, 255, 0)
  );
}

.page-root::after {
  width: min(34vw, 320px);
  height: min(34vw, 320px);
  right: -6%;
  top: 28%;
  background: radial-gradient(
    circle,
    rgba(255, 255, 255, 0.48),
    rgba(255, 255, 255, 0)
  );
}

.app-shell {
  width: min(1120px, 100%);
  margin: 0 auto;
  display: grid;
  gap: 1.1rem;
  position: relative;
  z-index: 1;
}

.app-shell > * {
  opacity: 0;
  transform: translateY(10px);
  animation: rise-in 480ms cubic-bezier(0.2, 0.75, 0.2, 1) forwards;
}

.app-shell > *:nth-child(1) {
  animation-delay: 30ms;
}

.app-shell > *:nth-child(2) {
  animation-delay: 100ms;
}

.app-shell > *:nth-child(3) {
  animation-delay: 170ms;
}

.app-shell > *:nth-child(4) {
  animation-delay: 240ms;
}

.hero {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
  gap: 1.1rem;
  background: linear-gradient(
    144deg,
    var(--surface-strong),
    rgba(244, 252, 255, 0.8)
  );
  border: 1px solid var(--line-soft);
  border-radius: 1.4rem;
  padding: 1.35rem;
  box-shadow: 0 18px 34px rgba(17, 31, 56, 0.1);
  backdrop-filter: blur(8px);
}

.logo-box {
  font-size: 2.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 4.2rem;
  height: 4.2rem;
  border-radius: 1.05rem;
  background: linear-gradient(
    165deg,
    rgba(255, 255, 255, 0.86),
    rgba(238, 249, 255, 0.78)
  );
  border: 1px solid rgba(17, 31, 56, 0.13);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.32);
}

.kicker {
  margin: 0;
  font-family: "Space Grotesk", "Manrope", sans-serif;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-weight: 700;
  color: var(--accent-orange);
}

h1 {
  margin: 0.25rem 0 0.42rem;
  font-family: "Sora", "Manrope", sans-serif;
  font-size: clamp(2rem, 4.2vw, 3.2rem);
  line-height: 1.02;
  letter-spacing: -0.03em;
}

.subtitle {
  margin: 0;
  max-width: 62ch;
  color: rgba(17, 31, 56, 0.82);
  font-size: clamp(0.98rem, 1.3vw, 1.12rem);
}

.grid-top {
  display: grid;
  grid-template-columns: minmax(320px, 1.03fr) minmax(320px, 1fr);
  gap: 1rem;
}

.result-anchor {
  scroll-margin-top: 1rem;
}

@keyframes rise-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 850px) {
  .page-root {
    padding: 1.2rem 0.78rem 2rem;
  }

  .hero {
    padding: 1rem;
    grid-template-columns: 1fr;
    gap: 0.72rem;
  }

  .logo-box {
    width: 3.6rem;
    height: 3.6rem;
    font-size: 2.2rem;
  }

  .grid-top {
    grid-template-columns: 1fr;
  }
}
</style>
