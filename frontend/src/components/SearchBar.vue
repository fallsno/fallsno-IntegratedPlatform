<template>
  <div class="search-bar">
    <el-autocomplete
      v-model="searchText"
      :fetch-suggestions="querySearch"
      placeholder="输入汉字、代号搜索..."
      @select="handleSelect"
      @keyup.enter="handleSearch"
      style="width: 400px"
    >
      <template #default="{ item }">
        <div>{{ item.term }}</div>
      </template>
    </el-autocomplete>
    <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon>搜索</el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
const searchText = ref('')
const emit = defineEmits(['search', 'select'])
const querySearch = async (q, cb) => {
  if (!q) return cb([])
  const res = await axios.get('/search/suggestions', { params: { prefix: q } })
  cb(res.data)
}
const handleSelect = (item) => emit('select', item)
const handleSearch = () => { if (searchText.value) emit('search', searchText.value) }
</script>
