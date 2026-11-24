# 紫微技能：地天盘 / 前程盘

两个用于**结构化命理推演**的技能文档。都基于紫微斗数，但解决的问题不同：

| 技能 | 解决的问题 | 输出 |
|---|---|---|
| **地天盘** | 手上有一个具体决定，该不该做、能不能成 | 三层校验 + 飞化验证 + 四象限结论 |
| **前程盘** | 没有具体选项，只想看方向、节奏和窗口 | 可行域 → 大限档位 → 未来三年 → 路径与代价 |

## 目录结构

```text
skills/
├── 地天盘/
│   ├── SKILL.md          # 方法、判定矩阵、禁区
│   └── 使用说明.md        # 操作步骤与虚构示例
└── 前程盘/
    ├── SKILL.md          # 六宫判定、大限四档、输出契约
    └── scripts/
        └── qiancheng.py  # 盘面摘要与报告结构校验
```

## 依赖

两个技能都不自带排盘引擎，需要配合以下技能使用（不在本仓库）：

- **ziwei-doushu**：本地排盘、个人档案版本隔离、十二宫报告。依赖 Node.js ≥18、Python ≥3.9、`iztro` 2.6.4。
- **meihua-yishu**：梅花易数起卦与断卦，地天盘的第三层需要它。

`前程盘/scripts/qiancheng.py` 只读 `chart.json`，不依赖 Node。

## 安装

### 方式一：复制到项目（推荐）

Trae 从项目根目录的 `.trae/skills/` 加载技能。

```bash
git clone https://github.com/282610325/ziwei-skills.git
cd ziwei-skills

mkdir -p /path/to/your-project/.trae/skills
cp -R skills/地天盘 skills/前程盘 /path/to/your-project/.trae/skills/
```

### 方式二：只取两个目录

不想保留仓库时，克隆到临时目录再复制：

```bash
tmp=$(mktemp -d)
git clone --depth 1 https://github.com/282610325/ziwei-skills.git "$tmp"
cp -R "$tmp/skills/地天盘" "$tmp/skills/前程盘" /path/to/your-project/.trae/skills/
rm -rf "$tmp"
```

### 补齐依赖（必做）

本仓库不含排盘与起卦引擎。缺下面两个技能时：地天盘跑不起来，前程盘只能做结构校验、取不到盘。

```bash
# 1) 排盘引擎：ziwei-doushu
#    按其文档放入 .trae/skills/ziwei-doushu，再安装锁定依赖
npm ci --prefix /path/to/your-project/.trae/skills/ziwei-doushu --ignore-scripts

# 2) 起卦引擎：meihua-yishu
#    放入 .trae/skills/meihua-yishu，地天盘第三层需要
```

环境检查：

```bash
node -v      # 需要 >= 18
python3 -V   # 需要 >= 3.9
```

### 验证安装

以前程盘为例（需要一份已建好的命盘）：

```bash
python3 /path/to/your-project/.trae/skills/前程盘/scripts/qiancheng.py digest \
  --chart /path/to/your-project/命理档案/YYYY-MM-DD_姓名/versions/vNNNN/chart.json
```

能输出六宫、三个大限和流年四化，就是装好了。报 `命盘不存在`，先走 `ziwei-doushu` 的建档流程生成 `chart.json`。

### 五分钟快速开始

1. 把 `skills/` 下两个目录复制到项目的 `.trae/skills/`
2. 放入 `ziwei-doushu`、`meihua-yishu`
3. `npm ci` 安装排盘依赖
4. 用 `ziwei-doushu` 建档，得到 `chart.json`
5. 在对话里说：「前程盘，问：我未来几年该往哪走」

### 安装说明

- 文档里的 `/path/to/workspace` 是占位符，替换成你的实际路径。
- Windows 下把 `cp -R` 换成 `xcopy /E /I`，路径分隔符相应调整。
- `flow.cjs`（流月/流日）属于 `ziwei-doushu`，不在本仓库；前程盘的可选月日窗口需要它。

## 使用

```text
地天盘，问：这个 offer 该不该接
前程盘，问：我未来几年该往哪走
```

地天盘的完整流程：先读当前版本 `chart.json`，再按梅花技能起卦，最后做飞化验证。
前程盘的完整流程：先跑 `qiancheng.py digest` 取盘面摘要，写报告草稿，再跑 `check` 校验结构。

## 数据与隐私

本仓库已做脱敏处理：

- 不含任何真实姓名、化名、生日、出生地、时区记录
- 不含任何真实命盘数据、`person_id`、命盘哈希或占卜记录
- 示例中的盘面数值一律为占位符或虚构值，不对应任何真实档案
- 文档中的路径均为 `/path/to/...` 占位符

**注意**：运行技能会在本地生成 `命理档案/` 目录，里面是真实个人资料与命盘。请勿将其提交到公开仓库，建议在 `.gitignore` 中排除：

```gitignore
命理档案/
*.chart.json
```

## 方法边界

1. **地天盘**的三元映射（体卦＝命宫、用卦＝所问之事）是自造方法，不是古籍。紫微与梅花在历史上没有系统合并过。
2. **前程盘**的「前程六宫」加权与大限四档，同样是操作化定义，不是传统定论。
3. 两个技能都**不预测具体职位、收入、公司或事件**，只缩小可行域、标出节奏、排除自欺选项。
4. 命理不具科学预测效力，不替代职业规划、医疗、法律、投资建议。
5. 如果长期复盘命中率不高于「什么都不说」，应当停用。这句话写在这里，防止以后自己骗自己。

## 许可证

以 [MIT License](LICENSE) 发布，可自由使用、修改与分发，需保留版权声明。命理结论不构成任何明示或暗示的保证。
