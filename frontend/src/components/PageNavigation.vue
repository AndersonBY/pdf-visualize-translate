<script setup>
import { ref, watch } from 'vue';
import { GoEnd, GoStart } from '@icon-park/vue-next';

const props = defineProps(['currentPage', 'totalPages']);
const emit = defineEmits(['changePage']);

const currentPageInput = ref(props.currentPage + 1);

watch(() => props.currentPage, (newPage) => {
  currentPageInput.value = newPage + 1;
});

watch(currentPageInput, (newPage) => {
  if (newPage >= 1 && newPage <= props.totalPages) {
    emit('changePage', newPage - 1);
  }
});

function prevPage() {
  if (props.currentPage > 0) {
    emit('changePage', props.currentPage - 1);
  }
}

function nextPage() {
  if (props.currentPage < props.totalPages - 1) {
    emit('changePage', props.currentPage + 1);
  }
}
</script>

<template>
  <a-affix :offset-bottom="20">
    <div class="flex items-center space-x-2 mb-4">
      <a-button type="primary" @click="prevPage">
        <template #icon>
          <GoStart />
        </template>
      </a-button>
      <a-input-number v-model:value="currentPageInput" min="1" />
      <span>/</span>
      <span>{{ totalPages }}</span>
      <a-button type="primary" @click="nextPage">
        <template #icon>
          <GoEnd />
        </template>
      </a-button>
    </div>
  </a-affix>
</template>
