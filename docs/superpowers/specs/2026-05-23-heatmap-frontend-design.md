# 热力图功能前端设计文档

> 创建日期：2026-05-23
> 状态：待审核

---

## 一、页面结构

### 1.1 Dashboard 入口卡片

**位置**：Dashboard.vue 快捷操作区域下方

**内容**：
- 卡片标题："热门推荐"
- 显示 Top 3 热门查询词
- 点击卡片或链接进入热力图详情页面

### 1.2 热力图独立页面

**路由**：`/heatmap`

**布局**：
```
┌─────────────────────────────────────────────────────────┐
│  [页面标题]                          [时间范围 ▼]       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────┐  ┌─────────────────────┐      │
│  │   热门查询词        │  │   热门文档          │      │
│  │   [列表 + 柱状图]   │  │   [列表 + 柱状图]   │      │
│  └─────────────────────┘  └─────────────────────┘      │
│                                                         │
│  ┌──────────────────────────────────────────────┐      │
│  │   时间热力图                    [柱状|矩阵|折线]│      │
│  │   [图表区域]                                   │      │
│  └──────────────────────────────────────────────┘      │
│                                                         │
│  ┌──────────────────────────────────────────────┐      │
│  │   知识导航热度                                 │      │
│  │   [带热度标签的树形列表]                      │      │
│  └──────────────────────────────────────────────┘      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 二、组件设计

### 2.1 热门查询词卡片

**展示内容**：
- 排名号（#1, #2, #3...）
- 查询词文本
- 检索次数
- 悬停显示：趋势详情（较昨日变化）

**交互**：
- 点击查询词 → 跳转搜索结果页
- 悬停 → 显示趋势弹窗

### 2.2 热门文档卡片

**展示内容**：
- 排名号
- 文档标题
- 文档类型图标（wiki/对话/外链）
- 命中次数
- 悬停显示：平均得分、点击跳转

**交互**：
- 点击文档 → 跳转文档详情页

### 2.3 时间热力图卡片

**展示内容**：
- 柱状图（默认）
- 热力矩阵
- 折线图
- 峰值标注

**交互**：
- 图表类型切换按钮组
- 悬停显示具体数值

### 2.4 知识导航热度卡片

**展示内容**：
- 导航树节点名称
- 热度标签（🔥 热 / 🔆 暖 / ❄️ 冷）
- 访问次数

**交互**：
- 点击节点 → 展开子节点或跳转

---

## 三、API 调用

### 3.1 API 文件

**新建**：`frontend/src/api/heatmap.js`

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

---

## 四、国际化

### 4.1 中文 (`zh-CN`)

```javascript
heatmap: {
  title: '检索热力图',
  hotQueries: '热门查询词',
  hotDocuments: '热门文档',
  timeline: '时间热力图',
  navigationHeat: '知识导航热度',
  timeRange: '时间范围',
  trend: '趋势',
  searchCount: '检索次数',
  hitCount: '命中次数',
  viewAll: '查看全部'
}
```

### 4.2 英文 (`en-US`)

```javascript
heatmap: {
  title: 'Search Heatmap',
  hotQueries: 'Hot Queries',
  hotDocuments: 'Hot Documents',
  timeline: 'Timeline',
  navigationHeat: 'Navigation Heat',
  timeRange: 'Time Range',
  trend: 'Trend',
  searchCount: 'Search Count',
  hitCount: 'Hit Count',
  viewAll: 'View All'
}
```

---

## 五、技术实现

### 5.1 文件结构

```
frontend/src/
├── api/
│   └── heatmap.js          # 新增
├── views/
│   ├── Heatmap.vue         # 新增
│   └── Dashboard.vue       # 修改
└── i18n/
    ├── zh-CN/
    │   └── heatmap.js      # 新增
    └── en-US/
        └── heatmap.js      # 新增
```

### 5.2 路由配置

```javascript
// router/index.js
{
  path: '/heatmap',
  component: () => import('../views/Heatmap.vue'),
  meta: { title: '检索热力图' }
}
```

### 5.3 组件依赖

- **Element Plus**：el-card, el-row, el-col, el-select, el-tag, el-tooltip
- **ECharts**：用于柱状图、热力矩阵、折线图（通过 vue-echarts 或直接引入）
- **现有组件复用**：stat-card 样式、card 样式

---

## 六、视觉规范

### 6.1 颜色

沿用现有 design-system.css：
- 主色：`--color-primary` (#7C3AED)
- 成功：`--color-success` (#10B981)
- 警告：`--color-warning` (#F59E0B)
- 错误：`--color-error` (#EF4444)

### 6.2 热度等级颜色

| 等级 | 颜色 | 阈值 |
|------|------|------|
| 热 (🔥) | #EF4444 | count > 100 |
| 暖 (🔆) | #F59E0B | 50 < count ≤ 100 |
| 冷 (❄️) | #3B82F6 | count ≤ 50 |

### 6.3 图表配色

```css
--chart-color-1: #7C3AED;  /* 主色 */
--chart-color-2: #A78BFA; /* 浅主色 */
--chart-color-3: #F97316; /* CTA色 */
--chart-color-4: #10B981;  /* 成功色 */
--chart-color-5: #3B82F6;  /* 信息色 */
```

---

## 七、待确认事项

- [ ] ECharts 引入方式（vue-echarts 或 直接引入）
- [ ] 文档详情页路由格式（如 `/wiki/:id`）
- [ ] 搜索结果页路由格式

---

## 八、验收标准

1. Dashboard 显示热门推荐入口卡片
2. 热力图页面 4 个模块正常展示
3. 时间范围筛选器正常工作
4. 时间热力图 3 种图表可切换
5. 悬停显示趋势详情
6. 点击查询词/文档可跳转
7. 中英文切换正常
8. 响应式布局正常（移动端适配）
