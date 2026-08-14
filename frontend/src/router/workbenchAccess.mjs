export const canEnterExistingDesignWorkbench = ({ typeId, moduleCode } = {}) => (
  Boolean(String(typeId || '').trim() && String(moduleCode || '').trim())
)
