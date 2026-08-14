import { createRouter, createWebHistory } from 'vue-router'
import ProductTypes from '../views/ProductTypes.vue'
import ProductComponents from '../views/ProductComponents.vue'
import FamilyList from '../views/FamilyList.vue'
import VersionManage from '../views/VersionManage.vue'
import FormulaLibrary from '../views/FormulaLibrary.vue'
import DesignPointCompare from '../views/DesignPointCompare.vue'
import KnowledgeBase from '../views/KnowledgeBase.vue'
import Dashboard from '../views/Dashboard.vue'
import MonitorView from '../views/MonitorView.vue'
import ParameterCenter from '../views/ParameterCenter.vue'
import TemplateCenter from '../views/TemplateCenter.vue'
import SearchResult from '../views/SearchResult.vue'
import ProductTypeSelection from '../views/ProductTypeSelection.vue'
import ModuleSelection from '../views/ModuleSelection.vue'
import OptimizedWorkbench from '../views/NewDesignWorkbench.vue'
import LegacyWorkbench from '../views/DesignWorkbench.vue'
import DesignGuidance from '../views/DesignGuidance.vue'
import ModelParameterMatrix from '../views/ModelParameterMatrix.vue'
import DrumCatalog from '../views/DrumCatalog.vue'
import TrialList from '../views/lab/TrialList.vue'
import TrialDetail from '../views/lab/TrialDetail.vue'
import TemplateManage from '../views/lab/TemplateManage.vue'
import MaterialManage from '../views/lab/MaterialManage.vue'
import ReportView from '../views/ReportView.vue'
import FormulaTemplateCenter from '../views/FormulaTemplate/TemplateCenter.vue'
import TemplateEditor from '../views/FormulaTemplate/TemplateEditor.vue'
import { canEnterExistingDesignWorkbench } from './workbenchAccess.mjs'

const routes = [
  { 
    path: '/',
    redirect: '/workbench/product-select'
  },
  {
    path: '/dashboard',
    component: Dashboard, 
    name: 'Dashboard' 
  },
  {
    path: '/report',
    name: 'ReportView',
    component: ReportView,
    meta: { hideLayout: true }
  },
  {
    path: '/product-management',
    redirect: '/drums'
  },
  {
    path: '/lab',
    name: 'LabSystem',
    children: [
      { path: '', name: 'TrialList', component: TrialList },
      { path: 'trial/:id', name: 'TrialDetail', component: TrialDetail },
      { path: 'templates', name: 'TemplateManage', component: TemplateManage },
      { path: 'materials', name: 'MaterialManage', component: MaterialManage }
    ]
  },
  {
    path: '/catalog',
    name: 'Catalog',
    component: () => import('../views/CatalogExplorer.vue'),
    meta: { title: '设备选型目录', icon: 'List' }
  },
  { 
    path: '/product-types', 
    component: ProductTypes, 
    name: 'ProductTypes' 
  },
  { 
    path: '/types/:typeId/components', 
    component: ProductComponents, 
    name: 'ProductComponents', 
    props: true 
  },
  { 
    path: '/types/:typeId/families', 
    component: FamilyList, 
    name: 'Families', 
    props: true 
  },
  { 
    path: '/families/:familyId/versions', 
    component: VersionManage, 
    name: 'Versions', 
    props: true 
  },
  {
    path: '/families/:familyId/matrix',
    component: ModelParameterMatrix,
    name: 'ModelParameterMatrix',
    meta: { primaryFlow: true },
    props: true
  },
  { 
    path: '/parameters',
    component: ParameterCenter,
    name: 'ParameterCenter'
  },
  {
    path: '/drums',
    component: DrumCatalog,
    name: 'DrumCatalog',
    meta: { primaryFlow: true }
  },
  { 
    path: '/templates',
    component: TemplateCenter,
    name: 'TemplateCenter',
    meta: { legacy: true }
  },
  {
    path: '/formula-templates',
    component: FormulaTemplateCenter,
    name: 'FormulaTemplateCenter',
    meta: { primaryFlow: true }
  },
  {
    path: '/formula-templates/:id/edit',
    component: TemplateEditor,
    name: 'TemplateEditor',
    props: true
  },
  { 
    path: '/workbench/product-select',
    component: ProductTypeSelection,
    name: 'ProductTypeSelection',
    meta: { primaryFlow: true }
  },
  { 
    path: '/workbench/modules/:typeId',
    component: ModuleSelection,
    name: 'ModuleSelection',
    meta: { primaryFlow: true }
  },
  { 
    path: '/workbench/workspace',
    component: OptimizedWorkbench,
    name: 'NewDesignWorkbench',
    meta: { primaryFlow: true }
  },
  { 
    path: '/workbench/legacy',
    component: LegacyWorkbench,
    name: 'DesignWorkbench',
    meta: { legacy: true }
  },
  {
    path: '/guidance',
    component: DesignGuidance,
    name: 'DesignGuidance',
    meta: { legacy: true }
  },
  {
    path: '/design', 
    redirect: '/workbench/product-select'
  },
  { 
    path: '/formulas', 
    component: FormulaLibrary, 
    name: 'Formulas' 
  },
  { 
    path: '/compare', 
    component: DesignPointCompare, 
    name: 'Compare',
    meta: { legacy: true }
  },
  { 
    path: '/knowledge', 
    component: KnowledgeBase, 
    name: 'KnowledgeBase',
    meta: { legacy: true }
  },
  {
    path: '/search',
    component: SearchResult,
    name: 'Search'
  },
  {
    path: '/monitor',
    component: MonitorView,
    name: 'Monitor'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  if (to.name !== 'NewDesignWorkbench') return true

  const allowed = canEnterExistingDesignWorkbench({
    typeId: to.query.typeId,
    moduleCode: to.query.moduleCode
  })
  if (allowed) return true

  return {
    name: 'ModuleSelection',
    params: { typeId: String(to.query.typeId || '') },
    query: {
      familyId: to.query.familyId || undefined,
      versionId: to.query.versionId || undefined
    }
  }
})

export default router
