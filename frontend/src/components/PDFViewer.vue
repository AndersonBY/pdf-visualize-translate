<script setup>
import { onMounted, onUnmounted, watch, ref } from 'vue';
import { ZoomIn, ZoomOut } from '@icon-park/vue-next';
import * as pdfjsLib from 'pdfjs-dist';

const props = defineProps(['pdfPath', 'currentPage', 'showAllTranslations']);
const emit = defineEmits(['updateTotalPages', 'selectBlock', 'splitBlock']);

const pageInfo = defineModel();

const pdfViewer = ref(null);
let pdfDoc;
let pdfPage;
const scale = ref(1.5);
const viewport = ref();
const textBlocks = ref([]);
const showTextBlocks = ref(false);
const showAllTranslations = ref(false);

const currentHoverBlock = ref(null);
function popoverChange(visible, blockIndex) {
  if (visible) {
    currentHoverBlock.value = blockIndex;
  } else {
    currentHoverBlock.value = null;
  }
}

function handleGlobalKeyDown(event) {
  if (event.ctrlKey && event.key === 'e') {
    event.preventDefault(); // 总是阻止默认行为
    if (currentHoverBlock.value !== null) {
      reselectBlock(currentHoverBlock.value);
    }
  }
}

// 确保在组件卸载时清理 PDF 对象
onUnmounted(() => {
  if (pdfDoc) {
    pdfDoc.destroy();
    pdfDoc = null;
  }
  document.removeEventListener('keydown', handleGlobalKeyDown);
});

onMounted(() => {
  pdfjsLib.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.mjs', import.meta.url).toString();
  if (props.pdfPath) {
    loadPDF();
  }
  document.addEventListener('keydown', handleGlobalKeyDown, true);
});

watch(() => props.currentPage, (newValue, oldValue) => {
  if (oldValue !== newValue) {
    showTextBlocks.value = true;
  }
  renderPage();
});
watch(() => props.pdfPath, loadPDF);
watch(() => props.showAllTranslations, (value) => {
  if (value) {
    drawTextBlocks(pageInfo.value.blocks);
  }
  showAllTranslations.value = value;
});

async function loadPDF() {
  if (!props.pdfPath) return;

  try {
    // 如果已经有一个 PDF 文档打开，先销毁它
    if (pdfDoc) {
      pdfDoc.destroy();
    }

    // 使用 .promise 来等待 PDF 加载完成
    pdfDoc = await pdfjsLib.getDocument(props.pdfPath).promise;
    emit('updateTotalPages', pdfDoc.numPages);
    await renderPage();
  } catch (error) {
    console.error('Error loading PDF:', error);
  }
}

async function renderPage() {
  if (!pdfDoc) return;

  try {
    pdfPage = await pdfDoc.getPage(props.currentPage + 1);
    viewport.value = pdfPage.getViewport({ scale: scale.value });

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.height = viewport.value.height;
    canvas.width = viewport.value.width;

    const renderContext = {
      canvasContext: context,
      viewport: viewport.value
    };

    await pdfPage.render(renderContext).promise;

    if (pdfViewer.value) {
      pdfViewer.value.innerHTML = '';
      pdfViewer.value.appendChild(canvas);
      // 只有在成功渲染后才获取页面信息
      await fetchPageInfo();
    }
  } catch (error) {
    console.error('Error rendering page:', error);
  }
}

function splitBlock(blockIndex) {
  const block = pageInfo.value.blocks[blockIndex];
  const rect = block.rect;
  const midX = (rect[0] + rect[2]) / 2;

  const newBlock1 = {
    index: blockIndex,
    translation: null,
    ...block,
    originalRect: block.rect,
    rect: [rect[0], rect[1], midX, rect[3]]
  };
  pageInfo.value.blocks.splice(blockIndex, 1, newBlock1);

  const block2Index = pageInfo.value.blocks.length;
  const newBlock2 = {
    index: block2Index,
    translation: null,
    ...block,
    originalRect: [midX, rect[1], rect[2], rect[3]],
    rect: [midX, rect[1], rect[2], rect[3]],
    is_extra: true
  };

  pageInfo.value.blocks.splice(block2Index, 0, newBlock2);

  drawTextBlocks(pageInfo.value.blocks);
  emit('splitBlock', [newBlock1, newBlock2]);
}

async function fetchPageInfo() {
  try {
    const response = await fetch('/api/get_page_info', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ page_num: props.currentPage })
    });

    if (!response.ok) {
      throw new Error('Failed to fetch page info');
    }

    const data = await response.json();
    pageInfo.value = data;
    drawTextBlocks(data.blocks);
  } catch (error) {
    console.error('Error fetching page info:', error);
  }
}

defineExpose({
  renderPage,
  splitBlock,
  fetchPageInfo,
});


