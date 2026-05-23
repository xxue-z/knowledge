-- Wiki 文档对象存储系统数据库初始化脚本
-- 日期: 2026-05-23

-- =============================================
-- 第一部分: 删除旧表（如果存在）
-- =============================================

DROP TABLE IF EXISTS wiki_page_versions CASCADE;
DROP TABLE IF EXISTS wiki_page_tags CASCADE;
DROP TABLE IF EXISTS wiki_chunks CASCADE;
DROP TABLE IF EXISTS wiki_files CASCADE;
DROP TABLE IF EXISTS wiki_tags CASCADE;
DROP TABLE IF EXISTS wiki_pages CASCADE;
DROP TABLE IF EXISTS chunking_rules CASCADE;

-- =============================================
-- 第二部分: 创建新表
-- =============================================

-- wiki_pages 表：存储 Wiki 页面元数据
CREATE TABLE wiki_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    parent_id UUID REFERENCES wiki_pages(id),
    sensitivity VARCHAR(20) DEFAULT 'public',
    dept_id VARCHAR(50),
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processing_status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    processing_error TEXT
);

CREATE INDEX idx_wiki_pages_parent ON wiki_pages(parent_id);
CREATE INDEX idx_wiki_pages_slug ON wiki_pages(slug);
CREATE INDEX idx_wiki_pages_sensitivity ON wiki_pages(sensitivity);
CREATE INDEX idx_wiki_pages_status ON wiki_pages(processing_status);

-- wiki_files 表：存储文件元数据
CREATE TABLE wiki_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES wiki_pages(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(200) NOT NULL,
    file_size INTEGER NOT NULL,
    md5_hash VARCHAR(32) NOT NULL,
    mime_type VARCHAR(100) DEFAULT 'text/markdown',
    is_current BOOLEAN DEFAULT true,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    edit_summary VARCHAR(500)
);

CREATE INDEX idx_wiki_files_page ON wiki_files(page_id);
CREATE INDEX idx_wiki_files_current ON wiki_files(page_id, is_current) WHERE is_current = true;
CREATE UNIQUE INDEX idx_wiki_files_version ON wiki_files(page_id, version);

-- wiki_chunks 表：存储文档切片元数据
CREATE TABLE wiki_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES wiki_files(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    start_pos INTEGER NOT NULL,
    end_pos INTEGER NOT NULL,
    text_preview VARCHAR(200),
    vector_id VARCHAR(100) NOT NULL
);

CREATE INDEX idx_wiki_chunks_file ON wiki_chunks(file_id);
CREATE INDEX idx_wiki_chunks_vector ON wiki_chunks(vector_id);

-- wiki_tags 表：存储标签
CREATE TABLE wiki_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(20) DEFAULT '#3B82F6',
    description TEXT,
    parent_id UUID REFERENCES wiki_tags(id),
    sort_order INTEGER DEFAULT 0,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_wiki_tags_parent ON wiki_tags(parent_id);
CREATE INDEX idx_wiki_tags_sort ON wiki_tags(sort_order);

-- wiki_page_tags 关联表
CREATE TABLE wiki_page_tags (
    page_id UUID NOT NULL REFERENCES wiki_pages(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES wiki_tags(id) ON DELETE CASCADE,
    PRIMARY KEY (page_id, tag_id)
);

CREATE INDEX idx_wiki_page_tags_page ON wiki_page_tags(page_id);
CREATE INDEX idx_wiki_page_tags_tag ON wiki_page_tags(tag_id);

-- chunking_rules 表：存储切片规则
CREATE TABLE chunking_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    rule_type VARCHAR(20) NOT NULL, -- heading, paragraph, length, custom
    rule_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunking_rules_active ON chunking_rules(is_active) WHERE is_active = true;
CREATE INDEX idx_chunking_rules_sort ON chunking_rules(sort_order);

-- =============================================
-- 第三部分: 初始化数据
-- =============================================

-- 初始化切片规则
INSERT INTO chunking_rules (name, description, rule_type, rule_config, sort_order) VALUES
('按标题切片', '按 Markdown 标题（#、##、### 等）进行切片', 'heading', '{"levels": [1, 2, 3]}'::jsonb, 1),
('按段落切片', '按空行分隔的段落进行切片', 'paragraph', '{"min_length": 50}'::jsonb, 2),
('按长度切片', '按固定长度进行切片', 'length', '{"max_tokens": 500, "overlap": 50}'::jsonb, 3);

-- =============================================
-- 初始化完成
-- =============================================

SELECT 'Wiki 文档对象存储系统数据库初始化完成！' AS message;
