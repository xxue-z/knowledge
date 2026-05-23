-- 链路追踪表

-- Trace Session - 一次完整的请求链路
CREATE TABLE IF NOT EXISTS trace_sessions (
    id VARCHAR(64) PRIMARY KEY,
    trace_id VARCHAR(32) NOT NULL UNIQUE,
    request_id VARCHAR(32) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    username VARCHAR(128),
    endpoint VARCHAR(256),
    method VARCHAR(16),
    question TEXT,
    intent VARCHAR(32),
    status VARCHAR(16) DEFAULT 'running',
    total_spans INTEGER DEFAULT 0,
    total_events INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms FLOAT,
    result_summary TEXT,
    output_preview TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trace_user_time ON trace_sessions(user_id, start_time);
CREATE INDEX IF NOT EXISTS idx_trace_status_time ON trace_sessions(status, start_time);

-- Trace Span - 一次 MCP 消息传递
CREATE TABLE IF NOT EXISTS trace_spans (
    id VARCHAR(64) PRIMARY KEY,
    trace_id VARCHAR(32) NOT NULL,
    span_id VARCHAR(32) NOT NULL,
    parent_span_id VARCHAR(32),
    session_id VARCHAR(64) NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    agent_name VARCHAR(128),
    action VARCHAR(64),
    input_summary JSON,
    output_summary JSON,
    status VARCHAR(16) DEFAULT 'running',
    error_message TEXT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms FLOAT,
    confidence FLOAT,
    sources_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_span_session FOREIGN KEY (session_id) REFERENCES trace_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_span_parent FOREIGN KEY (parent_span_id) REFERENCES trace_spans(span_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_span_trace_id ON trace_spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_span_session_agent ON trace_spans(session_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_span_duration ON trace_spans(duration_ms);

-- Trace Event - Span 内的关键事件
CREATE TABLE IF NOT EXISTS trace_events (
    id VARCHAR(64) PRIMARY KEY,
    trace_id VARCHAR(32) NOT NULL,
    span_id VARCHAR(32) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    event_name VARCHAR(128),
    data JSON,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_event_span FOREIGN KEY (span_id) REFERENCES trace_spans(span_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_event_trace_id ON trace_events(trace_id);
CREATE INDEX IF NOT EXISTS idx_event_span_time ON trace_events(span_id, timestamp);

-- Trace Stats - 统计聚合表
CREATE TABLE IF NOT EXISTS trace_stats (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    stat_date TIMESTAMP NOT NULL,
    total_requests INTEGER DEFAULT 0,
    success_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    total_duration_ms FLOAT DEFAULT 0,
    avg_duration_ms FLOAT DEFAULT 0,
    p95_duration_ms FLOAT DEFAULT 0,
    agent_usage JSON,
    intent_distribution JSON,
    error_types JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stats_user_date ON trace_stats(user_id, stat_date);
