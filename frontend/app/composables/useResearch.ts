import { computed, ref } from "vue";
import { useRuntimeConfig } from "#imports";
import { createSseParser, type ResearchStreamEvent } from "~/utils/sseParser";

interface StatusEvent {
  message: string;
  step: number;
  total: number;
  timestamp: string;
}

export function useResearch() {
  const config = useRuntimeConfig();

  const topic = ref("");
  const isRunning = ref(false);
  const isCancelled = ref(false);

  const currentStep = ref(0);
  const totalSteps = ref(6);
  const latestMessage = ref("Idle");

  const markdown = ref("");
  const errorMessage = ref("");
  const statusHistory = ref<StatusEvent[]>([]);

  const abortController = ref<AbortController | null>(null);

  const trimmedTopic = computed(() => topic.value.trim());
  const canSubmit = computed(
    () => !isRunning.value && trimmedTopic.value.length >= 3,
  );

  const validationError = computed(() => {
    if (!trimmedTopic.value.length) {
      return "";
    }

    if (trimmedTopic.value.length < 3) {
      return "Topic must be at least 3 characters.";
    }

    return "";
  });

  const progressPercent = computed(() => {
    if (!totalSteps.value || !currentStep.value) {
      return 0;
    }

    return Math.min(
      100,
      Math.max(0, (currentStep.value / totalSteps.value) * 100),
    );
  });

  const applyEvent = (event: ResearchStreamEvent) => {
    const message = event.message?.trim() || "";

    if (event.event === "status") {
      const step = Number.isFinite(event.step)
        ? Number(event.step)
        : currentStep.value;
      const total = Number.isFinite(event.total)
        ? Number(event.total)
        : totalSteps.value || 6;

      currentStep.value = step;
      totalSteps.value = total;
      latestMessage.value = message || latestMessage.value;

      statusHistory.value.push({
        message: latestMessage.value,
        step: currentStep.value,
        total: totalSteps.value,
        timestamp: new Date().toISOString(),
      });
      return;
    }

    if (event.event === "result") {
      if (Number.isFinite(event.step)) {
        currentStep.value = Number(event.step);
      }
      if (Number.isFinite(event.total)) {
        totalSteps.value = Number(event.total);
      }

      latestMessage.value = message || "Done";

      const resultData = event.data;
      if (resultData && typeof resultData.markdown === "string") {
        markdown.value = resultData.markdown;
      }
      return;
    }

    if (event.event === "error") {
      errorMessage.value = message || "The backend returned an error event.";
    }
  };

  const clearRunData = () => {
    currentStep.value = 0;
    totalSteps.value = 6;
    latestMessage.value = "Idle";
    markdown.value = "";
    errorMessage.value = "";
    statusHistory.value = [];
    isCancelled.value = false;
  };

  const startResearch = async () => {
    if (isRunning.value) {
      return;
    }

    if (trimmedTopic.value.length < 3) {
      errorMessage.value =
        "Please enter a research topic with at least 3 characters.";
      return;
    }

    clearRunData();
    isRunning.value = true;

    const controller = new AbortController();
    abortController.value = controller;

    try {
      const response = await fetch(`${config.public.apiBaseUrl}/research`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ topic: trimmedTopic.value }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(
          body || `Request failed with status ${response.status}.`,
        );
      }

      const contentType = response.headers.get("content-type") || "";
      if (!contentType.includes("text/event-stream")) {
        throw new Error("The backend response is not an SSE stream.");
      }

      if (!response.body) {
        throw new Error("No response body available from backend stream.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      const parser = createSseParser({ onEvent: applyEvent });

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        parser.pushChunk(chunk);
      }

      parser.pushChunk(decoder.decode());
      parser.flush();

      if (!markdown.value && !errorMessage.value && !isCancelled.value) {
        errorMessage.value =
          "Stream ended before a final result event was received.";
      }
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        if (!isCancelled.value) {
          isCancelled.value = true;
          latestMessage.value = "Cancelled";
        }
      } else {
        const message =
          error instanceof Error ? error.message : "Unexpected stream error.";
        errorMessage.value = message;
      }
    } finally {
      isRunning.value = false;
      abortController.value = null;
    }
  };

  const cancelResearch = () => {
    if (!abortController.value) {
      return;
    }
    isCancelled.value = true;
    latestMessage.value = "Cancelling stream...";
    abortController.value.abort();
  };

  const resetResearch = () => {
    if (isRunning.value) {
      cancelResearch();
    }
    clearRunData();
  };

  return {
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
  };
}
