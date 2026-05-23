<template>
  <div class="trace-view">
    <div class="trace-header">
      <h2>Agent 链路追踪</h2>
      <div class="trace-filters">
        <el-select v-model="filterIntent" placeholder="意图类型" clearable @change="loadTraces">
          <el-option label="全部" value="" />
          <el-option label="PURE_DB" value="PURE_DB" />
          <el-option label="PURE_KB" value="PURE_KB" />
          <el-option label="HYBRID" value="HYBRID" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="状态" clearable @change="loadTraces">
          <el-option label="全部" value="" />
          <el-option label="成功" value="completed" />
          <el-option label="失败" value="error" />
          <el-option label="进行中" value="running" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="loadTraces"
        />
        <el-button type="primary" @click="loadTraces">刷新</el-button>
      </div>
    </div>

    <div class="trace-content">
      <div class="trace-list-panel">
        <div class="trace-list-header">
          <span>共 {{ total }} 条记录</span>
        </div>
        <div class="trace-list">
          <div
            v-for="trace in traces"
            :key="trace.trace_id"
            class="trace-item"
            :class="{ active: selectedTraceId === trace.trace_id, owner: trace.is_owner }"
            @click="selectTrace(trace)"
          >
            <div class="trace-item-header">
              <span class="trace-id">{{ trace.trace_id }}</span>
              <span class="trace-status" :class="trace.status">{{ trace.status }}</span>
            </div>
            <div class="trace-item-info">
              <span class="trace-user">{{ trace.username || trace.user_id }}</span>
              <span class="trace-intent">{{ trace.intent }}</span>
            </div>
            <div class="trace-item-meta">
              <span class="trace-time">{{ formatTime(trace.start_time) }}</span>
              <span class="trace-duration">{{ trace.duration_ms ? (trace.duration_ms / 1000).toFixed(2) + 's' : '-' }}</span>
            </div>
            <div class="trace-item-stats">
              <span class="stat success">✓ {{ trace.success_count }}</span>
              <span class="stat error">✗ {{ trace.error_count }}</span>
              <span class="stat spans">{{ trace.total_spans }} spans</span>
            </div>
            <div v-if="trace.view_level === 'summary'" class="trace-item-badge">
              概要
            </div>
          </div>
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadTraces"
        />
      </div>

      <div class="trace-detail-panel">
        <div v-if="!selectedTrace" class="trace-detail-empty">
          <p>选择一条 Trace 查看详情</p>
        </div>
        <div v-else-if="traceDetail.error" class="trace-detail-error">
          <p>{{ traceDetail.error }}</p>
        </div>
        <div v-else class="trace-detail">
          <div class="trace-detail-header">
            <h3>Trace: {{ selectedTrace.trace_id }}</h3>
            <div class="trace-detail-meta">
              <span>用户: {{ traceDetail.username }}</span>
              <span>意图: {{ traceDetail.intent }}</span>
              <span>状态: {{ traceDetail.status }}</span>
              <span>耗时: {{ traceDetail.duration_ms ? (traceDetail.duration_ms / 1000).toFixed(2) + 's' : '-' }}</span>
              <span v-if="traceDetail.view_level === 'summary'" class="view-level-badge">下属概要</span>
              <span v-else class="view-level-badge owner">完整详情</span>
            </div>
            <div v-if="traceDetail.question" class="trace-detail-question">
              <strong>问题:</strong> {{ traceDetail.question }}
            </div>
            <div v-if="traceDetail.result_summary" class="trace-detail-summary">
              <strong>结果摘要:</strong> {{ traceDetail.result_summary }}
            </div>
            <div v-if="traceDetail.view_level === 'summary'" class="trace-summary-notice">
              <p>⚠️ 您正在查看下属员工的链路概要。如需查看完整详情，请联系管理员。</p>
            </div>
          </div>

          <div class="trace-timeline">
            <h4>链路视图 (Jaeger 风格)</h4>
            <div class="timeline-container">
              <div class="timeline-header">
                <div class="timeline-time-axis">
                  <span v-for="i in 11" :key="i" class="time-mark">
                    {{ ((i - 1) * 10) + '%' }}
                  </span>
                </div>
              </div>
              <div class="timeline-spans">
                <div
                  v-for="(span, index) in traceDetail.spans"
                  :key="span.span_id"
                  class="timeline-span"
                  :class="{ error: span.status === 'error', selected: selectedSpanId === span.span_id }"
                  :style="getSpanStyle(span)"
                  @click="selectSpan(span)"
                >
                  <div class="span-info">
                    <span class="span-name">{{ span.agent_name || span.agent_id }}</span>
                    <span class="span-action">{{ span.action }}</span>
                  </div>
                  <div class="span-duration">
                    {{ span.duration_ms ? (span.duration_ms / 1000).toFixed(2) + 's' : '-' }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="selectedSpan" class="span-detail">
            <h4>Span 详情: {{ selectedSpan.agent_name || selectedSpan.agent_id }}</h4>
            <div class="span-detail-content">
              <div class="span-detail-section">
                <h5>基本信息</h5>
                <table class="detail-table">
                  <tr>
                    <td>Span ID</td>
                    <td>{{ selectedSpan.span_id }}</td>
                  </tr>
                  <tr>
                    <td>Agent</td>
                    <td>{{ selectedSpan.agent_name }} ({{ selectedSpan.agent_id }})</td>
                  </tr>
                  <tr>
                    <td>Action</td>
                    <td>{{ selectedSpan.action }}</td>
                  </tr>
                  <tr>
                    <td>状态</td>
                    <td :class="selectedSpan.status">{{ selectedSpan.status }}</td>
                  </tr>
                  <tr>
                    <td>耗时</td>
                    <td>{{ selectedSpan.duration_ms ? (selectedSpan.duration_ms / 1000).toFixed(2) + 's' : '-' }}</td>
                  </tr>
                  <tr>
                    <td>置信度</td>
                    <td>{{ selectedSpan.confidence ? (selectedSpan.confidence * 100).toFixed(1) + '%' : '-' }}</td>
                  </tr>
                </table>
              </div>

              <div v-if="selectedSpan.input_summary" class="span-detail-section">
                <h5>输入</h5>
                <pre class="json-preview">{{ JSON.stringify(selectedSpan.input_summary, null, 2) }}</pre>
              </div>

              <div v-if="selectedSpan.output_summary" class="span-detail-section">
                <h5>输出</h5>
                <pre class="json-preview">{{ JSON.stringify(selectedSpan.output_summary, null, 2) }}</pre>
              </div>

              <div v-if="selectedSpan.error_message" class="span-detail-section">
                <h5>错误信息</h5>
                <pre class="error-preview">{{ selectedSpan.error_message }}</pre>
              </div>

              <div v-if="selectedSpan.events && selectedSpan.events.length" class="span-detail-section">
                <h5>事件 ({{ selectedSpan.events.length }})</h5>
                <div class="span-events">
                  <div v-for="event in selectedSpan.events" :key="event.event_id" class="span-event">
                    <span class="event-time">{{ formatTime(event.timestamp) }}</span>
                    <span class="event-name">{{ event.event_name || event.event_type }}</span>
                    <span v-if="event.message" class="event-message">{{ event.message }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { traceApi } from '@/api/trace'
import { ElMessage } from 'element-plus'

const traces = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const selectedTraceId = ref(null)
const selectedSpanId = ref(null)
const selectedTrace = ref(null)
const traceDetail = ref({})
const selectedSpan = ref(null)

const filterIntent = ref('')
const filterStatus = ref('')
const dateRange = ref([])

const loadTraces = async () => {
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterIntent.value) params.intent = filterIntent.value
    if (filterStatus.value) params.status = filterStatus.value
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0].toISOString()
      params.end_date = dateRange.value[1].toISOString()
    }

    const res = await traceApi.listTraces(params)
    traces.value = res.traces || []
    total.value = res.total || 0
  } catch (error) {
    ElMessage.error('加载 Trace 列表失败')
  }
}

