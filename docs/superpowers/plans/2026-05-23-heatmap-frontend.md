# 热力图功能前端实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有前端项目中实现热力图功能，包括 Dashboard 入口卡片和独立热力图页面。

**Architecture:** 采用仪表盘式布局，使用 Element Plus 组件 + ECharts 图表库，通过 API 调用后端热力图数据。

**Tech Stack:** Vue 3, Element Plus, ECharts, vue-i18n

---

## 文件结构

```
frontend/src/
├── api/
│   └── heatmap.js                    # 新增：热力图 API 调用
├── views/
│   ├── Heatmap.vue                   # 新增：热力图页面
│   └── Dashboard.vue                 # 修改：添加入口卡片
├── i18n/
│   ├── zh-CN/
│   │   └── heatmap.js               # 新增：中文翻译
│   └── en-US/
│       └── heatmap.js               # 新增：英文翻译
└── router/
    └── index.js                     # 修改：添加热力图路由
```

---

## 任务 1：添加 ECharts 依赖

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: 添加 echarts 依赖到 package.json**

```json
{
  "dependencies": {
    "echarts": "^5.5.0"
  }
}
```

- [ ] **Step 2: 安装依赖**

```bash
cd frontend && npm install
```

- [ ] **Step 3: 提交代码**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat(heatmap): add echarts dependency"
```

---

## 任务 2：创建热力图 API 文件

**Files:**
- Create: `frontend/src/api/heatmap.js`
- Test: `frontend/src/api/heatmap.js` (手动测试 API 调用)

- [ ] **Step 1: 创建 API 文件**

```javascript
import request from './request'

export const heatmapApi = {
  getHotQueries(timeRange = '24h', limit = 10) {
    return request.get('/api/heatmap/queries', { params: { time_range: timeRange, limit } })
  },

  getHotDocuments(timeRange = '24h', limit = 10) {
    return request.get('/api/heatmap/documents', { params: { time_range: timeRange, limit } })
  },

  getTimeline(date, granularity = 'hour') {
    return request.get('/api/heatmap/timeline', { params: { date, granularity } })
  },

  getNavigationHeat() {
    return request.get('/api/heatmap/navigation')
  }
}
```

- [ ] **Step 2: 提交代码**

```bash
git add frontend/src/api/heatmap.js
git commit -m "feat(heatmap): add heatmap API module"
```

---

## 任务 3：创建中文国际化文件

**Files:**
- Create: `frontend/src/i18n/zh-CN/heatmap.js`
- Modify: `frontend/src/i18n/zh-CN/index.js`

- [ ] **Step 1: 创建中文翻译文件**

```javascript
export default {
  title: '检索热力图',
  hotQueries: '热门查询词',
  hotDocuments: '热门文档',
  timeline: '时间热力图',
  navigationHeat: '知识导航热度',
  timeRange: {
    label: '时间范围',
    '24h': '最近 24 小时',
    '7d': '最近 7 天',
    '30d': '最近 30 天'
  },
  trend: {
    title: '趋势详情',
    up: '较昨日上升',
    down: '较昨日下降',
    stable: '持平'
  },
  searchCount: '检索次数',
  hitCount: '命中次数',
  viewAll: '查看全部',
  chartTypes: {
    bar: '柱状图',
    matrix: '热力矩阵',
    line: '折线图'
  },
  heatLevels: {
    hot: '热',
    warm: '暖',
    cold: '冷'
  },
  dashboardCard: {
    title: '热门推荐',
    subtitle: '发现热门知识'
  }
}
```

- [ ] **Step 2: 修改 index.js 导入**

在 `frontend/src/i18n/zh-CN/index.js` 中添加：

```javascript
import heatmap from './heatmap'

