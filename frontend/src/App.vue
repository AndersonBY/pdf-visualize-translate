<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { message } from 'ant-design-vue';
import ConfigPanel from './components/ConfigPanel.vue';
import PDFViewer from './components/PDFViewer.vue';
import TranslationPanel from './components/TranslationPanel.vue';
import PageNavigation from './components/PageNavigation.vue';

const initialized = ref(false);
const currentPage = ref(0);
const pdfViewer = ref(null);
const translationPanel = ref(null);
const pageInfo = ref(null);
const currentBlockIndex = ref(null);
const totalPages = ref(0);
const showAllTranslations = ref(false);
const config = ref({
  pdfPath: '',
  outputJsonPath: '',
  translatedPdfPath: '',
  modelSelection: [],
});

function initTranslator(c) {
  config.value = c;
  initialized.value = true;
  message.success('Translator initialized successfully');
  // 如果 URL 中有 page 参数，使用它作为当前页
  nextTick(() => {
    const url = new URL(window.location.href);
    const page = url.searchParams.get('page');
    if (page) {
      changePage(parseInt(page) - 1);
      showAllTranslations.value = true;
      pdfViewer.value.fetchPageInfo();
    }
  });
}

function updateTotalPages(pages) {
  totalPages.value = pages;
}

function changePage(newPage) {
  currentPage.value = newPage;
  // Reset current block index when changing page
  currentBlockIndex.value = null;
  // Update url with new page number
  const url = new URL(window.location.href);
  url.searchParams.set('page', newPage + 1);
  window.history.pushState({}, '', url);
}

async function saveBlocks(blocks) {
  try {
    const msgKey = 'savingMessage';
    message.loading({ content: 'Saving block...', key: msgKey }, 0);
    for (const block of blocks) {
      const response = await fetch('/api/save_translation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          page_num: currentPage.value,
          block_index: block?.index || currentBlockIndex.value,
          translation: block.translation,
          original: block.text,
          rect: block.originalRect || block.rect,
          new_rect: block.rect,
          font_size: block.font_size,
          color: block.color,
          align: block.align,
        })
      });

      if (!response.ok) {
        throw new Error('Failed to save translation');
      }

      const data = await response.json();
      if (data.status !== 'success') {
        throw new Error(data.message || 'Unknown error occurred');
      }
    }
    message.success({ content: 'Blocks saved!', key: msgKey });
    pdfViewer.value.renderPage();
  } catch (error) {
    console.error('Error saving translation:', error);
    message.error('Failed to save translation: ' + error.message);
  }
}

async function deleteBlock(blockIndex) {
  try {
    const currentBlock = pageInfo.value.blocks[blockIndex]
    const response = await fetch('/api/delete_block', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_num: currentPage.value,
        rect: currentBlock.originalRect || currentBlock.rect,
        original: currentBlock.text,
      })
    });

    if (!response.ok) {
      throw new Error('Failed to delete block');
    }

    const data = await response.json();
    if (data.status === 'success') {
      message.success('Block deleted successfully');
      pdfViewer.value.renderPage();
    } else {
      throw new Error(data.message || 'Unknown error occurred');
    }
  } catch (error) {
    console.error('Error deleting block:', error);
    message.error('Failed to delete block: ' + error.message);
  }
}

const generatingPDF = ref(false)
async function finishTranslation() {
  try {
    generatingPDF.value = true;
    const response = await fetch('/api/finish_translation', {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Failed to finish translation');
    }

    const data = await response.json();
    if (data.status === 'success') {
      message.success(data.message);
    } else {
      throw new Error(data.message || 'Unknown error occurred');
    }
  } catch (error) {
    console.error('Error finishing translation:', error);
    message.error('Failed to finish translation: ' + error.message);
  } finally {
    generatingPDF.value = false;
  }
}

const translatingPage = ref(false);
async function translatePage() {
  if (!pageInfo.value || !pageInfo.value.blocks) return;

  try {
    translatingPage.value = true;
    let index = 0;
    for (const block of pageInfo.value.blocks) {
      if (!block.translated) {
        currentBlockIndex.value = index;
        block.translation = await translationPanel.value.autoTranslate(block.text);
        block.translated = true;
        await saveBlocks([block]);
      }
      index++;
    }
  } catch (error) {
    console.error('Error translating page:', error);
    message.error('Failed to translate page: ' + error.message);
  } finally {
    translatingPage.value = false;
  }
}

function toggleAllTranslations() {
  showAllTranslations.value = !showAllTranslations.value;
}

function selectBlock(index) {
  currentBlockIndex.value = index;
}

const generatingPreview = ref(false);
const previewVisible = ref(false);
const previewImageUrl = ref('');
async function generatePreview() {
  try {
    generatingPreview.value = true;
    const response = await fetch('/api/preview', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_num: currentPage.value
      })
    });

    if (!response.ok) {
      throw new Error('Failed to generate preview');
    }

    // Instead of parsing JSON, we're expecting a blob
    const blob = await response.blob();

    // Create a URL for the blob
    previewImageUrl.value = URL.createObjectURL(blob);

    // Show the modal with the preview image
    previewVisible.value = true;

    message.success('Preview generated successfully');
  } catch (error) {
    console.error('Error generating preview:', error);
    message.error('Failed to generate preview: ' + error.message);
  } finally {
    generatingPreview.value = false;
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload);
});

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload);
});

function handleBeforeUnload(event) {
  event.preventDefault();
  event.returnValue = '';
}
</script>

<template>
  <a-config-provider>
    <a-layout class="min-h-screen p-4">
      <a-layout-content>
        <ConfigPanel v-if="!initialized" @init="initTranslator" />
        <a-flex v-else>
          <PDFViewer ref="pdfViewer" v-model="pageInfo" :pdfPath="config.pdfPath" :currentPage="currentPage"
            :showAllTranslations="showAllTranslations" @updateTotalPages="updateTotalPages" @selectBlock="selectBlock"
            @splitBlock="saveBlocks" />
          <a-affix :offset-top="10" class="affix-container">
            <a-flex vertical gap="small" class="panel custom-scrollbar">
              <a-button @click="generatePreview" :loading="generatingPreview" type="primary">
                Preview Page
              </a-button>
              <a-button @click="finishTranslation" :loading="generatingPDF" type="primary" danger>
                Finish Translation
              </a-button>
              <a-button @click="translatePage" :loading="translatingPage">Translate Page</a-button>
              <a-button @click="toggleAllTranslations">
                {{ showAllTranslations ? 'Hide' : 'Show' }} All Translations
              </a-button>
              <TranslationPanel ref="translationPanel" v-model="pageInfo" :currentBlockIndex="currentBlockIndex"
                :model-selection="config.modelSelection" @saveBlocks="saveBlocks" @deleteBlock="deleteBlock" />
            </a-flex>
          </a-affix>
        </a-flex>

        <PageNavigation v-if="initialized" :currentPage="currentPage" :totalPages="totalPages"
          @changePage="changePage" />
        <a-modal v-model:open="previewVisible" title="Page Preview" :footer="null" width="80%">
          <img :src="previewImageUrl" style="width: 100%;" alt="Page Preview" />
        </a-modal>
      </a-layout-content>
    </a-layout>
  </a-config-provider>
</template>

<style scoped>
.affix-container {
  height: calc(100vh - 20px);
  overflow: visible;
}

.panel {
  width: 300px;
  padding: 0 1rem;
  overflow-y: auto;
  /* 允许垂直滚动 */
  max-height: 100%;
  /* 最大高度为父容器的100% */
}
</style>