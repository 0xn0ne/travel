# Phase 10 UAT (User Acceptance Testing)

## Phase Info
- **Phase**: 10-map-sharing
- **Status**: In Progress
- **Started**: 2026-04-17
- **Completed**: 

## Test Results Summary

| Test ID | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| UAT-10-01 | MAP-01: POI坐标丰富 | 🔄 Pending | 验证API返回坐标 |
| UAT-10-02 | MAP-02: 地图可视化 | 🔄 Pending | 验证地图渲染 |
| UAT-10-03 | MAP-03: 天数筛选 | 🔄 Pending | 验证天数切换 |
| UAT-10-04 | MAP-04: 双向同步 | 🔄 Pending | 验证点击联动 |
| UAT-10-05 | SHARE-01: 分享按钮 | 🔄 Pending | 验证复制链接 |
| UAT-10-06 | SHARE-02: OG元数据 | 🔄 Pending | 验证meta端点 |

## Detailed Test Cases

### UAT-10-01: POI 坐标丰富 (MAP-01)

**测试步骤:**
1. 创建一个包含 POI 的行程
2. 调用 GET /api/itineraries/{id}
3. 检查返回的 POI 数据

**预期结果:**
- 每个有坐标的 POI 应该包含 `latitude` 和 `longitude` 字段
- 坐标的值应该是有效的浮点数
- 没有坐标的 POI 应该有 null 值

**实际结果:**
- 状态: 🔄 Pending
- 备注: 

---

### UAT-10-02: 地图可视化 (MAP-02)

**测试步骤:**
1. 打开一个行程详情页面
2. 观察地图显示
3. 检查标记和路线

**预期结果:**
- 地图应该正确加载（高德地图）
- POI 位置应该有标记（Tier 徽章样式）
- 同一天内的 POI 应该有虚线连接
- 不同天数应该有不同的颜色（蓝/绿/橙）

**实际结果:**
- 状态: 🔄 Pending
- 备注:

---

### UAT-10-03: 天数筛选 (MAP-03)

**测试步骤:**
1. 打开多日行程
2. 点击天数选择器（Pill 样式）
3. 观察地图变化

**预期结果:**
- 应该显示所有天数的 Pill 按钮
- 点击某一天应该只显示该天的路线
- 地图应该自动缩放到该天的 POI 范围
- 再次点击应该取消筛选（显示所有天数）

**实际结果:**
- 状态: 🔄 Pending
- 备注:

---

### UAT-10-04: 双向同步 (MAP-04)

**测试步骤:**
1. 点击时间线中的某个 POI
2. 观察地图反应
3. 点击地图中的标记
4. 观察时间线反应

**预期结果:**
- 点击时间线 POI:
  - 地图应该平移到该 POI 位置
  - 对应的标记应该高亮（弹跳动画）
  - 信息窗口应该打开
- 点击地图标记:
  - 时间线应该滚动到对应 POI
  - POI 卡片应该展开
  - 应该有高亮样式（左边框）
- 高亮应该在 3 秒后自动清除

**实际结果:**
- 状态: 🔄 Pending
- 备注:

---

### UAT-10-05: 分享按钮 (SHARE-01)

**测试步骤:**
1. 打开行程页面
2. 点击分享按钮
3. 观察反馈

**预期结果:**
- 按钮应该在标题旁边可见
- 点击后应该复制当前 URL 到剪贴板
- 应该显示成功 Toast（"链接已复制，分享给朋友吧！"）
- 如果剪贴板 API 失败，应该降级使用 execCommand

**实际结果:**
- 状态: 🔄 Pending
- 备注:

---

### UAT-10-06: OG 元数据 (SHARE-02)

**测试步骤:**
1. 调用 GET /api/itineraries/{id}/meta
2. 检查返回数据

**预期结果:**
- 端点应该不需要认证
- 应该返回 JSON: `{title, description, city}`
- title 应该从行程的 title 字段获取
- description 应该从行程的 summary 字段获取
- 如果行程不存在，应该返回 404

**实际结果:**
- 状态: 🔄 Pending
- 备注:

---

## Issues Found

| Issue ID | Severity | Description | Fix Plan |
|----------|----------|-------------|----------|
| | | | |

## Conclusion

- **Overall Status**: 🔄 In Progress
- **Tests Passed**: 0/6
- **Tests Failed**: 0/6
- **Tests Pending**: 6/6

**Next Steps:**
1. Execute UAT test cases
2. Record actual results
3. Fix any issues found
4. Mark Phase 10 as verified
