# Astro Starter Kit: Minimal

```sh
npm create astro@latest -- --template minimal
```

> 🧑‍🚀 **Seasoned astronaut?** Delete this file. Have fun!

## 🚀 Project Structure

Inside of your Astro project, you'll see the following folders and files:

```text
/
├── public/
├── src/
│   └── pages/
│       └── index.astro
└── package.json
```

Astro looks for `.astro` or `.md` files in the `src/pages/` directory. Each page is exposed as a route based on its file name.

There's nothing special about `src/components/`, but that's where we like to put any Astro/React/Vue/Svelte/Preact components.

Any static assets, like images, can be placed in the `public/` directory.

## 🧞 Commands

All commands are run from the root of the project, from a terminal:

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs dependencies                            |
| `npm run dev`             | Starts local dev server at `localhost:4321`      |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |
| `npm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `npm run astro -- --help` | Get help using the Astro CLI                     |

## 👀 Want to learn more?

Feel free to check [our documentation](https://docs.astro.build) or jump into our [Discord server](https://astro.build/chat).

---

## 🔍 新词监测

每日从全部信源标题中自动筛出刚冒头的新名词（新工具、新模型、新开源项目），用于公众号选题预警与快速建站信号识别。

### 判定口径

**三通道抽词**：
1. GitHub 仓库名：从 URL 提取 `github.com/<owner>/<repo>`
2. 拉丁词组：标题中的驼峰命名（DeepSeek）、版本号（V4.1）、全大写缩写（AI）
3. 中文括号词：《》「」"" 中的 1-8 字词组

**两档状态**：
- `new`（全新）：过去 14 天未出现，且今日 ≥2 条
- `rising`（升温）：过去 14 天曾出现，且今日量 ≥ 历史日均 ×3 且 ≥3 条

**强信号**：今日 ≥5 条且最高分 ≥8，或 GitHub 仓库词且条目 score ≥8

### 使用方式

```bash
# 手动运行
python scripts/new_terms.py --date 2026-10-20

# 单元测试
python scripts/test_new_terms.py
```

### 产出

- 数据文件：`src/data/v4/new-terms-YYYY-MM-DD.json` + `new-terms-latest.json`
- 展示页面：`/new-terms/`（强信号区置顶，全新/升温分组）
- Workflow 自动运行：每日定时班次结束后执行

### 展示结构

- **强信号区**：`strong=true` 的条目置顶，带 ★ 标记
- **全新组**：`status=new` 的条目
- **升温组**：`status=rising` 的条目
- 每条含：词本身、kind 徽章（开源项目/产品模型/中文新词）、status 徽章、提及次数、最高分、首现日期、最多 3 条样本链接

---

## 🔍 新词监测

每日从全部信源标题中自动筛出刚冒头的新名词（新工具、新模型、新开源项目），用于公众号选题预警与快速建站信号识别。

### 判定口径

**三通道抽词**：
1. GitHub 仓库名：从 URL 提取 `github.com/<owner>/<repo>`
2. 拉丁词组：标题中的驼峰命名（DeepSeek）、版本号（V4.1）、全大写缩写（AI）
3. 中文括号词：《》「」"" 中的 1-8 字词组

**两档状态**：
- `new`（全新）：过去 14 天未出现，且今日 ≥2 条
- `rising`（升温）：过去 14 天曾出现，且今日量 ≥ 历史日均 ×3 且 ≥3 条

**强信号**：今日 ≥5 条且最高分 ≥8，或 GitHub 仓库词且条目 score ≥8

### 使用方式

```bash
# 手动运行
python scripts/new_terms.py --date 2026-10-20

# 单元测试
python scripts/test_new_terms.py
```

### 产出

- 数据文件：`src/data/v4/new-terms-YYYY-MM-DD.json` + `new-terms-latest.json`
- 展示页面：`/new-terms/`（强信号区置顶，全新/升温分组）
- Workflow 自动运行：每日定时班次结束后执行

### 展示结构

- **强信号区**：`strong=true` 的条目置顶，带 ★ 标记
- **全新组**：`status=new` 的条目
- **升温组**：`status=rising` 的条目
- 每条含：词本身、kind 徽章（开源项目/产品模型/中文新词）、status 徽章、提及次数、最高分、首现日期、最多 3 条样本链接

