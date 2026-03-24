import { computed, ref } from "vue";
import { useRuntimeConfig } from "#imports";
import { createSseParser, type ResearchStreamEvent } from "~/utils/sseParser";

interface StatusEvent {
  message: string;
  step: number;
  total: number;
  timestamp: string;
}

interface ResultPayload {
  markdown?: string;
  success?: boolean;
  warnings?: string[];
  network_errors?: string[];
  failed_paper_ids?: string[];
  pipeline_error?: string;
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
  const warningMessage = ref("");
  const warnings = ref<string[]>([]);
  const networkErrors = ref<string[]>([]);
  const failedPaperIds = ref<string[]>([]);
  const malformedEventCount = ref(0);
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

      const resultData = (event.data as ResultPayload | undefined) ?? undefined;
      if (resultData && typeof resultData.markdown === "string") {
        markdown.value = resultData.markdown;
      }

      const incomingWarnings = Array.isArray(resultData?.warnings)
        ? resultData?.warnings.filter((item): item is string => typeof item === "string")
        : [];
      const incomingNetworkErrors = Array.isArray(resultData?.network_errors)
        ? resultData?.network_errors.filter((item): item is string => typeof item === "string")
        : [];
      const incomingFailedIds = Array.isArray(resultData?.failed_paper_ids)
        ? resultData?.failed_paper_ids.filter((item): item is string => typeof item === "string")
        : [];

      warnings.value = incomingWarnings;
      networkErrors.value = incomingNetworkErrors;
      failedPaperIds.value = incomingFailedIds;

      if (incomingWarnings.length || incomingNetworkErrors.length) {
        const parts: string[] = [];
        if (incomingWarnings.length) {
          parts.push(`${incomingWarnings.length} warning(s)`);
        }
        if (incomingNetworkErrors.length) {
          parts.push(`${incomingNetworkErrors.length} network error(s)`);
        }
        warningMessage.value = `Run completed with ${parts.join(" and ")}.`;
      }

      if (resultData?.success === false && !errorMessage.value) {
        errorMessage.value =
          resultData.pipeline_error ||
          "Run completed with errors. Check warnings for details.";
      }
      return;
    }

    if (event.event === "error") {
      errorMessage.value = message || "The backend returned an error event.";

      const errorData = (event.data as ResultPayload | undefined) ?? undefined;
      const incomingWarnings = Array.isArray(errorData?.warnings)
        ? errorData.warnings.filter((item): item is string => typeof item === "string")
        : [];
      const incomingNetworkErrors = Array.isArray(errorData?.network_errors)
        ? errorData.network_errors.filter((item): item is string => typeof item === "string")
        : [];

      if (incomingWarnings.length) {
        warnings.value = incomingWarnings;
      }
      if (incomingNetworkErrors.length) {
        networkErrors.value = incomingNetworkErrors;
      }
      if (!warningMessage.value && incomingWarnings.length) {
        warningMessage.value = `Received ${incomingWarnings.length} warning(s) from backend.`;
      }
    }
  };

  const clearRunData = () => {
    currentStep.value = 0;
    totalSteps.value = 6;
    latestMessage.value = "Idle";
    markdown.value = "";
    errorMessage.value = "";
    warningMessage.value = "";
    warnings.value = [];
    networkErrors.value = [];
    failedPaperIds.value = [];
    malformedEventCount.value = 0;
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
    latestMessage.value = "Connecting to backend...";

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
      const parser = createSseParser({
        onEvent: applyEvent,
        onMalformedEvent: () => {
          malformedEventCount.value += 1;
          warningMessage.value =
            malformedEventCount.value === 1
              ? "Received a malformed stream event. Continuing with valid events."
              : `Received ${malformedEventCount.value} malformed stream events. Continuing with valid events.`;
        },
      });

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
        const completedStep = currentStep.value || 0;
        errorMessage.value =
          completedStep > 0
            ? `Stream disconnected before completion at step ${completedStep}/${totalSteps.value}. Please retry.`
            : "Stream ended before a final result event was received.";
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
        const looksUnavailable =
          message.includes("Failed to fetch") ||
          message.includes("NetworkError") ||
          message.includes("Load failed");

        errorMessage.value = looksUnavailable
          ? `Backend is unreachable at ${config.public.apiBaseUrl}. Ensure the API server is running and CORS allows this frontend.`
          : message;
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
    warningMessage,
    warnings,
    networkErrors,
    failedPaperIds,
    malformedEventCount,
    statusHistory,
    validationError,
    canSubmit,
    progressPercent,
    startResearch,
    cancelResearch,
    resetResearch,
  };
}
