<template>
  <div class="position-relative" @click.stop>
    <el-input
      ref="expressionRef"
      type="textarea"
      :autosize="{ minRows: 1, maxRows: 4 }"
      :model-value="formula.expression"
      placeholder="输入表达式，例如 =托轮摩擦力矩*滚筒转速/9550"
      @input="handleExpressionInput"
      @click="captureSelection"
      @focus="captureSelection"
      @keyup="captureSelection"
      @keydown.enter.prevent.stop="emit('save')"
      @keydown.esc.prevent.stop="emit('cancel')"
      @compositionstart="handleCompositionStart"
      @compositionend="handleCompositionEnd"
    />
    <div v-if="argumentHint" class="formula-argument-hint">
      <span class="formula-argument-hint__title">{{ argumentHint.functionName }} / {{ argumentHint.label }}</span>
      <span class="formula-argument-hint__text">{{ argumentHint.description }}</span>
    </div>
    <div v-if="autocompleteSections.length" class="autocomplete-panel">
      <div
        v-for="section in autocompleteSections"
        :key="section.label"
        class="autocomplete-section"
      >
        <div class="autocomplete-section__title">{{ section.label }}</div>
        <button
          v-for="item in section.items"
          :key="`${section.label}-${item.value}`"
          type="button"
          class="autocomplete-item"
          @click.stop="insertAutocompleteItem(item)"
        >
          <span>{{ item.label }}</span>
          <span class="autocomplete-item__meta">
            {{ item.group || section.label }}<template v-if="item.description"> · {{ item.description }}</template><template v-else-if="item.sourceFormula"> · {{ item.sourceFormula }}</template>
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { resolveFormulaAutocompleteInsertion } from '@/api/drumDesign.helpers.mjs'

const props = defineProps({
  formula: {
    type: Object,
    default: () => ({})
  },
  loading: {
    type: Boolean,
    default: false
  },
  autocompleteSections: {
    type: Array,
    default: () => []
  },
  argumentHint: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['change', 'save', 'cancel', 'selection-change'])

const expressionRef = ref(null)
const selectionRange = ref({ start: 0, end: 0 })
const isComposing = ref(false)

const updateField = (field, value) => {
  emit('change', { field, value })
}

const captureSelection = () => {
  const textarea = expressionRef.value?.textarea
  if (!textarea) return
  selectionRange.value = {
    start: textarea.selectionStart || 0,
    end: textarea.selectionEnd || 0
  }
  emit('selection-change', {
    ...selectionRange.value,
    isComposing: isComposing.value
  })
}

const handleExpressionInput = (value) => {
  updateField('expression', value)
  captureSelection()
}

const handleCompositionStart = () => {
  isComposing.value = true
  emit('selection-change', {
    ...selectionRange.value,
    isComposing: true
  })
}

const handleCompositionEnd = () => {
  isComposing.value = false
  captureSelection()
}

const insertAutocompleteItem = async (item) => {
  const resolved = resolveFormulaAutocompleteInsertion({
    expression: props.formula?.expression,
    selectionStart: selectionRange.value.start,
    selectionEnd: selectionRange.value.end,
    insertedValue: item.value
  })
  updateField('expression', resolved.nextValue)
  await nextTick()
  const textarea = expressionRef.value?.textarea
  textarea?.focus()
  textarea?.setSelectionRange(resolved.nextSelectionStart, resolved.nextSelectionEnd)
  captureSelection()
}
</script>

<style scoped>
.position-relative {
  position: relative;
}

.formula-argument-hint {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
  padding: 6px 10px;
  border-radius: 8px;
  background: #f8fafc;
  color: #334155;
  font-size: 12px;
}

.formula-argument-hint__title {
  font-weight: 700;
  color: #0f172a;
}

.autocomplete-panel {
  display: grid;
  gap: 6px;
  margin-top: 6px;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 10;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  padding: 6px;
  max-height: 240px;
  overflow-y: auto;
}

.autocomplete-section + .autocomplete-section {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid #e2e8f0;
}

.autocomplete-section__title {
  padding: 0 4px 4px;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.autocomplete-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 10px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background: #eff6ff;
  text-align: left;
  color: #0f172a;
  cursor: pointer;
  font-size: 13px;
}

.autocomplete-item:hover {
  border-color: #60a5fa;
  background: #dbeafe;
}

.autocomplete-item__meta {
  font-size: 12px;
  color: #475569;
}
</style>