function drawTextBlocks(blocks) {
  textBlocks.value = blocks.map((block, index) => ({
    ...block,
    style: {
      position: 'absolute',
      left: `${viewport.value.width * block.rect[0] / pageInfo.value.width}px`,
      top: `${viewport.value.height * block.rect[1] / pageInfo.value.height}px`,
      width: `${viewport.value.width * (block.rect[2] - block.rect[0]) / pageInfo.value.width}px`,
      height: `${viewport.value.height * (block.rect[3] - block.rect[1]) / pageInfo.value.height}px`,
      fontSize: `${block.font_size}px`,
      color: block.color,
      textAlign: getAlignment(block.align),
    },
    index
  }));
  showTextBlocks.value = true;
}

function getAlignment(align) {
  switch (parseInt(align)) {
    case 1: return 'center';
    case 2: return 'right';
    case 3: return 'justify';
    default: return 'left';
  }
}

function reselectBlock(blockIndex) {
  emit('selectBlock', blockIndex)

  // 创建一个透明的 canvas 覆盖在原来的 canvas 上
  const overlayCanvas = document.createElement('canvas');
  overlayCanvas.width = viewport.value.width;
  overlayCanvas.height = viewport.value.height;
  overlayCanvas.style.position = 'absolute';
  overlayCanvas.style.left = '0';
  overlayCanvas.style.top = '0';
  overlayCanvas.style.zIndex = '1000';
  overlayCanvas.style.cursor = 'crosshair';
  pdfViewer.value.appendChild(overlayCanvas);

  let isSelecting = false;
  let startX, startY;

  overlayCanvas.addEventListener('mousedown', startSelection);
  overlayCanvas.addEventListener('mousemove', updateSelection);
  overlayCanvas.addEventListener('mouseup', endSelection);

  function startSelection(e) {
    isSelecting = true;
    const rect = overlayCanvas.getBoundingClientRect();
    startX = e.clientX - rect.left;
    startY = e.clientY - rect.top;
  }

  function updateSelection(e) {
    if (!isSelecting) return;
    const rect = overlayCanvas.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;

    const ctx = overlayCanvas.getContext('2d');
    ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    ctx.strokeStyle = 'blue';
    ctx.lineWidth = 2;
    ctx.strokeRect(startX, startY, currentX - startX, currentY - startY);
  }

  function endSelection(e) {
    if (!isSelecting) return;
    isSelecting = false;
    const rect = overlayCanvas.getBoundingClientRect();
    const endX = e.clientX - rect.left;
    const endY = e.clientY - rect.top;

    const newRect = [
      Math.min(startX, endX) / viewport.value.width * pageInfo.value.width,
      Math.min(startY, endY) / viewport.value.height * pageInfo.value.height,
      Math.max(startX, endX) / viewport.value.width * pageInfo.value.width,
      Math.max(startY, endY) / viewport.value.height * pageInfo.value.height
    ];

    // 更新 block 的位置
    pageInfo.value.blocks[blockIndex].rect = newRect;

    // 清除事件监听器和 overlay canvas
    overlayCanvas.removeEventListener('mousedown', startSelection);
    overlayCanvas.removeEventListener('mousemove', updateSelection);
    overlayCanvas.removeEventListener('mouseup', endSelection);
    pdfViewer.value.removeChild(overlayCanvas);

    // 重新绘制文本块
    drawTextBlocks(pageInfo.value.blocks);
  }
}

function changeScale(newScale) {
  scale.value = newScale;
  renderPage();
}
</script>

<template>
  <div id="pdf-container">
    <div id="pdf-viewer" ref="pdfViewer" class="custom-scrollbar">
    </div>
    <template v-if="showTextBlocks">
      <a-popover v-for="block in textBlocks" :key="block.index" @openChange="popoverChange($event, block.index)">
        <template #content>
          <a-flex vertical gap="small" class="max-w-80">
            <a-typography-paragraph :content="block.translated ? block.translation : 'Not translated yet'" />
            <a-button type="primary" block @click="splitBlock(block.index)">Split Block</a-button>
            <a-button type="primary" block @click="reselectBlock(block.index)">Reselect Block</a-button>
          </a-flex>
        </template>
        <div class="text-block border-2 hover:border-blue-500 transition-colors duration-200"
          :class="block.translated ? 'border-green-500' : 'border-red-500'" :style="block.style"
          @click="emit('selectBlock', block.index)"></div>
      </a-popover>
    </template>
    <template v-if="showAllTranslations">
      <div v-for="block in textBlocks" :key="block.index" class="absolute bg-white bg-opacity-80 p-1 translate-block"
        :style="block.style">
        {{ block.translated ? block.translation : '' }}
      </div>
    </template>

    <a-float-button-group shape="square">
      <a-float-button @click="changeScale(scale + 0.1)">
        <template #icon>
          <ZoomIn />
        </template>
      </a-float-button>

      <a-float-button @click="changeScale(scale - 0.1)">
        <template #icon>
          <ZoomOut />
        </template>
      </a-float-button>
      <a-back-top :visibility-height="0" />
    </a-float-button-group>
  </div>
</template>

<style scoped>
#pdf-container {
  position: relative;
  margin-bottom: 40px;
}

.text-block {
  position: absolute;
  cursor: pointer;
}

.translate-block {
  pointer-events: none;
}
</style>