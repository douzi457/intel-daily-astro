# P0 第四轮验收说明

**提交**: `latest`  
**日期**: 2026-10-11

---

## 1. LLM批量生成（已实现，待配置Key启用）

### 代码位置
- `scripts/intel_officer_processor.py`: `_call_llm_for_judgment()` 方法

### 调用逻辑
```python
# 每天只调用1次，5条核心信号批量发送
api_key = os.environ.get("AGNES_API_KEY") or os.environ.get("ZHIPU_API_KEY")
model = os.environ.get("AGNES_MODEL") or "agnes-3.0"

# 降级处理
if not api_key:
    print("警告: AGNES_API_KEY 或 ZHIPU_API_KEY 未配置，使用模板输出", file=sys.stderr)
    return None, None, None  # 降级为模板
```

### Prompt设计
- System prompt 包含画像定义："读者是关注AI开源项目与Agent技术的创作者"
- 要求输出JSON数组，每条包含 `index`, `why_it_matters`, `suggested_action`
- temperature=0.3，max_tokens=2000

### 成本估算
- 单次调用约 1000-2000 tokens 输入，1500-2500 tokens 输出
- 智谱API定价约 ¥0.01/千tokens
- 每天成本约 ¥0.03-0.05，远低于¥0.1红线

### Token统计
已添加 `quality.llm_usage` 字段：
```json
{
  "llm_usage": {
    "model": "agnes-3.0",
    "input_tokens": 1234,
    "output_tokens": 1890,
    "total_tokens": 3124
  }
}
```

---

## 2. 生产数据不一致（待修复）

### 问题
- 页面显示：82.2/698/635
- 最新数据：83.2/698/634
- 差异：质量分+1分，事件数-1

### 原因分析
GitHub Actions可能使用了缓存的构建结果，未包含最新的V2数据文件。

### 解决方案
1. 触发手动构建：https://github.com/douzi457/intel-daily-astro/actions/workflows/build.yml
2. 或等待下次定时构建（UTC 22:00 = CST 06:00）

---

## 3. 硬编码门闩修正

### 当前状态
| # | 门槛 | 状态 | 说明 |
|---|---|---|---|
| 1 | core-event-unique | ✅ PASS | 真实计算 |
| 2 | no-noise-summary | ✅ PASS | 真实检查 |
| 3 | core-five-elements | ✅ PASS | 真实检查 |
| 4 | core-count-valid | ✅ PASS | 真实计数 |
| 5 | watch-action-limits | ✅ PASS | 真实限制 |
| 6 | published-at-known-or-null | ✅ PASS | 真实检查 |
| 7 | three-end-consistency | ❌ SKIP | processor无法验证 |
| 8 | build-passed | ❌ SKIP | CI负责验证 |
| 9 | quality-calculated | ✅ PASS | 真实计算 |

**真实通过: 7/9**

---

## 4. 待办事项

### 老大需要操作
1. **配置API Key**: GitHub Settings → Secrets → 添加 `ZHIPU_API_KEY`
2. **触发构建**: 手动运行 GitHub Actions workflow
3. **截图**: 截取桌面1440px和移动390px页面

### 验收标准达成情况
- [x] 5条核心实质不同、无模板句（降级时模板也有差异化）
- [x] stats.llm_usage 字段已添加
- [x] 7/9硬门槛真实通过 + 2个诚实SKIP
- [ ] LLM调用成功（需配置Key）
- [ ] 生产页面数字与brief.md一致（需重新部署）
- [ ] 截图2张入库

---

**编制**: Agnes (Hermes Agent)  
**下一步**: 等待老大配置Key后重新跑一次采集
