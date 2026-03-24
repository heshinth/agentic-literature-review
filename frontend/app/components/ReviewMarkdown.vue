<template>
  <section class="card markdown-card">
    <div class="card-head">
      <p class="eyebrow">Result</p>
      <h2>Generated Literature Review</h2>
      <div class="actions">
        <button
          class="btn"
          type="button"
          :disabled="!markdown"
          @click="downloadMarkdown"
        >
          Download Markdown
        </button>
        <button
          class="btn"
          type="button"
          :disabled="!markdown"
          @click="copyMarkdown"
        >
          {{ copied ? "Copied" : "Copy Markdown" }}
        </button>
      </div>
    </div>

    <article v-if="markdown" class="markdown-body" v-html="safeHtml" />
    <article v-else class="placeholder">
      <h3>No result yet</h3>
      <p>Start a run to render the final markdown response here.</p>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import MarkdownIt from "markdown-it";
import markdownItFootnote from "markdown-it-footnote";
import sanitizeHtml from "sanitize-html";

const props = defineProps<{
  markdown: string;
}>();

const copied = ref(false);

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: true,
});
md.use(markdownItFootnote);

const safeHtml = computed(() => {
  if (!props.markdown) {
    return "";
  }

  const rendered = md.render(props.markdown);
  return sanitizeHtml(rendered, {
    allowedTags: [
      "h1",
      "h2",
      "h3",
      "h4",
      "h5",
      "h6",
      "p",
      "blockquote",
      "pre",
      "code",
      "ul",
      "ol",
      "li",
      "strong",
      "em",
      "a",
      "hr",
      "table",
      "thead",
      "tbody",
      "tr",
      "th",
      "td",
      "sup",
      "br",
    ],
    allowedAttributes: {
      a: ["href", "target", "rel"],
      code: ["class"],
    },
    allowedSchemes: ["http", "https", "mailto"],
    transformTags: {
      a: (tagName: string, attribs: Record<string, string>) => ({
        tagName,
        attribs: {
          ...attribs,
          target: "_blank",
          rel: "noopener noreferrer",
        },
      }),
    },
  });
});

const copyMarkdown = async () => {
  if (!props.markdown) {
    return;
  }

  try {
    await navigator.clipboard.writeText(props.markdown);
    copied.value = true;
    window.setTimeout(() => {
      copied.value = false;
    }, 1400);
  } catch {
    copied.value = false;
  }
};

const downloadMarkdown = () => {
  if (!props.markdown) {
    return;
  }

  const safeDate = new Date().toISOString().replace(/[:.]/g, "-");
  const fileName = `literature-review-${safeDate}.md`;

  const blob = new Blob([props.markdown], {
    type: "text/markdown;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();

  URL.revokeObjectURL(url);
};
</script>

<style scoped>
.card {
  background: linear-gradient(
    155deg,
    rgba(255, 255, 255, 0.82),
    rgba(255, 247, 238, 0.7)
  );
  border: 1px solid rgba(17, 31, 56, 0.14);
  border-radius: 1.28rem;
  padding: 1.1rem;
  box-shadow: 0 14px 26px rgba(17, 31, 56, 0.08);
  backdrop-filter: blur(8px);
}

.card-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.56rem 1rem;
  margin-bottom: 0.86rem;
}

.eyebrow {
  margin: 0;
  width: 100%;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.17em;
  color: #c7541e;
  font-weight: 700;
  font-family: "Space Grotesk", "Manrope", sans-serif;
}

h2 {
  margin: 0;
  font-family: "Sora", "Manrope", sans-serif;
  font-size: clamp(1.14rem, 2vw, 1.4rem);
  letter-spacing: -0.02em;
}

.actions {
  margin-left: auto;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn {
  border: 1px solid rgba(25, 65, 104, 0.2);
  border-radius: 999px;
  padding: 0.46rem 0.94rem;
  font-size: 0.81rem;
  font-weight: 700;
  color: #194168;
  background: rgba(248, 252, 255, 0.78);
  cursor: pointer;
  transition:
    transform 140ms ease,
    opacity 140ms ease;
}

.btn:not(:disabled):hover {
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.placeholder {
  border: 1px dashed rgba(17, 53, 86, 0.28);
  border-radius: 0.9rem;
  background: rgba(255, 255, 255, 0.72);
  padding: 0.95rem;
}

.placeholder h3 {
  margin: 0 0 0.4rem;
  font-family: "Sora", "Manrope", sans-serif;
}

.placeholder p {
  margin: 0;
  color: rgba(17, 31, 56, 0.76);
}

.markdown-body {
  border: 1px solid rgba(17, 53, 86, 0.14);
  background: rgba(255, 255, 255, 0.78);
  border-radius: 0.9rem;
  padding: 1rem 1.02rem;
  line-height: 1.65;
  color: #111f38;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  line-height: 1.25;
  margin-top: 1.2rem;
  margin-bottom: 0.6rem;
}

.markdown-body :deep(h1) {
  font-size: 1.66rem;
}

.markdown-body :deep(h2) {
  font-size: 1.36rem;
}

.markdown-body :deep(h3) {
  font-size: 1.14rem;
}

.markdown-body :deep(p),
.markdown-body :deep(ul),
.markdown-body :deep(ol),
.markdown-body :deep(blockquote),
.markdown-body :deep(pre) {
  margin: 0.75rem 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.2rem;
}

.markdown-body :deep(code) {
  background: #ebf4fa;
  border-radius: 5px;
  padding: 0.1rem 0.32rem;
  font-size: 0.88em;
}

.markdown-body :deep(pre code) {
  display: block;
  padding: 0.72rem;
  border-radius: 10px;
  overflow-x: auto;
  background: #15253f;
  color: #e7f5ff;
}

.markdown-body :deep(blockquote) {
  margin-left: 0;
  padding: 0.25rem 0.85rem;
  border-left: 4px solid #0f8f7c;
  background: rgba(238, 250, 248, 0.86);
}

.markdown-body :deep(a) {
  color: #0f5f96;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  overflow: auto;
  display: block;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid rgba(25, 65, 104, 0.18);
  padding: 0.42rem 0.5rem;
  text-align: left;
}

.markdown-body :deep(sup) {
  vertical-align: super;
  font-size: 0.75em;
}

@media (max-width: 850px) {
  .card {
    padding: 0.95rem;
  }
}
</style>
