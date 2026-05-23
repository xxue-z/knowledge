# 需求文档：Wiki 文档系统

## 1. 需求概述

Wiki 系统用于管理企业制度文件，支持结构化组织、版本控制和细粒度权限控制。

---

## 2. 功能需求

### 2.1 Wiki 基础功能

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| WIKI-001 | 支持 Wiki 文档的创建、读取、更新、删除 | README.md 第1节 |
| WIKI-002 | 文档标题最大长度 500 字符 | 设计约束 |
| WIKI-003 | 支持 Markdown 格式内容 | 技术选型 |
| WIKI-004 | 文档唯一标识（slug） | URL友好设计 |

### 2.2 版本控制

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| WIKI-005 | 每次编辑自动创建版本记录 | README.md 第3节 |
| WIKI-006 | 支持查看历史版本列表 | 版本管理需求 |
| WIKI-007 | 支持版本对比功能 | 版本管理需求 |
| WIKI-008 | 支持版本回滚 | 版本管理需求 |

### 2.3 权限与安全

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| WIKI-009 | 文档敏感度分级：public/internal/confidential/secret | README.md 第4节 |
| WIKI-010 | 访问控制列表（ACL）支持按部门/角色/密级设置 | README.md 第4节 |
| WIKI-011 | 文档创建者自动获得管理权限 | 权限设计 |
| WIKI-012 | 支持部门级文档隔离 | README.md 第4节 |

### 2.4 检索功能

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| WIKI-013 | 支持全文检索 | README.md 第3节 |
| WIKI-014 | 支持按关键词搜索 | 检索需求 |
| WIKI-015 | 支持按敏感度过滤搜索结果 | 权限约束 |
| WIKI-016 | 支持按部门过滤搜索结果 | 权限约束 |

### 2.5 Wiki Agent

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| WIKI-017 | Wiki Agent 封装文档 CRUD 操作 | README.md 第3节 |
| WIKI-018 | Wiki Agent 查询时携带用户身份 | README.md 第4节 |
| WIKI-019 | Wiki Agent 根据权限标签过滤页面可见性 | README.md 第3节 |

---

## 3. 数据模型需求

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | 主键 | 文档唯一标识 |
| title | String | max=500 | 文档标题 |
| content | Text | - | Markdown 内容 |
| slug | String | max=500, 唯一 | URL路径标识 |
| parent_id | UUID | 外键 | 父文档ID（支持层级） |
| sensitivity | String | enum | public/internal/confidential/secret |
| dept_id | String | 可选 | 所属部门 |
| created_by | String | - | 创建者ID |
| updated_by | String | 可选 | 最后更新者ID |
| created_at | DateTime | - | 创建时间 |
| updated_at | DateTime | - | 更新时间 |

---

## 4. 非功能需求

| 需求编号 | 需求描述 |
|----------|----------|
| WIKI-NFR-001 | 文档检索响应时间 < 500ms |
| WIKI-NFR-002 | 支持 10000+ 文档存储 |
| WIKI-NFR-003 | 版本记录保留最近 100 个版本 |
