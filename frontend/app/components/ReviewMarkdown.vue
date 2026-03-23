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
import { marked } from "marked";
import sanitizeHtml from "sanitize-html";

const props = defineProps<{
  markdown: string;
}>();

const copied = ref(false);

const safeHtml = computed(() => {
  if (!props.markdown) {
    return "";
  }

  const rendered = marked.parse(props.markdown, { async: false });
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
</script>

<style scoped>
.card {
  background: linear-gradient(
    165deg,
    rgba(255, 255, 255, 0.95),
    rgba(255, 248, 240, 0.86)
  );
  border: 1px solid rgba(26, 33, 52, 0.12);
  border-radius: 20px;
  padding: 1.15rem;
  box-shadow: 0 10px 26px rgba(17, 26, 43, 0.08);
}

.card-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem 1rem;
  margin-bottom: 0.8rem;
}

.eyebrow {
  margin: 0;
  width: 100%;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #8a2d08;
  font-weight: 700;
}

h2 {
  margin: 0;
  font-size: clamp(1.1rem, 2vw, 1.35rem);
}

.actions {
  margin-left: auto;
}

.btn {
  border: 1px solid rgba(25, 56, 94, 0.2);
  border-radius: 999px;
  padding: 0.45rem 0.9rem;
  font-size: 0.82rem;
  font-weight: 700;
  color: #18305c;
  background: #f7fbff;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.placeholder {
  border: 1px dashed rgba(31, 57, 93, 0.26);
  border-radius: 12px;
  background: #fffdf9;
  padding: 0.9rem;
}

.placeholder h3 {
  margin: 0 0 0.45rem;
}

.placeholder p {
  margin: 0;
  color: #3b4660;
}

.markdown-body {
  border: 1px solid rgba(38, 52, 84, 0.14);
  background: #fffdfa;
  border-radius: 12px;
  padding: 1rem;
  line-height: 1.62;
  color: #13233f;
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
  font-size: 1.62rem;
}

.markdown-body :deep(h2) {
  font-size: 1.34rem;
}

.markdown-body :deep(h3) {
  font-size: 1.13rem;
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
  background: #edf4ff;
  border-radius: 5px;
  padding: 0.1rem 0.32rem;
  font-size: 0.88em;
}

.markdown-body :deep(pre code) {
  display: block;
  padding: 0.72rem;
  border-radius: 10px;
  overflow-x: auto;
  background: #10243b;
  color: #e6f1ff;
}

.markdown-body :deep(blockquote) {
  margin-left: 0;
  padding: 0.25rem 0.85rem;
  border-left: 4px solid #0e7490;
  background: #f3fcff;
}

.markdown-body :deep(a) {
  color: #065f93;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  overflow: auto;
  display: block;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid rgba(25, 56, 94, 0.18);
  padding: 0.42rem 0.5rem;
  text-align: left;
}

.markdown-body :deep(sup) {
  vertical-align: super;
  font-size: 0.75em;
}
</style>
