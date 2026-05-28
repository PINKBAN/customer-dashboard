-- ============================================================
-- 客户联络看板 - Supabase 数据库初始化脚本
-- 在 Supabase SQL Editor 中执行此脚本
-- ============================================================

-- 1. 客户联络状态表（勾选、原因、今日交易）
CREATE TABLE IF NOT EXISTS customer_state (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    checked     BOOLEAN DEFAULT FALSE,
    reason      TEXT DEFAULT '',
    reason_date TEXT DEFAULT '',
    traded_today BOOLEAN DEFAULT NULL,
    updated_by  TEXT DEFAULT '',
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customer_state_name ON customer_state(name);
CREATE INDEX IF NOT EXISTS idx_customer_state_checked ON customer_state(checked);

ALTER TABLE customer_state ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_select" ON customer_state FOR SELECT USING (true);
CREATE POLICY "anon_insert" ON customer_state FOR INSERT WITH CHECK (true);
CREATE POLICY "anon_update" ON customer_state FOR UPDATE USING (true) WITH CHECK (true);
CREATE POLICY "anon_delete" ON customer_state FOR DELETE USING (true);

-- 2. 客户基础数据快照表（build_dashboard.py 上传，前端拉取）
CREATE TABLE IF NOT EXISTS data_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    data            JSONB NOT NULL,
    customer_count  INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT FALSE,
    source_file     TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_data_snapshots_active ON data_snapshots(is_active);
CREATE INDEX IF NOT EXISTS idx_data_snapshots_created ON data_snapshots(created_at DESC);

ALTER TABLE data_snapshots ENABLE ROW LEVEL SECURITY;

-- 所有人都能读取最新数据
CREATE POLICY "anon_select_snapshots" ON data_snapshots FOR SELECT USING (true);
-- build_dashboard.py 通过 publishable key 上传
CREATE POLICY "anon_insert_snapshots" ON data_snapshots FOR INSERT WITH CHECK (true);
-- 允许更新 is_active（用于切换版本）
CREATE POLICY "anon_update_snapshots" ON data_snapshots FOR UPDATE USING (true) WITH CHECK (true);

-- 3. 操作日志表（可选，用于追溯）
CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGSERIAL PRIMARY KEY,
    action      TEXT NOT NULL,
    customer    TEXT NOT NULL,
    detail      TEXT DEFAULT '',
    operator    TEXT DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_customer ON audit_log(customer);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);

ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_select_log" ON audit_log FOR SELECT USING (true);
CREATE POLICY "anon_insert_log" ON audit_log FOR INSERT WITH CHECK (true);

-- 4. 实时订阅
ALTER PUBLICATION supabase_realtime ADD TABLE customer_state;
