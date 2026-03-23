export interface ResearchStreamEvent {
  event?: "status" | "result" | "error" | string;
  message?: string;
  step?: number;
  total?: number;
  data?: Record<string, unknown>;
}

interface SseParserOptions {
  onEvent: (event: ResearchStreamEvent) => void;
}

/**
 * Incremental parser for text/event-stream payloads that may arrive in partial chunks.
 */
export function createSseParser(options: SseParserOptions) {
  let buffer = "";

  const parseBlock = (block: string): void => {
    const lines = block.split(/\r?\n/);
    const dataLines: string[] = [];

    for (const line of lines) {
      if (!line.startsWith("data:")) {
        continue;
      }

      // SSE allows optional leading space after "data:".
      dataLines.push(line.slice(5).trimStart());
    }

    if (!dataLines.length) {
      return;
    }

    const payload = dataLines.join("\n").trim();
    if (!payload) {
      return;
    }

    try {
      const parsed = JSON.parse(payload) as ResearchStreamEvent;
      options.onEvent(parsed);
    } catch {
      // Ignore malformed payloads instead of breaking the entire stream.
    }
  };

  const drainBlocks = (flushRemainder = false): void => {
    let delimiterIndex = buffer.search(/\r?\n\r?\n/);

    while (delimiterIndex !== -1) {
      const block = buffer.slice(0, delimiterIndex);
      buffer = buffer.slice(delimiterIndex).replace(/^\r?\n\r?\n/, "");
      parseBlock(block);
      delimiterIndex = buffer.search(/\r?\n\r?\n/);
    }

    if (flushRemainder && buffer.trim().length > 0) {
      parseBlock(buffer);
      buffer = "";
    }
  };

  return {
    pushChunk(chunk: string): void {
      if (!chunk) {
        return;
      }
      buffer += chunk;
      drainBlocks(false);
    },
    flush(): void {
      drainBlocks(true);
    },
  };
}
