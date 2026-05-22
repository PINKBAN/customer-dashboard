-- ============================================================
-- 客户联络看板 - Supabase 数据库初始化脚本
-- 在 Supabase SQL Editor 中执行此脚本
-- ============================================================

-- 1. 创建客户联络状态表
CREATE TABLE IF NOT EXISTS customer_state (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,       -- 客户名称（与Excel一致）
    checked     BOOLEAN DEFAULT FALSE,       -- 是否已勾选
    reason      TEXT DEFAULT '',             -- 不拿货原因
    updated_by  TEXT DEFAULT '',             -- 修改人
    updated_at  TIMESTAMPTZ DEFAULT NOW()    -- 修改时间
);

-- 2. 索引
CREATE INDEX IF NOT EXISTS idx_customer_state_name ON customer_state(name);
CREATE INDEX IF NOT EXISTS idx_customer_state_checked ON customer_state(checked);

-- 3. 启用 RLS
ALTER TABLE customer_state ENABLE ROW LEVEL SECURITY;

-- 4. 允许所有人读取（匿名访问）
CREATE POLICY "anon_select" ON customer_state
    FOR SELECT
    USING (true);

-- 5. 允许所有人写入（upsert）- 内部工具场景，不涉及敏感数据
CREATE POLICY "anon_insert" ON customer_state
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "anon_update" ON customer_state
    FOR UPDATE
    USING (true)
    WITH CHECK (true);

CREATE POLICY "anon_delete" ON customer_state
    FOR DELETE
    USING (true);

-- 6. 实时订阅支持（可选，用于多人实时同步）
ALTER PUBLICATION supabase_realtime ADD TABLE customer_state;
