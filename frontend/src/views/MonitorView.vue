<template>
  <div class="monitor-redirect">
    <el-result
      icon="success"
      title="正在打开滚筒检测服务端"
      sub-title="系统会以新窗口打开监测平台，避免在当前页面内反复叠加嵌入窗口。"
    >
      <template #extra>
        <el-button type="primary" @click="openMonitor">重新打开</el-button>
        <el-button @click="goBack">返回设计平台</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const getMonitorUrl = () => `${window.location.protocol}//${window.location.hostname}:5001/admin`

const openMonitor = () => {
  window.open(getMonitorUrl(), '_blank')
}

const goBack = () => {
  router.replace('/')
}

onMounted(() => {
  openMonitor()
  goBack()
})
</script>

<style scoped>
.monitor-redirect {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 120px);
  background: #fff;
  border-radius: 12px;
}
</style>
