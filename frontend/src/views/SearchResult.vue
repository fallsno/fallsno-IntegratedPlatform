<template>
  <div class="search-result">
    <h2>搜索结果：{{ keyword }}</h2>
    <el-table :data="results" stripe>
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.type === 'family' ? 'success' : 'info'">
            {{ row.type === 'family' ? '型号' : '部件' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="main_code" label="代号" width="200" />
      <el-table-column prop="name" label="名称" />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button link type="primary" @click="goToDetail(row)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const keyword = ref(route.query.q || '')
const results = ref([])

onMounted(async () => {
  if (keyword.value) {
    const res = await axios.get('/search/', { params: { keyword: keyword.value } })
    results.value = res.data
  }
})

const goToDetail = (row) => {
  if (row.type === 'family') {
    router.push({ name: 'Versions', params: { familyId: row.id } })
  } else {
    // 部件跳转到对应版本页面
    router.push({ name: 'Versions', params: { familyId: row.family_id } })
  }
}
</script>