export default {
  common,
  login,
  setup,
  dashboard,
  wiki,
  qa,
  knowledge,
  settings,
  trace,
  heatmap  // 添加这一行
}
```

- [ ] **Step 3: 提交代码**

```bash
git add frontend/src/i18n/zh-CN/heatmap.js frontend/src/i18n/zh-CN/index.js
git commit -m "feat(heatmap): add Chinese i18n translations"
```

---

## 任务 4：创建英文国际化文件

**Files:**
- Create: `frontend/src/i18n/en-US/heatmap.js`
- Modify: `frontend/src/i18n/en-US/index.js`

- [ ] **Step 1: 创建英文翻译文件**

```javascript
export default {
  title: 'Search Heatmap',
  hotQueries: 'Hot Queries',
  hotDocuments: 'Hot Documents',
  timeline: 'Timeline',
  navigationHeat: 'Navigation Heat',
  timeRange: {
    label: 'Time Range',
    '24h': 'Last 24 Hours',
    '7d': 'Last 7 Days',
    '30d': 'Last 30 Days'
  },
  trend: {
    title: 'Trend Details',
    up: 'Up from yesterday',
    down: 'Down from yesterday',
    stable: 'Stable'
  },
  searchCount: 'Search Count',
  hitCount: 'Hit Count',
  viewAll: 'View All',
  chartTypes: {
    bar: 'Bar Chart',
    matrix: 'Heat Map',
    line: 'Line Chart'
  },
  heatLevels: {
    hot: 'Hot',
    warm: 'Warm',
    cold: 'Cold'
  },
  dashboardCard: {
    title: 'Hot Recommendations',
    subtitle: 'Discover popular knowledge'
  }
}
```

- [ ] **Step 2: 修改 index.js 导入**

在 `frontend/src/i18n/en-US/index.js` 中添加：

```javascript
import heatmap from './heatmap'

