<template>
  <section class="card progress-card">
    <div class="status-inline" role="status" aria-live="polite">
      <div class="health-pill" :class="healthClass">
        <span class="health-dot" />
        <span class="health-label">{{ healthLabel }}</span>
      </div>
      <p class="status-text" :class="{ 'status-warning': isStatusWarning }">
        {{ statusMessage }}
      </p>
    </div>

    <div class="card-head">
      <p class="eyebrow">Progress</p>
      <h2>{{ latestMessage }}</h2>
      <p class="meta">Step {{ currentStep || 0 }} / {{ totalSteps }}</p>
    </div>

    <div class="meter" aria-hidden="true">
      <div class="meter-fill" :style="{ width: `${progressPercent}%` }" />
    </div>

    <ol class="steps">
      <li
        v-for="step in steps"
        :key="step.index"
        :class="{
          done: currentStep > step.index,
          active: currentStep === step.index,
        }"
      >
        <span class="index">{{ step.index }}</span>
        <span class="label">{{ step.label }}</span>
      </li>
    </ol>

    <ul class="events">
      <template v-if="statusHistory.length">
        <li
          v-for="entry in statusHistory"
          :key="`${entry.timestamp}-${entry.step}`"
        >
          <span class="stamp">{{ formatTime(entry.timestamp) }}</span>
          <span>[{{ entry.step }}/{{ entry.total }}] {{ entry.message }}</span>
        </li>
      </template>
      <li v-else class="events-empty">Waiting for backend status events...</li>
    </ul>
  </section>
</template>

<script setup lang="ts">
interface StatusEvent {
  message: string;
  step: number;
  total: number;
  timestamp: string;
}

defineProps<{
  healthLabel: string;
  healthClass: string;
  statusMessage: string;
  isStatusWarning: boolean;
  currentStep: number;
  totalSteps: number;
  latestMessage: string;
  progressPercent: number;
  statusHistory: StatusEvent[];
}>();

const steps = [
  { index: 1, label: "Generating search queries" },
  { index: 2, label: "Searching and deduplicating papers" },
  { index: 3, label: "Downloading and extracting PDFs" },
  { index: 4, label: "Preparing searchable representations" },
  { index: 5, label: "Updating search index" },
  { index: 6, label: "Running retrieval and generating review" },
];

const formatTime = (iso: string): string => {
  const date = new Date(iso);
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};
</script>

<style scoped>
.card {
  background: linear-gradient(
    152deg,
    rgba(255, 255, 255, 0.8),
    rgba(240, 252, 248, 0.7)
  );
  border: 1px solid rgba(17, 31, 56, 0.14);
  border-radius: 1.28rem;
  padding: 1.1rem;
  box-shadow: 0 14px 26px rgba(17, 31, 56, 0.08);
  backdrop-filter: blur(8px);
}

.status-inline {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
  border-radius: 999px;
  padding: 0.42rem 0.58rem;
  margin-bottom: 0.82rem;
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(17, 31, 56, 0.12);
}

.health-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.44rem;
  border-radius: 999px;
  padding: 0.3rem 0.58rem;
  font-size: 0.82rem;
  font-weight: 700;
  border: 1px solid transparent;
}

.health-dot {
  width: 0.52rem;
  height: 0.52rem;
  border-radius: 50%;
}

.health-pill.is-online {
  color: #17663e;
  background: rgba(187, 247, 208, 0.42);
  border-color: rgba(34, 197, 94, 0.35);
}

.health-pill.is-online .health-dot {
  background: #1f9f55;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
}

.health-pill.is-offline {
  color: #9d2626;
  background: rgba(254, 202, 202, 0.48);
  border-color: rgba(239, 68, 68, 0.35);
}

.health-pill.is-offline .health-dot {
  background: #e34848;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
}

.health-pill.is-checking {
  color: #1f4da4;
  background: rgba(191, 219, 254, 0.48);
  border-color: rgba(59, 130, 246, 0.35);
}

.health-pill.is-checking .health-dot {
  background: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.status-text {
  margin: 0;
  color: rgba(17, 31, 56, 0.8);
  font-size: 0.84rem;
}

.status-warning {
  color: #98520f;
}

.card-head {
  margin-bottom: 0.86rem;
}

.eyebrow {
  margin: 0;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.17em;
  color: #0a6f96;
  font-weight: 700;
  font-family: "Space Grotesk", "Manrope", sans-serif;
}

h2 {
  margin: 0.28rem 0 0;
  font-family: "Sora", "Manrope", sans-serif;
  font-size: clamp(1.08rem, 2vw, 1.3rem);
  letter-spacing: -0.02em;
}

.meta {
  margin: 0.38rem 0 0;
  color: rgba(17, 31, 56, 0.72);
  font-size: 0.88rem;
}

.meter {
  width: 100%;
  height: 11px;
  border-radius: 999px;
  background: rgba(17, 89, 121, 0.16);
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(92deg, #d16120 0%, #0f8f7c 100%);
  transition: width 200ms ease;
}

.steps {
  margin: 0.9rem 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.48rem;
}

.steps li {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: rgba(17, 31, 56, 0.86);
}

.index {
  width: 1.45rem;
  height: 1.45rem;
  border-radius: 50%;
  display: inline-grid;
  place-content: center;
  font-size: 0.76rem;
  font-weight: 700;
  background: rgba(21, 83, 135, 0.14);
  color: #17406f;
}

.steps li.done .index {
  background: rgba(15, 143, 124, 0.18);
  color: #0c685b;
}

.steps li.active .index {
  background: rgba(209, 97, 32, 0.22);
  color: #8f3b15;
}

.steps li.active .label {
  font-weight: 700;
  color: #9a4218;
}

.events {
  margin: 0.92rem 0 0;
  padding: 0.7rem 0.84rem;
  list-style: none;
  border: 1px solid rgba(17, 53, 86, 0.16);
  border-radius: 0.88rem;
  background: rgba(252, 254, 255, 0.78);
  min-height: 160px;
  max-height: 160px;
  overflow: auto;
  display: grid;
  gap: 0.42rem;
  font-size: 0.84rem;
}

.events li {
  display: grid;
  gap: 0.14rem;
  border-left: 2px solid rgba(15, 143, 124, 0.28);
  padding-left: 0.55rem;
}

.stamp {
  color: #5a6982;
  font-size: 0.75rem;
}

.events-empty {
  color: rgba(17, 31, 56, 0.62);
  border-left: 2px dashed rgba(17, 53, 86, 0.24);
  padding-left: 0.55rem;
  align-self: start;
}

@media (max-width: 850px) {
  .card {
    padding: 0.95rem;
  }
}
</style>
