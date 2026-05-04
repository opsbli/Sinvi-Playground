<script setup>
import { computed, ref } from "vue";
import {
  Boxes,
  CheckCircle2,
  FileText,
  GitPullRequestArrow,
  Loader2,
  Play,
  RefreshCw,
  Sparkles,
} from "lucide-vue-next";

const props = defineProps({
  pipelines: {
    type: Array,
    required: true,
  },
  selectedRun: {
    type: Object,
    default: null,
  },
  busy: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["bootstrap", "generate", "run-story", "execute-run", "select-run"]);

const brief = ref("做一个 Pipeline Console，支持 PRD、Story、阶段执行和产物查看。");

const prdStoryDefinition = computed(() =>
  props.pipelines.find((pipeline) => pipeline.kind === "prd_story_generation") || null,
);

const sequentialDefinition = computed(() =>
  props.pipelines.find((pipeline) => pipeline.kind === "sequential_pipeline") || null,
);

const stories = computed(() =>
  (props.selectedRun?.artifacts || []).filter((artifact) => artifact.artifact_type === "story"),
);

const visibleArtifacts = computed(() => props.selectedRun?.artifacts || []);

function artifactPreview(artifact) {
  const content = String(artifact?.content || "").trim();
  if (!content) return "No content.";
  return content.length > 900 ? `${content.slice(0, 900)}...` : content;
}

function stageName(stageRun) {
  const definitions = [...(prdStoryDefinition.value?.stages || []), ...(sequentialDefinition.value?.stages || [])];
  const found = definitions.find((stage) => stage.id === stageRun.stage_definition_id);
  return found?.name || stageRun.input_payload?.role || stageRun.stage_definition_id;
}

function statusClass(status) {
  return `pipeline-status-${status || "pending"}`;
}

function generate() {
  emit("generate", {
    pipeline_id: prdStoryDefinition.value?.id,
    brief: brief.value,
  });
}

function runStory(story) {
  if (!sequentialDefinition.value) return;
  emit("run-story", {
    pipelineId: sequentialDefinition.value.id,
    story,
  });
}
</script>

<template>
  <div class="page-stack pipeline-page">
    <section class="toolbar-card pipeline-hero">
      <div class="manager-topbar">
        <div>
          <span class="chip chip-blue">AI Coding Pipeline</span>
          <h2>Pipelines</h2>
          <p>把 brief 变成 PRD、Story，再把单个 Story 送入 Designer / Reviewer / Coder / Validator 阶段。</p>
        </div>
        <button class="primary-button" :disabled="busy" @click="$emit('bootstrap')">
          <RefreshCw :size="16" :class="{ 'spin-icon': busy }" />
          Bootstrap
        </button>
      </div>
    </section>

    <section class="pipeline-console-grid">
      <aside class="glass-panel pipeline-column">
        <div class="pipeline-section-head">
          <h3><Boxes :size="18" /> Definitions</h3>
          <span class="chip">{{ pipelines.length }}</span>
        </div>

        <div v-if="pipelines.length" class="pipeline-definition-list">
          <article
            v-for="pipeline in pipelines"
            :key="pipeline.id"
            class="pipeline-definition-card"
          >
            <div>
              <h4>{{ pipeline.name }}</h4>
              <p>{{ pipeline.description || pipeline.kind }}</p>
            </div>
            <span class="chip chip-dark">{{ pipeline.kind }}</span>
            <div class="pipeline-stage-pills">
              <span v-for="stage in pipeline.stages" :key="stage.id" class="pipeline-stage-pill">
                {{ stage.stage_order }}. {{ stage.role }}
              </span>
            </div>
          </article>
        </div>
        <div v-else class="pipeline-empty">
          <Sparkles :size="22" />
          <strong>还没有 Pipeline 模板</strong>
          <span>点击 Bootstrap 创建 AI Coding 默认模板。</span>
        </div>
      </aside>

      <section class="glass-panel pipeline-column pipeline-main-column">
        <div class="pipeline-section-head">
          <h3><FileText :size="18" /> Brief -> PRD -> Stories</h3>
          <span v-if="stories.length" class="chip chip-green">{{ stories.length }} stories</span>
        </div>

        <textarea
          v-model="brief"
          class="pipeline-brief-input"
          placeholder="输入产品想法或需求 brief..."
          rows="6"
        ></textarea>
        <button
          class="primary-button pipeline-wide-action"
          :disabled="busy || !prdStoryDefinition || !brief.trim()"
          @click="generate"
        >
          <Sparkles :size="16" />
          Generate PRD & Stories
        </button>

        <div class="pipeline-story-list">
          <article
            v-for="story in stories"
            :key="story.id"
            class="pipeline-story-card"
          >
            <div>
              <span class="chip">{{ story.metadata?.story_id || story.name }}</span>
              <h4>{{ story.metadata?.title || story.name }}</h4>
              <p>{{ artifactPreview(story).slice(0, 180) }}</p>
            </div>
            <button
              class="text-button"
              :disabled="busy || !sequentialDefinition"
              @click="runStory(story)"
            >
              Run Story
              <Play :size="14" />
            </button>
          </article>
        </div>

        <div v-if="!stories.length" class="pipeline-empty compact">
          <strong>Story Queue 为空</strong>
          <span>生成 PRD 后，拆分出的 Story 会出现在这里。</span>
        </div>
      </section>

      <aside class="glass-panel pipeline-column">
        <div class="pipeline-section-head">
          <h3><GitPullRequestArrow :size="18" /> Run Detail</h3>
          <span v-if="selectedRun" class="chip" :class="statusClass(selectedRun.status)">
            {{ selectedRun.status }}
          </span>
        </div>

        <div v-if="selectedRun" class="pipeline-run-detail">
          <div class="pipeline-run-title">
            <h4>{{ selectedRun.title }}</h4>
            <p>{{ selectedRun.id }}</p>
          </div>

          <button
            v-if="sequentialDefinition && selectedRun.pipeline_id === sequentialDefinition.id"
            class="primary-button pipeline-wide-action"
            :disabled="busy || selectedRun.status === 'done'"
            @click="$emit('execute-run', selectedRun.id)"
          >
            <Loader2 v-if="busy" :size="15" class="spin-icon" />
            <CheckCircle2 v-else :size="15" />
            Execute Sequential Run
          </button>

          <div class="pipeline-stage-run-list">
            <article
              v-for="stage in selectedRun.stage_runs"
              :key="stage.id"
              class="pipeline-stage-run"
            >
              <div>
                <strong>{{ stageName(stage) }}</strong>
                <span>attempt {{ stage.attempt }}</span>
              </div>
              <span class="chip" :class="statusClass(stage.status)">{{ stage.status }}</span>
            </article>
          </div>

          <div class="pipeline-artifact-list">
            <article
              v-for="artifact in visibleArtifacts"
              :key="artifact.id"
              class="pipeline-artifact-card"
            >
              <div class="pipeline-artifact-head">
                <span class="chip chip-blue">{{ artifact.artifact_type }}</span>
                <strong>{{ artifact.name }}</strong>
              </div>
              <pre>{{ artifactPreview(artifact) }}</pre>
            </article>
          </div>
        </div>

        <div v-else class="pipeline-empty">
          <Play :size="22" />
          <strong>暂无 Run</strong>
          <span>先生成 PRD/story，或从 Story Queue 启动一个 sequential run。</span>
        </div>
      </aside>
    </section>
  </div>
</template>