const selectTrace = async (trace) => {
  selectedTraceId.value = trace.trace_id
  selectedTrace.value = trace
  selectedSpan.value = null
  selectedSpanId.value = null

  try {
    const res = await traceApi.getTraceDetail(trace.trace_id)
    traceDetail.value = res
  } catch (error) {
    ElMessage.error('加载 Trace 详情失败')
  }
}

const selectSpan = (span) => {
  selectedSpanId.value = span.span_id
  selectedSpan.value = span
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const getSpanStyle = (span) => {
  if (!traceDetail.value.start_time || !span.start_time) return {}

  const traceStart = new Date(traceDetail.value.start_time).getTime()
  const spanStart = new Date(span.start_time).getTime()
  const traceDuration = traceDetail.value.duration_ms || 1

  const left = ((spanStart - traceStart) / traceDuration) * 100
  const width = (span.duration_ms / traceDuration) * 100

  return {
    left: `${Math.max(0, left)}%`,
    width: `${Math.min(100 - left, width)}%`
  }
}

onMounted(() => {
  loadTraces()
})
</script>

<style scoped>
.trace-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
}

.trace-header {
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.trace-header h2 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.trace-filters {
  display: flex;
  gap: 12px;
  align-items: center;
}

.trace-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.trace-list-panel {
  width: 400px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.trace-list-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  font-size: 13px;
  color: #909399;
}

.trace-list {
  flex: 1;
  overflow-y: auto;
}

.trace-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
}

