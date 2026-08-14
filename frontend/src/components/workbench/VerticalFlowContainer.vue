<template>
  <div class="vertical-flow-container">
    <!-- 输入层 -->
    <div v-if="showInputLayer" class="input-layer">
      <div class="layer-title">
        <span class="layer-icon">📥</span>
        {{ inputLayerTitle }}
      </div>
      <div class="card-grid-container">
        <slot name="input-layer">
          <!-- 默认插槽内容 -->
          <div v-for="(item, index) in inputItems" :key="index" class="flow-card flow-card--input">
            <div class="card-title">{{ item.title }}</div>
            <div class="card-content">{{ item.content }}</div>
            <div v-if="item.meta" class="card-meta">
              <span>{{ item.meta }}</span>
            </div>
          </div>
        </slot>
      </div>
    </div>

    <!-- 流向指示器 -->
    <div v-if="showInputLayer && showCalculationLayer" class="flow-connections">
      <div class="vertical-flow-indicator"></div>
    </div>

    <!-- 计算层 -->
    <div v-if="showCalculationLayer" class="calculation-layer">
      <div class="layer-title">
        <span class="layer-icon">⚙️</span>
        {{ calculationLayerTitle }}
      </div>
      <div class="card-grid-container">
        <slot name="calculation-layer">
          <!-- 默认插槽内容 -->
          <div v-for="(item, index) in calculationItems" :key="index" class="flow-card flow-card--calculation">
            <div class="card-title">{{ item.title }}</div>
            <div class="card-content">{{ item.content }}</div>
            <div v-if="item.meta" class="card-meta">
              <span>{{ item.meta }}</span>
            </div>
          </div>
        </slot>
      </div>
    </div>

    <!-- 流向指示器 -->
    <div v-if="showCalculationLayer && showOutputLayer" class="flow-connections">
      <div class="vertical-flow-indicator"></div>
    </div>

    <!-- 输出层 -->
    <div v-if="showOutputLayer" class="output-layer">
      <div class="layer-title">
        <span class="layer-icon">📤</span>
        {{ outputLayerTitle }}
      </div>
      <div class="card-grid-container">
        <slot name="output-layer">
          <!-- 默认插槽内容 -->
          <div v-for="(item, index) in outputItems" :key="index" class="flow-card flow-card--output">
            <div class="card-title">{{ item.title }}</div>
            <div class="card-content">{{ item.content }}</div>
            <div v-if="item.meta" class="card-meta">
              <span>{{ item.meta }}</span>
            </div>
          </div>
        </slot>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="isEmpty" class="empty-state">
      <div class="empty-icon">📊</div>
      <div class="empty-title">{{ emptyTitle }}</div>
      <div class="empty-description">{{ emptyDescription }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 层显示控制
  showInputLayer: {
    type: Boolean,
    default: true
  },
  showCalculationLayer: {
    type: Boolean,
    default: true
  },
  showOutputLayer: {
    type: Boolean,
    default: true
  },
  
  // 层标题
  inputLayerTitle: {
    type: String,
    default: '输入条件'
  },
  calculationLayerTitle: {
    type: String,
    default: '计算与转换'
  },
  outputLayerTitle: {
    type: String,
    default: '输出结果'
  },
  
  // 默认数据
  inputItems: {
    type: Array,
    default: () => []
  },
  calculationItems: {
    type: Array,
    default: () => []
  },
  outputItems: {
    type: Array,
    default: () => []
  },
  
  // 空状态
  emptyTitle: {
    type: String,
    default: '暂无数据'
  },
  emptyDescription: {
    type: String,
    default: '当前模块暂无可展示的设计推理链路'
  }
})

// 计算是否为空状态
const isEmpty = computed(() => {
  const hasInputItems = props.inputItems.length > 0
  const hasCalculationItems = props.calculationItems.length > 0
  const hasOutputItems = props.outputItems.length > 0
  
  // 检查是否有插槽内容
  const hasSlotContent = false // 这里需要实际检查插槽内容
  
  return !hasInputItems && !hasCalculationItems && !hasOutputItems && !hasSlotContent
})
</script>

<style scoped>
@import '@/assets/styles/workbench-formula-flow.css';

/* 组件特定样式 */
.layer-icon {
  font-size: 18px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;
  color: #64748b;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #475569;
}

.empty-description {
  font-size: 14px;
  max-width: 400px;
  line-height: 1.5;
}
</style>