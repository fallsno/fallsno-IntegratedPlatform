<template>
  <div 
    :class="[
      'flow-card',
      `flow-card--${type}`,
      { 
        'flow-card--selected': selected,
        'flow-card--hover': hoverable,
        'flow-card--disabled': disabled,
        'fade-in': animate
      }
    ]"
    :style="cardStyle"
    @click="handleClick"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <!-- 卡片头部 -->
    <div v-if="showHeader" class="card-header">
      <div class="card-header-left">
        <div v-if="icon" class="card-icon">
          {{ icon }}
        </div>
        <div class="card-title-wrapper">
          <div class="card-title">{{ title }}</div>
          <div v-if="subtitle" class="card-subtitle">{{ subtitle }}</div>
        </div>
      </div>
      <div v-if="showBadge" class="card-badge" :class="`badge--${badgeType}`">
        {{ badgeText }}
      </div>
    </div>

    <!-- 卡片内容 -->
    <div v-if="showContent" class="card-content">
      <slot name="content">
        <div v-if="content" class="card-content-text">{{ content }}</div>
        <div v-if="value" class="card-value">
          <span class="card-value-number">{{ value }}</span>
          <span v-if="unit" class="card-value-unit">{{ unit }}</span>
        </div>
      </slot>
    </div>

    <!-- 卡片底部 -->
    <div v-if="showFooter" class="card-footer">
      <slot name="footer">
        <div v-if="meta" class="card-meta">
          <span v-if="metaIcon" class="card-meta-icon">{{ metaIcon }}</span>
          <span class="card-meta-text">{{ meta }}</span>
        </div>
        <div v-if="status" class="card-status" :class="`status--${status}`">
          {{ statusText }}
        </div>
      </slot>
    </div>

    <!-- 选中指示器 -->
    <div v-if="selected" class="card-selection-indicator"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 基础属性
  title: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'calculation',
    validator: (value) => ['input', 'calculation', 'output'].includes(value)
  },
  
  // 内容属性
  subtitle: {
    type: String,
    default: ''
  },
  content: {
    type: String,
    default: ''
  },
  value: {
    type: [String, Number],
    default: ''
  },
  unit: {
    type: String,
    default: ''
  },
  
  // 视觉属性
  icon: {
    type: String,
    default: ''
  },
  color: {
    type: String,
    default: ''
  },
  backgroundColor: {
    type: String,
    default: ''
  },
  
  // 状态属性
  selected: {
    type: Boolean,
    default: false
  },
  hoverable: {
    type: Boolean,
    default: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  animate: {
    type: Boolean,
    default: true
  },
  
  // 徽章属性
  showBadge: {
    type: Boolean,
    default: false
  },
  badgeText: {
    type: String,
    default: ''
  },
  badgeType: {
    type: String,
    default: 'info',
    validator: (value) => ['info', 'success', 'warning', 'error'].includes(value)
  },
  
  // 元信息
  meta: {
    type: String,
    default: ''
  },
  metaIcon: {
    type: String,
    default: ''
  },
  
  // 状态
  status: {
    type: String,
    default: '',
    validator: (value) => ['', 'success', 'warning', 'error', 'pending'].includes(value)
  },
  statusText: {
    type: String,
    default: ''
  },
  
  // 显示控制
  showHeader: {
    type: Boolean,
    default: true
  },
  showContent: {
    type: Boolean,
    default: true
  },
  showFooter: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'mouseenter', 'mouseleave'])

// 计算卡片样式
const cardStyle = computed(() => {
  const style = {}
  
  if (props.color) {
    style.color = props.color
  }
  
  if (props.backgroundColor) {
    style.backgroundColor = props.backgroundColor
  }
  
  return style
})

// 计算状态文本
const statusText = computed(() => {
  if (props.statusText) {
    return props.statusText
  }
  
  const statusMap = {
    success: '成功',
    warning: '警告',
    error: '错误',
    pending: '处理中'
  }
  
  return statusMap[props.status] || ''
})

// 事件处理
const handleClick = (event) => {
  if (props.disabled) return
  emit('click', event)
}

const handleMouseEnter = (event) => {
  if (props.disabled) return
  emit('mouseenter', event)
}

const handleMouseLeave = (event) => {
  if (props.disabled) return
  emit('mouseleave', event)
}
</script>

<style scoped>
@import '@/assets/styles/workbench-formula-flow.css';

/* 卡片特定样式 */
.flow-card {
  position: relative;
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-header-left {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.card-icon {
  font-size: 18px;
  line-height: 1;
  margin-top: 2px;
  flex-shrink: 0;
}

.card-title-wrapper {
  min-width: 0;
  flex: 1;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.4;
  margin-bottom: 2px;
  word-break: break-word;
}

.card-subtitle {
  font-size: 11px;
  color: #64748b;
  line-height: 1.4;
}

/* 徽章 */
.card-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 500;
  line-height: 1.2;
  white-space: nowrap;
  flex-shrink: 0;
}

.badge--info {
  background: #dbeafe;
  color: #1d4ed8;
}

.badge--success {
  background: #d1fae5;
  color: #065f46;
}

.badge--warning {
  background: #fef3c7;
  color: #92400e;
}

.badge--error {
  background: #fee2e2;
  color: #991b1b;
}

/* 卡片内容 */
.card-content {
  margin-bottom: 12px;
}

.card-content-text {
  font-size: 12px;
  color: #475569;
  line-height: 1.5;
  margin-bottom: 8px;
}

.card-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.card-value-number {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.card-value-unit {
  font-size: 12px;
  color: #64748b;
}

/* 卡片底部 */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #64748b;
}

.card-meta-icon {
  font-size: 10px;
}

.card-status {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 10px;
  white-space: nowrap;
}

.status--success {
  background: #d1fae5;
  color: #065f46;
}

.status--warning {
  background: #fef3c7;
  color: #92400e;
}

.status--error {
  background: #fee2e2;
  color: #991b1b;
}

.status--pending {
  background: #f3f4f6;
  color: #4b5563;
}

/* 选中指示器 */
.card-selection-indicator {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: #3b82f6;
  border-radius: 2px 2px 0 0;
}

/* 类型特定颜色 */
.flow-card--input {
  border-left-color: #3b82f6;
}

.flow-card--calculation {
  border-left-color: #64748b;
}

.flow-card--output {
  border-left-color: #f97316;
}

/* 悬停效果 */
.flow-card--hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
}

/* 禁用状态 */
.flow-card--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.flow-card--disabled:hover {
  transform: none;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}
</style>