.trace-item:hover {
  background: #f5f7fa;
}

.trace-item.active {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}

.trace-item.owner {
  border-left: 3px solid #67c23a;
}

.trace-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.trace-id {
  font-family: monospace;
  font-size: 12px;
  color: #409eff;
}

.trace-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
}

.trace-status.completed {
  background: #f0f9eb;
  color: #67c23a;
}

.trace-status.error {
  background: #fef0f0;
  color: #f56c6c;
}

.trace-status.running {
  background: #ecf5ff;
  color: #409eff;
}

.trace-item-info {
  display: flex;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 4px;
}

.trace-user {
  color: #303133;
}

.trace-intent {
  color: #909399;
  font-size: 12px;
}

.trace-item-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.trace-item-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.stat.success {
  color: #67c23a;
}

.stat.error {
  color: #f56c6c;
}

.trace-item-badge {
  position: absolute;
  top: 12px;
  right: 16px;
  font-size: 10px;
  padding: 2px 6px;
  background: #fdf6ec;
  color: #e6a23c;
  border-radius: 3px;
}

.trace-detail-panel {
  flex: 1;
  overflow-y: auto;
  background: white;
}

.trace-detail-empty,
.trace-detail-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.trace-detail {
  padding: 20px;
}

.trace-detail-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.trace-detail-header h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
}

.trace-detail-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.view-level-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 3px;
  background: #fdf6ec;
  color: #e6a23c;
}

.view-level-badge.owner {
  background: #f0f9eb;
  color: #67c23a;
}

.trace-summary-notice {
  background: #fdf6ec;
  border: 1px solid #f5dab1;
  border-radius: 4px;
  padding: 12px;
  margin-top: 12px;
}

.trace-summary-notice p {
  margin: 0;
  font-size: 13px;
  color: #e6a23c;
}

.trace-detail-question,
.trace-detail-summary {
  font-size: 13px;
  color: #606266;
  margin-top: 8px;
  line-height: 1.5;
}

.trace-timeline {
  margin-bottom: 20px;
}

.trace-timeline h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
}

.timeline-container {
  background: #fafafa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
}

.timeline-header {
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
  margin-bottom: 8px;
}

.timeline-time-axis {
  display: flex;
  justify-content: space-between;
}

.time-mark {
  font-size: 11px;
  color: #c0c4cc;
}

.timeline-spans {
  position: relative;
  min-height: 50px;
}

.timeline-span {
  position: absolute;
  height: 32px;
  background: linear-gradient(135deg, #409eff, #66b1ff);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 60px;
}

.timeline-span:hover {
  transform: scaleY(1.1);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4);
}

.timeline-span.error {
  background: linear-gradient(135deg, #f56c6c, #f78989);
}

.timeline-span.selected {
  box-shadow: 0 0 0 2px #409eff, 0 2px 8px rgba(64, 158, 255, 0.4);
}

.span-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.span-name {
  font-size: 12px;
  font-weight: 500;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.span-action {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.8);
}

.span-duration {
  font-size: 11px;
  color: white;
  white-space: nowrap;
}

.span-detail {
  background: #fafafa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 16px;
}

.span-detail h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
}

.span-detail-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.span-detail-section h5 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #606266;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
}

.detail-table td {
  padding: 6px 12px;
  border: 1px solid #ebeef5;
  font-size: 13px;
}

.detail-table td:first-child {
  width: 100px;
  background: #f5f7fa;
  color: #909399;
}

.json-preview {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
  margin: 0;
  max-height: 200px;
  overflow-y: auto;
}

.error-preview {
  background: #fef0f0;
  color: #f56c6c;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  margin: 0;
}

.span-events {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.span-event {
  display: flex;
  gap: 12px;
  font-size: 12px;
  padding: 6px 8px;
  background: white;
  border-radius: 4px;
}

.event-time {
  color: #909399;
  font-family: monospace;
}

.event-name {
  color: #409eff;
}

.event-message {
  color: #606266;
}
</style>
