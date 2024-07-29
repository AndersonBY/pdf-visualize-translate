<script setup>
import { ref, reactive, watch, onMounted, onUnmounted } from 'vue';
import { message } from 'ant-design-vue';
import { AlignTextLeft, AlignTextRight, AlignTextCenter, AlignTextBoth, Translate } from '@icon-park/vue-next';
import { chatModelOptions } from '@/utils/common';

const props = defineProps({
  currentBlockIndex: { type: Number, default: null },
  modelSelection: { type: Array, default: () => [] },
});
const emit = defineEmits(['saveBlocks', 'deleteBlock']);

const originalText = ref('');
const translatedText = ref('');
const alignment = ref(0);
const fontSize = ref(10);
const fontColor = reactive({
  r: 0,
  g: 0,
  b: 0,
});
const extraRequirements = ref('');
const currentBlock = ref(null);
const pageInfo = defineModel();
const modelSelection = ref(props.modelSelection);

const panelRef = ref(null);

watch(() => props.currentBlockIndex, updateTranslationPanel);

function updateTranslationPanel() {
  if (pageInfo.value && pageInfo.value.blocks && props.currentBlockIndex !== null) {
    currentBlock.value = pageInfo.value.blocks[props.currentBlockIndex];
    originalText.value = currentBlock.value.text;
    translatedText.value = currentBlock.value.translated ? currentBlock.value.translation : '';
    alignment.value = currentBlock.value.align || 0;
    fontSize.value = currentBlock.value.font_size || 10;
    fontColor.r = currentBlock.value.color?.[0] || 0;
    fontColor.g = currentBlock.value.color?.[1] || 0;
    fontColor.b = currentBlock.value.color?.[2] || 0;
  } else {
    originalText.value = '';
    translatedText.value = '';
    alignment.value = 0;
    currentBlock.value = null;
  }
}

const autoTranslating = ref(false)
async function autoTranslate(text = null) {
  if (!text) {
    message.error('Please input text to translate');
    return;
  }

  try {
    autoTranslating.value = true;
    const response = await fetch('/api/translate_block', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        model_selection: modelSelection.value,
        extra_requirements: extraRequirements.value,
      })
    });

    if (!response.ok) {
      throw new Error('Failed to auto translate');
    }

    const data = await response.json();
    translatedText.value = data.translation;
  } catch (error) {
    console.error('Error auto translating:', error);
    message.error('Failed to auto translate: ' + error.message);
  } finally {
    autoTranslating.value = false;
    return translatedText.value;
  }
}

defineExpose({
  autoTranslate,
  saveBlocks,
});

function saveBlocks() {
  if (!currentBlock.value) return;
  pageInfo.value.blocks[props.currentBlockIndex].translated = true;
  pageInfo.value.blocks[props.currentBlockIndex].translation = translatedText.value;
  pageInfo.value.blocks[props.currentBlockIndex].align = alignment.value;
  pageInfo.value.blocks[props.currentBlockIndex].font_size = fontSize.value;
  pageInfo.value.blocks[props.currentBlockIndex].color = [fontColor.r, fontColor.g, fontColor.b];
  emit('saveBlocks', [pageInfo.value.blocks[props.currentBlockIndex]]);
}

function deleteBlock() {
  emit('deleteBlock', props.currentBlockIndex);
}

function handleGlobalKeyDown(event) {
  if (event.ctrlKey && event.key === 's') {
    event.preventDefault(); // 总是阻止默认行为
    saveBlocks();
  } else if (event.ctrlKey && event.key === 'd') {
    event.preventDefault();
    if (!autoTranslating.value) {
      autoTranslating.value = true;
      autoTranslate(originalText.value);
    }
  }
}

onMounted(() => {
  updateTranslationPanel();
  // 在全局范围内添加事件监听器
  document.addEventListener('keydown', handleGlobalKeyDown, true);
});

onUnmounted(() => {
  // 移除全局事件监听器
  document.removeEventListener('keydown', handleGlobalKeyDown);
});
</script>

<template>
  <a-flex vertical gap="small" id="translation-panel" class="mt-3" ref="panelRef">
    <a-typography-title :level="3" class="text-lg font-bold mb-2">Translation</a-typography-title>
    <a-textarea v-model:value="originalText" :auto-size="{ minRows: 1, maxRows: 5 }"></a-textarea>
    <a-collapse :bordered="false">
      <a-collapse-panel key="1">
        <template #header>
          <a-flex justify="space-between">
            <a-typography-text>AI Settings</a-typography-text>
            <a-typography-text>{{ modelSelection[0] }}/{{ modelSelection[1] }}</a-typography-text>
          </a-flex>
        </template>
        <a-cascader style="width: 100%;" v-model:value="modelSelection" :options="chatModelOptions" />
        <a-flex vertical :gap="2">
          <a-typography-text>Extra Requirements</a-typography-text>
          <a-textarea v-model:value="extraRequirements" :auto-size="{ minRows: 2, maxRows: 5 }" />
        </a-flex>
      </a-collapse-panel>
    </a-collapse>
    <a-button type="primary" ghost @click="autoTranslate(originalText)" :loading="autoTranslating">
      <template #icon>
        <Translate />
      </template>
      Auto Translate (Ctrl+D)
    </a-button>
    <a-textarea v-model:value="translatedText" :auto-size="{ minRows: 2, maxRows: 15 }"></a-textarea>
    <a-flex gap="small" align="center" justify="space-between">
      <a-typography-text>Text Align</a-typography-text>
      <a-radio-group v-model:value="alignment">
        <a-radio-button :value="0">
          <AlignTextLeft />
        </a-radio-button>
        <a-radio-button :value="1">
          <AlignTextCenter />
        </a-radio-button>
        <a-radio-button :value="2">
          <AlignTextRight />
        </a-radio-button>
        <a-radio-button disabled :value="3">
          <AlignTextBoth />
        </a-radio-button>
      </a-radio-group>
    </a-flex>
    <a-flex gap="small" align="center" justify="space-between">
      <a-typography-text>Font Size</a-typography-text>
      <a-input-number v-model:value="fontSize" :min="1" :max="100" :step="0.5" />
    </a-flex>
    <a-flex gap="small" align="center" justify="space-between">
      <a-typography-text style="word-break: keep-all;">RGB</a-typography-text>
      <a-input-number v-model:value="fontColor.r" :min="0" :max="1" :step="0.1" />
      <a-input-number v-model:value="fontColor.g" :min="0" :max="1" :step="0.1" />
      <a-input-number v-model:value="fontColor.b" :min="0" :max="1" :step="0.1" />
    </a-flex>
    <a-button type="primary" block @click="saveBlocks">Save Block (Ctrl+S)</a-button>
    <a-button type="primary" danger block @click="deleteBlock">
      Delete Block
    </a-button>
    <a-divider></a-divider>
    <a-flex>
      <a-tag v-if="pageInfo?.blocks?.[props.currentBlockIndex]?.is_extra" color="blue">
        Extra Block
      </a-tag>
      <a-tag v-else color="red">
        Original Block
      </a-tag>
    </a-flex>
    <a-typography-text>
      Original Rect
      {{ pageInfo?.blocks?.[props.currentBlockIndex]?.originalRect }}
    </a-typography-text>
    <a-typography-text>
      New Rect
      {{ pageInfo?.blocks?.[props.currentBlockIndex]?.rect }}
    </a-typography-text>
  </a-flex>
</template>