export default {
  common,
  login,
  setup,
  dashboard,
  wiki,
  qa,
  knowledge,
  settings,
  trace,
  heatmap  // 添加这一行
}
```

- [ ] **Step 3: 提交代码**

```bash
git add frontend/src/i18n/en-US/heatmap.js frontend/src/i18n/en-US/index.js
git commit -m "feat(heatmap): add English i18n translations"
```

---

## 任务 5：添加热力图路由

**Files:**
- Modify: `frontend/src/router/index.js:30-45`

- [ ] **Step 1: 在 children 数组中添加 heatmap 路由**

在 `path: 'knowledge'` 之后添加：

```javascript
{
  path: 'heatmap',
  name: 'Heatmap',
  component: () => import('@/views/Heatmap.vue'),
},
```

完整代码段：

```javascript
{
  path: 'knowledge',
  name: 'Knowledge',
  component: () => import('@/views/Knowledge.vue'),
},
{
  path: 'heatmap',
  name: 'Heatmap',
  component: () => import('@/views/Heatmap.vue'),
},
```

- [ ] **Step 2: 提交代码**

```bash
git add frontend/src/router/index.js
git commit -m "feat(heatmap): add heatmap route"
```

---

## 任务 6：创建热力图页面组件

**Files:**
- Create: `frontend/src/views/Heatmap.vue`

- [ ] **Step 1: 创建完整的 Heatmap.vue 组件**

```vue
<template>
  <div class="heatmap-page fade-in">
    <div class="page-header">
      <h1>{{ t('heatmap.title') }}</h1>
      <div class="header-actions">
        <el-select v-model="timeRange" size="default" style="width: 160px">
          <el-option :value="'24h'" :label="t('heatmap.timeRange.24h')" />
          <el-option :value="'7d'" :label="t('heatmap.timeRange.7d')" />
          <el-option :value="'30d'" :label="t('heatmap.timeRange.30d')" />
        </el-select>
      </div>
    </div>

    <!-- 热门查询词 & 热门文档 -->
    <el-row :gutter="20" class="card-row">
      <el-col :xs="24" :md="12">
        <div class="card">
          <h3>{{ t('heatmap.hotQueries') }}</h3>
          <div class="list-container">
            <div
              v-for="(item, index) in hotQueries"
              :key="index"
              class="list-item"
              @click="handleQueryClick(item.query)"
            >
              <span class="rank">#{{ index + 1 }}</span>
              <span class="content">{{ item.query }}</span>
              <span class="count">{{ item.count }}</span>
              <el-tooltip :content="`${t('heatmap.searchCount')}: ${item.count}`" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card">
          <h3>{{ t('heatmap.hotDocuments') }}</h3>
          <div class="list-container">
            <div
              v-for="(item, index) in hotDocuments"
              :key="index"
              class="list-item"
              @click="handleDocClick(item.doc_id)"
            >
              <span class="rank">#{{ index + 1 }}</span>
              <span class="content">{{ item.doc_title }}</span>
              <el-tag size="small" type="info">{{ item.doc_type }}</el-tag>
              <span class="count">{{ item.hit_count }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 时间热力图 -->
    <el-row :gutter="20" class="card-row">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">
            <h3>{{ t('heatmap.timeline') }}</h3>
            <el-radio-group v-model="chartType" size="small">
              <el-radio-button value="bar">{{ t('heatmap.chartTypes.bar') }}</el-radio-button>
              <el-radio-button value="matrix">{{ t('heatmap.chartTypes.matrix') }}</el-radio-button>
              <el-radio-button value="line">{{ t('heatmap.chartTypes.line') }}</el-radio-button>
            </el-radio-group>
          </div>
          <div ref="timelineChartRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 知识导航热度 -->
    <el-row :gutter="20" class="card-row">
      <el-col :span="24">
        <div class="card">
          <h3>{{ t('heatmap.navigationHeat') }}</h3>
          <div class="nav-heat-list">
            <div
              v-for="item in navigationHeat"
              :key="item.node_id"
              class="nav-heat-item"
              @click="handleNavClick(item.node_id)"
            >
              <span class="node-name">{{ item.node_name }}</span>
              <el-tag
                :type="getHeatTagType(item.hot_level)"
                size="small"
              >
                {{ t(`heatmap.heatLevels.${item.hot_level}`) }}
              </el-tag>
              <span class="hit-count">{{ item.hit_count }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { heatmapApi } from '@/api/heatmap'

const { t } = useI18n()
const router = useRouter()

const timeRange = ref('24h')
const chartType = ref('bar')
const hotQueries = ref([])
const hotDocuments = ref([])
const timelineData = ref([])
const navigationHeat = ref([])
const timelineChartRef = ref(null)
let timelineChart = null

const fetchData = async () => {
  try {
    const [queriesRes, docsRes, timelineRes, navRes] = await Promise.all([
      heatmapApi.getHotQueries(timeRange.value),
      heatmapApi.getHotDocuments(timeRange.value),
      heatmapApi.getTimeline(null, 'hour'),
      heatmapApi.getNavigationHeat()
    ])

    hotQueries.value = queriesRes.data?.data || []
    hotDocuments.value = docsRes.data?.data || []
    timelineData.value = timelineRes.data?.data || []
    navigationHeat.value = navRes.data?.data || []

    updateTimelineChart()
  } catch (error) {
    console.error('Failed to fetch heatmap data:', error)
  }
}

const updateTimelineChart = () => {
  if (!timelineChartRef.value) return

  if (!timelineChart) {
    timelineChart = echarts.init(timelineChartRef.value)
  }

  let option
  if (chartType.value === 'bar') {
    option = {
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: timelineData.value.map(d => `${d.hour}:00`)
      },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar',
        data: timelineData.value.map(d => d.count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#7C3AED' },
            { offset: 1, color: '#A78BFA' }
          ])
        }
      }]
    }
  } else if (chartType.value === 'line') {
    option = {
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: timelineData.value.map(d => `${d.hour}:00`)
      },
      yAxis: { type: 'value' },
      series: [{
        type: 'line',
        data: timelineData.value.map(d => d.count),
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(124, 58, 237, 0.3)' },
            { offset: 1, color: 'rgba(124, 58, 237, 0.05)' }
          ])
        },
        lineStyle: { color: '#7C3AED' },
        itemStyle: { color: '#7C3AED' }
      }]
    }
  } else {
    // matrix
    const matrixData = timelineData.value.map(d => [d.hour, 0, d.count])
    option = {
      tooltip: {
        formatter: (p) => `${p.data[0]}:00 - ${p.data[2]} 次检索`
      },
      xAxis: { type: 'category', data: timelineData.value.map(d => `${d.hour}`) },
      yAxis: { show: false },
      visualMap: {
        min: 0,
        max: Math.max(...timelineData.value.map(d => d.count), 1),
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        inRange: { color: ['#E9D5FF', '#7C3AED', '#5B21B6'] }
      },
      series: [{
        type: 'heatmap',
        data: matrixData,
        label: { show: true },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
      }]
    }
  }

  timelineChart.setOption(option)
}

const getHeatTagType = (level) => {
  const types = { hot: 'danger', warm: 'warning', cold: 'info' }
  return types[level] || 'info'
}

const handleQueryClick = (query) => {
  router.push({ path: '/qa', query: { q: query } })
}

const handleDocClick = (docId) => {
  router.push({ path: '/wiki', query: { id: docId } })
}

const handleNavClick = (nodeId) => {
  router.push({ path: '/knowledge', query: { node: nodeId } })
}

watch(timeRange, fetchData)
watch(chartType, updateTimelineChart)

onMounted(() => {
  fetchData()
  window.addEventListener('resize', () => timelineChart?.resize())
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: var(--font-size-2xl);
  margin-bottom: 0;
}

.card-row {
  margin-bottom: 20px;
}

.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 20px;
}

.card h3 {
  font-size: var(--font-size-lg);
  margin-bottom: 16px;
  color: var(--color-text);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  margin-bottom: 0;
}

