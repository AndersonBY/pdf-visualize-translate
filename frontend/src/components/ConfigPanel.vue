<script setup>
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import { chatModelOptions } from '@/utils/common';

const config = ref({
  pdfPath: '',
  outputJsonPath: '',
  translatedPdfPath: '',
  fontName: '',
  fontFile: '',
  targetLanguage: '',
  modelSelection: [],
});
const formRef = ref();
const initializing = ref(false);

const emit = defineEmits(['init']);

async function loadConfig() {
  try {
    const response = await fetch('/api/get_config');
    if (!response.ok) {
      throw new Error('Failed to load config');
    }
    const data = await response.json();
    config.value = {
      pdfPath: data.pdf_path || '',
      outputJsonPath: data.output_json_path || '',
      translatedPdfPath: data.translated_pdf_path || '',
      fontName: data.font_name || '',
      fontFile: data.font_file || '',
      targetLanguage: data.target_language || '',
      modelSelection: data.model_selection || [],
    };
    message.success('Config loaded successfully');
  } catch (error) {
    console.error('Error loading config:', error);
    message.error('Failed to load config: ' + error.message);
  }
}

async function saveConfig() {
  try {
    await formRef.value.validate()
  } catch (error) {
    console.error(error)
    return
  }

  try {
    const response = await fetch('/api/save_config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pdf_path: config.value.pdfPath,
        output_json_path: config.value.outputJsonPath,
        translated_pdf_path: config.value.translatedPdfPath,
        font_name: config.value.fontName,
        font_file: config.value.fontFile,
        target_language: config.value.targetLanguage,
        model_selection: config.value.modelSelection,
      })
    });

    if (!response.ok) {
      throw new Error(response);
    }

    const data = await response.json();
    if (data.status === 'success') {
      message.success('Config saved successfully!');
    } else {
      throw new Error(data.message || 'Unknown error occurred');
    }
  } catch (error) {
    console.error('Error saving config:', error);
    message.error('Failed to save config: ' + error);
  }
}

async function initTranslator() {
  try {
    await formRef.value.validate()
  } catch (error) {
    console.error(error)
    return
  }

  try {
    initializing.value = true;
    const response = await fetch('/api/init_translator', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pdf_path: config.value.pdfPath,
        output_json_path: config.value.outputJsonPath,
        translated_pdf_path: config.value.translatedPdfPath,
        font_name: config.value.fontName,
        font_file: config.value.fontFile,
        target_language: config.value.targetLanguage,
        model_selection: config.value.modelSelection,
      })
    });

    if (!response.ok) {
      throw new Error(response);
    }

    const data = await response.json();
    if (data.status === 'success') {
      message.success('Translator initialized successfully!');
      emit('init', config.value);
    } else {
      throw new Error(data.message || 'Unknown error occurred');
    }
  } catch (error) {
    console.log(error);
    console.error('Error initializing translator:', error);
    message.error('Failed to initialize translator: ' + error.message);
  } finally {
    initializing.value = false;
  }
}
</script>

<template>
  <a-form ref="formRef" :model="config" layout="vertical" class="mb-3">
    <a-form-item label="PDF Path" name="pdfPath" required>
      <a-input v-model:value="config.pdfPath" placeholder="Enter PDF Path" />
    </a-form-item>
    <a-form-item label="Output JSON Path" name="outputJsonPath" required>
      <a-input v-model:value="config.outputJsonPath" placeholder="Enter Output JSON Path" />
    </a-form-item>
    <a-form-item label="Translated PDF Path" name="translatedPdfPath" required>
      <a-input v-model:value="config.translatedPdfPath" placeholder="Enter Translated PDF Path" />
    </a-form-item>
    <a-form-item label="Font Name" name="fontName" required>
      <a-input v-model:value="config.fontName" placeholder="Enter Font Name" />
    </a-form-item>
    <a-form-item label="Font File" name="fontFile" required>
      <a-input v-model:value="config.fontFile" placeholder="Enter Font File" />
    </a-form-item>
    <a-form-item label="Target Language" name="targetLanguage" required>
      <a-input v-model:value="config.targetLanguage" placeholder="Enter Target Language" />
    </a-form-item>
    <a-form-item label="Model Selection" name="modelSelection" required>
      <a-cascader style="width: 100%;" v-model:value="config.modelSelection" :options="chatModelOptions" />
    </a-form-item>
    <a-divider></a-divider>
    <a-flex vertical gap="small">
      <a-flex gap="small" justify="center">
        <a-button @click="loadConfig" type="default">Load Config From config.json</a-button>
        <a-button @click="saveConfig" type="default">Save Config To config.json</a-button>
      </a-flex>
      <a-button block type="primary" size="large" @click="initTranslator" :loading="initializing">
        Initialize Translator
      </a-button>
    </a-flex>
  </a-form>
</template>