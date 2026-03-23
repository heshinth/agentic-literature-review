<template>
  <section class="card progress-card">
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

    <ul class="events" v-if="statusHistory.length">
      <li
        v-for="entry in statusHistory"
        :key="`${entry.timestamp}-${entry.step}`"
      >
        <span class="stamp">{{ formatTime(entry.timestamp) }}</span>
        <span>[{{ entry.step }}/{{ entry.total }}] {{ entry.message }}</span>
      </li>
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
  { index: 4, label: "Creating sparse embeddings" },
  { index: 5, label: "Storing vectors in Qdrant" },
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
    145deg,
    rgba(255, 255, 255, 0.96),
    rgba(242, 253, 251, 0.88)
  );
  border: 1px solid rgba(26, 33, 52, 0.12);
  border-radius: 20px;
  padding: 1.15rem;
  box-shadow: 0 10px 26px rgba(17, 26, 43, 0.08);
}

.card-head {
  margin-bottom: 0.75rem;
}

.eyebrow {
  margin: 0;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #075985;
  font-weight: 700;
}

h2 {
  margin: 0.25rem 0 0;
  font-size: clamp(1.05rem, 2vw, 1.28rem);
}

.meta {
  margin: 0.35rem 0 0;
  color: #3a4b68;
  font-size: 0.88rem;
}

.meter {
  width: 100%;
  height: 11px;
  border-radius: 999px;
  background: rgba(13, 67, 112, 0.16);
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #d97706 0%, #059669 100%);
  transition: width 200ms ease;
}

.steps {
  margin: 0.8rem 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.44rem;
}

.steps li {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: #263754;
}

.index {
  width: 1.45rem;
  height: 1.45rem;
  border-radius: 50%;
  display: inline-grid;
  place-content: center;
  font-size: 0.76rem;
  font-weight: 700;
  background: rgba(37, 99, 235, 0.14);
  color: #1f3b77;
}

.steps li.done .index {
  background: rgba(21, 128, 61, 0.16);
  color: #166534;
}

.steps li.active .index {
  background: rgba(8, 145, 178, 0.22);
  color: #0f4a6b;
}

.steps li.active .label {
  font-weight: 700;
  color: #114b6f;
}

.events {
  margin: 0.9rem 0 0;
  padding: 0.68rem 0.82rem;
  list-style: none;
  border: 1px solid rgba(17, 65, 88, 0.18);
  border-radius: 11px;
  background: #f8fbff;
  max-height: 190px;
  overflow: auto;
  display: grid;
  gap: 0.36rem;
  font-size: 0.84rem;
}

.events li {
  display: grid;
  gap: 0.12rem;
}

.stamp {
  color: #5d6c85;
  font-size: 0.75rem;
}
</style>