.list-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  cursor: pointer;
  transition: all var(--transition-base);
}

.list-item:hover {
  background: var(--color-primary-50);
  transform: translateX(4px);
}

.rank {
  font-weight: 700;
  color: var(--color-primary);
  min-width: 28px;
}

.content {
  flex: 1;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.count {
  font-weight: 600;
  color: var(--color-text-secondary);
}

.info-icon {
  color: var(--color-text-muted);
  cursor: help;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.nav-heat-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-heat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  cursor: pointer;
  transition: all var(--transition-base);
}

.nav-heat-item:hover {
  background: var(--color-primary-50);
}

.node-name {
  flex: 1;
  color: var(--color-text);
}

.hit-count {
  font-weight: 600;
  color: var(--color-text-secondary);
}
</style>
```

- [ ] **Step 2: 提交代码**

```bash
git add frontend/src/views/Heatmap.vue
git commit -m "feat(heatmap): create Heatmap.vue page component"
```

---

## 任务 7：更新 Dashboard 添加入口卡片

**Files:**
- Modify: `frontend/src/views/Dashboard.vue:56-104`

- [ ] **Step 1: 在快捷操作区域后添加热门推荐卡片**

在 `</el-row>` (第 54 行) 后添加：

```vue
    <!-- 热门推荐入口 -->
    <el-row :gutter="20" class="card-row">
      <el-col :span="24">
        <div class="card hot-recommend-card" @click="router.push('/heatmap')">
          <div class="hot-recommend-content">
            <div class="hot-icon">
              <el-icon :size="32" color="#F97316"><TrendCharts /></el-icon>
            </div>
            <div class="hot-info">
              <h3>{{ t('heatmap.dashboardCard.title') }}</h3>
              <p>{{ t('heatmap.dashboardCard.subtitle') }}</p>
            </div>
          </div>
          <div class="hot-queries-preview">
            <el-tag
              v-for="(query, index) in topQueries"
              :key="index"
              size="small"
              effect="plain"
              class="query-tag"
            >
              {{ query }}
            </el-tag>
          </div>
          <el-icon class="arrow-icon"><ArrowRight /></el-icon>
        </div>
      </el-col>
    </el-row>
```

- [ ] **Step 2: 修改 script 部分**

在 import 语句中添加：

```javascript
import { TrendCharts, ArrowRight } from '@element-plus/icons-vue'
import { heatmapApi } from '@/api/heatmap'
```

在 `stats` ref 后添加：

```javascript
const topQueries = ref([])
```

在 `onMounted` 中添加数据获取：

```javascript
onMounted(async () => {
  // 获取统计数据
  // ...

  // 获取热门查询词
  try {
    const res = await heatmapApi.getHotQueries('24h', 3)
    topQueries.value = res.data?.data?.slice(0, 3).map(q => q.query) || []
  } catch (error) {
    console.error('Failed to fetch hot queries:', error)
  }
})
```

- [ ] **Step 3: 添加卡片样式**

在 `<style scoped>` 中添加：

```css
.card-row {
  margin-bottom: 20px;
}

.hot-recommend-card {
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: all var(--transition-base);
}

.hot-recommend-card:hover {
  border-color: var(--color-cta);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.hot-recommend-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hot-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hot-info h3 {
  font-size: var(--font-size-lg);
  margin-bottom: 2px;
  color: var(--color-text);
}

.hot-info p {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
}

.hot-queries-preview {
  display: flex;
  gap: 8px;
  flex: 1;
  justify-content: center;
}

.query-tag {
  cursor: pointer;
}

.arrow-icon {
  color: var(--color-text-muted);
  font-size: 20px;
  transition: transform var(--transition-base);
}

.hot-recommend-card:hover .arrow-icon {
  transform: translateX(4px);
  color: var(--color-cta);
}
```

- [ ] **Step 4: 提交代码**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "feat(heatmap): add heatmap entry card to Dashboard"
```

---

## 验收清单

- [ ] package.json 已添加 echarts 依赖
- [ ] npm install 成功执行
- [ ] heatmap.js API 文件已创建
- [ ] 中文翻译文件已创建并导入
- [ ] 英文翻译文件已创建并导入
- [ ] 路由已添加 `/heatmap`
- [ ] Heatmap.vue 页面组件已创建
- [ ] Dashboard.vue 已添加热门推荐卡片
- [ ] 页面可正常访问
- [ ] 数据正常加载显示
- [ ] 图表切换功能正常
- [ ] 中英文切换正常
