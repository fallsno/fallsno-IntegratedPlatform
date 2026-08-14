export function getRouteShellMode(route = {}) {
  const explicitMode = String(route?.meta?.shellMode || '').trim()
  if (explicitMode) {
    return explicitMode
  }
  if (route?.name === 'DesignWorkbench') {
    return 'page-managed'
  }
  return 'standard'
}

export function shouldUseGlobalDesignChrome(route = {}) {
  return getRouteShellMode(route) === 'legacy-design'
}
