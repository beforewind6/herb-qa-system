# 杏林问答前端重设计 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `static/index.html` 从通用暖棕色调重构为浓郁中国风（宣纸书卷风）单文件前端，功能逻辑不变。

**Architecture:** 单文件 HTML，CSS 变量驱动的双主题（日间/夜读），内联 JS 保留全部现有逻辑（会话管理、WebSocket 流式对话、历史搜索），只改 CSS 和 HTML 结构。

**Tech Stack:** 纯 HTML/CSS/JS，零外部框架，CDN 引用 Font Awesome 6 和 marked.js（保持不变）

## Global Constraints

- 单文件 HTML，内联 CSS/JS，零外部框架依赖
- 保持现有所有功能：多会话、流式 WebSocket、历史搜索、暗色模式、快速提问
- 不修改任何后端代码
- CSS 变量全部替换为新配色，class 命名保持兼容
- 暗色模式更名为"夜读"

---

### Task 1: 删除废弃文件并准备 Git 环境

**Files:**
- Delete: `static/src/App.jsx`
- Delete: `static/old_index.html`

- [ ] **Step 1: 删除废弃文件**

```bash
rm static/src/App.jsx static/old_index.html
```

- [ ] **Step 2: 确认文件已删除**

```bash
ls static/
```

Expected: 只剩 `index.html`（可能还有一个空的 `src/` 目录）

- [ ] **Step 3: 如果 static/src/ 目录为空，也删除它**

```bash
rmdir static/src 2>/dev/null || true
```

- [ ] **Step 4: 提交**

```bash
git add -A static/
git commit -m "chore: remove unused static files (App.jsx, old_index.html)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: 重写 CSS 变量与全局样式

**Files:**
- Modify: `static/index.html` — 替换 `:root` 中的 CSS 变量和全局样式

**Interfaces:**
- Consumes: 无
- Produces: CSS 变量名保持兼容（`--bg`, `--text`, `--primary` 等），仅替换色值

- [ ] **Step 1: 备份当前文件**

```bash
cp static/index.html static/index.html.bak
```

- [ ] **Step 2: 替换 `<style>` 标签中的 `:root` 和 `body.dark-mode` CSS 变量块**

找到 `<style>` 标签内的 `:root` 块（约第 9-32 行），替换为以下内容：

```css
:root {
    --bg: #f5f0e8;
    --bg-card: #faf7f0;
    --bg-sidebar: #ede6d8;
    --text: #2c2416;
    --text-muted: #8b7a62;
    --text-dim: #b8a387;
    --border: #d4c8b0;
    --primary: #c43a31;
    --primary-light: #d4533d;
    --primary-dark: #9a2e27;
    --accent: #c43a31;
    --accent-soft: #f5e8e0;
    --herb: #5b8c5a;
    --herb-light: #e8efe2;
    --gold: #b8963e;
    --gold-light: #faf3e6;
    --radius: 3px;
    --radius-sm: 2px;
    --shadow: 0 2px 8px rgba(44, 36, 22, 0.08);
    --shadow-lg: 0 4px 20px rgba(44, 36, 22, 0.12);
    --transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    --ink-spread: 0 0 0 4px rgba(184, 150, 62, 0.12);
}

body.dark-mode {
    --bg: #1a1c1f;
    --bg-card: #222420;
    --bg-sidebar: #1d1f1b;
    --text: #d4c8b8;
    --text-muted: #9b8e78;
    --text-dim: #6b5f50;
    --border: #3a3528;
    --primary: #b84a3a;
    --primary-dark: #8a3028;
    --accent-soft: #2a2018;
    --herb-light: #1a2218;
    --gold-light: #2a2218;
    --shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    --shadow-lg: 0 4px 20px rgba(0, 0, 0, 0.4);
    --ink-spread: 0 0 0 4px rgba(184, 150, 62, 0.2);
}
```

- [ ] **Step 3: 替换 body 样式，添加宣纸纹理背景**

找到 `body { ... }` 块（约第 51-60 行），替换为：

```css
body {
    font-family: 'Noto Serif SC', 'STSong', 'SimSun', 'Songti SC', serif;
    line-height: 1.8;
    color: var(--text);
    background: var(--bg);
    background-image:
        radial-gradient(ellipse at 10% 20%, rgba(180, 160, 140, 0.15) 0%, transparent 50%),
        radial-gradient(ellipse at 90% 80%, rgba(180, 160, 140, 0.12) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(200, 190, 170, 0.08) 0%, transparent 70%);
    display: flex;
    flex-direction: column;
    height: 100vh;
    transition: background 0.4s, color 0.4s;
}

body::before {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background:
        repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(180, 160, 140, 0.03) 2px, rgba(180, 160, 140, 0.03) 3px),
        repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(180, 160, 140, 0.02) 2px, rgba(180, 160, 140, 0.02) 3px);
}
```

- [ ] **Step 4: 提交**

```bash
git add static/index.html
git commit -m "style: replace CSS variables and body with 宣纸书卷 theme

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: 重写 Header 匾额样式

**Files:**
- Modify: `static/index.html` — header 相关 CSS 和 HTML

- [ ] **Step 1: 替换 header CSS**

找到 `/* === Header === */` 区块（约第 62-129 行），替换为：

```css
/* === Header === */
header {
    background: linear-gradient(180deg, #5a3020 0%, #4a2818 60%, #3a1f10 100%);
    color: #efe4d8;
    padding: 0.8rem 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow:
        0 2px 12px rgba(44, 20, 10, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    border-bottom: 2px solid var(--gold);
    z-index: 10;
}

header::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(180deg, rgba(0,0,0,0.15), transparent);
}

.header-content {
    display: flex;
    align-items: center;
    gap: 14px;
}

.header-seal {
    width: 42px;
    height: 42px;
    border: 2px solid #c43a31;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #c43a31;
    font-size: 1.4rem;
    font-weight: 900;
    font-family: 'STKaiti', 'KaiTi', 'Noto Serif SC', serif;
    transform: rotate(-3deg);
    flex-shrink: 0;
}

.header-text {
    display: flex;
    flex-direction: column;
    align-items: center;
}

header h1 {
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    font-family: 'STKaiti', 'KaiTi', 'Noto Serif SC', serif;
    line-height: 1.2;
}

.header-subtitle {
    font-size: 0.7rem;
    opacity: 0.6;
    letter-spacing: 0.12em;
    font-family: 'Noto Serif SC', serif;
}
```

- [ ] **Step 2: 替换 header-right 按钮样式**

```css
.header-right {
    position: absolute;
    right: 1.5rem;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    gap: 10px;
}

.theme-toggle, .github-link {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #efe4d8;
    width: 34px;
    height: 34px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 0.95rem;
    transition: var(--transition);
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
}

.theme-toggle:hover, .github-link:hover {
    background: rgba(255, 255, 255, 0.18);
    border-color: var(--gold);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
```

- [ ] **Step 3: 替换 header HTML**

找到 `<header>` 标签内的 HTML（约第 680-696 行），替换为：

```html
<header>
    <div class="header-content">
        <div class="header-seal">问答</div>
        <div class="header-text">
            <h1>杏林问答</h1>
            <div class="header-subtitle">中医药知识智能问答系统</div>
        </div>
    </div>
    <div class="header-right">
        <a href="https://github.com" target="_blank" class="github-link" title="GitHub">
            <i class="fab fa-github"></i>
        </a>
        <button class="theme-toggle" id="themeToggle" title="切换夜读模式">
            <i class="fas fa-moon"></i>
        </button>
    </div>
</header>
```

- [ ] **Step 4: 提交**

```bash
git add static/index.html
git commit -m "style: redesign header as 匾额 with seal stamp

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: 重写侧边栏（古籍目录风格）

**Files:**
- Modify: `static/index.html` — sidebar 相关 CSS

- [ ] **Step 1: 替换 sidebar CSS**

找到 `/* === Sidebar === */` 区块（约第 151-283 行），替换为：

```css
/* === Sidebar === */
.sidebar {
    width: 280px;
    background: var(--bg-sidebar);
    padding: 1.2rem;
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    transition: var(--transition);
}

.search-box {
    padding: 0.55rem 1rem;
    border-radius: 3px;
    border: 1.5px solid var(--border);
    background: var(--bg-card);
    color: var(--text);
    font-size: 0.85rem;
    margin-bottom: 1rem;
    transition: var(--transition);
    font-family: inherit;
    outline: none;
}

.search-box:focus {
    border-color: var(--gold);
    box-shadow: var(--ink-spread);
}

.session-controls {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.2rem;
}

.new-session-btn {
    flex: 1;
    padding: 0.5rem 0.5rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--primary);
    cursor: pointer;
    font-size: 0.82rem;
    transition: var(--transition);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.3rem;
    font-family: inherit;
    background: var(--primary);
    color: #fff;
}
.new-session-btn:hover {
    background: var(--primary-light);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(196, 58, 49, 0.25);
}

.clear-history-btn {
    flex: 1;
    padding: 0.5rem 0.5rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    cursor: pointer;
    font-size: 0.82rem;
    transition: var(--transition);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.3rem;
    font-family: inherit;
    background: transparent;
    color: var(--text-muted);
}
.clear-history-btn:hover {
    background: #fdeded;
    color: var(--accent);
    border-color: var(--accent);
}

.history-title {
    font-weight: 700;
    margin-bottom: 1rem;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    letter-spacing: 0.06em;
    font-family: 'STKaiti', 'KaiTi', 'Noto Serif SC', serif;
}
.history-title::before {
    content: '';
    display: inline-block;
    width: 3px;
    height: 1em;
    background: var(--gold);
    border-radius: 1px;
}

.history-list {
    flex: 1;
    overflow-y: auto;
    scrollbar-width: thin;
}

.history-item {
    padding: 0.7rem 0.8rem;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: var(--transition);
    margin-bottom: 0.4rem;
    background: var(--bg-card);
    border-left: 3px solid transparent;
    position: relative;
}
.history-item::before {
    content: '';
    position: absolute;
    left: -3px;
    top: 50%;
    transform: translateY(-50%) scale(0);
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--primary);
    transition: transform 0.25s ease;
}
.history-item:hover {
    border-left-color: transparent;
    transform: translateX(4px);
    box-shadow: var(--shadow);
}
.history-item:hover::before {
    transform: translateY(-50%) scale(1);
}

.history-question {
    font-weight: 600;
    font-size: 0.85rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--text);
}

.history-answer {
    color: var(--text-muted);
    font-size: 0.78rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 2px;
}

.history-item + .history-item {
    border-top: 1px solid rgba(184, 150, 62, 0.15);
    margin-top: 0.2rem;
    padding-top: 0.8rem;
}

.session-info {
    font-size: 0.72rem;
    color: var(--text-dim);
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px dashed var(--border);
    font-family: 'JetBrains Mono', 'Courier New', monospace;
}
```

- [ ] **Step 2: 提交**

```bash
git add static/index.html
git commit -m "style: redesign sidebar as 古籍目录 with vermillion dot hover

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: 重写聊天气泡与主内容区

**Files:**
- Modify: `static/index.html` — 聊天区域、消息气泡、Welcome 卡片 CSS

- [ ] **Step 1: 替换 main-content 和 chat-history CSS**

找到 `/* === Main Chat === */` 区块，将 `.main-content` 和 `.chat-history` 替换为：

```css
/* === Main Chat === */
.main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    position: relative;
    min-width: 0;
    background: var(--bg-card);
    box-shadow: inset 0 0 60px rgba(44, 36, 22, 0.04);
}

.chat-history {
    flex: 1;
    padding: 1.5rem 2rem;
    overflow-y: auto;
    scroll-behavior: smooth;
    scrollbar-width: thin;
}
```

- [ ] **Step 2: 替换消息气泡 CSS**

找到 `/* === Messages === */` 区块，替换为：

```css
/* === Messages === */
.message {
    margin-bottom: 1.5rem;
    display: flex;
    flex-direction: column;
    animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.message-header {
    display: flex;
    align-items: center;
    margin-bottom: 0.35rem;
    font-size: 0.78rem;
    color: var(--text-muted);
}

.avatar {
    width: 30px;
    height: 30px;
    border-radius: 3px;
    margin-right: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
}

.user-msg .avatar {
    background: var(--primary);
    color: #fff;
}
.sys-msg .avatar {
    background: var(--herb-light);
    color: var(--herb);
    border: 1px solid var(--herb);
}

.message-content {
    padding: 0.8rem 1.1rem;
    border-radius: var(--radius);
    max-width: 78%;
    word-break: break-word;
    line-height: 1.85;
    font-size: 0.95rem;
    box-shadow: var(--shadow);
}

.user-msg {
    align-self: flex-end;
    align-items: flex-end;
}
.user-msg .message-content {
    background: linear-gradient(135deg, #c43a31, #a8322a);
    color: #fff;
    border-bottom-right-radius: 2px;
    box-shadow: 0 2px 8px rgba(196, 58, 49, 0.2);
}

.sys-msg {
    align-self: flex-start;
}
.sys-msg .message-content {
    background: rgba(245, 240, 232, 0.6);
    border-left: 3px solid var(--gold);
    border-radius: 2px;
    border-top-right-radius: var(--radius);
    border-bottom-right-radius: var(--radius);
}

/* Markdown content styles */
.message-content p { margin-bottom: 0.5rem; }
.message-content p:last-child { margin-bottom: 0; }
.message-content pre {
    background: rgba(0, 0, 0, 0.04);
    padding: 0.8rem 1rem;
    border-radius: 2px;
    overflow-x: auto;
    margin: 0.5rem 0;
    font-size: 0.85rem;
    border-left: 2px solid var(--gold);
}
body.dark-mode .message-content pre {
    background: rgba(0, 0, 0, 0.25);
}
.message-content code {
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
    font-size: 0.88rem;
}
.message-content ul, .message-content ol {
    padding-left: 1.5rem;
    margin: 0.5rem 0;
}
```

- [ ] **Step 3: 替换 welcome card CSS**

```css
/* === Welcome Card === */
.welcome-card {
    text-align: center;
    padding: 3rem 2rem;
    max-width: 520px;
    margin: 0 auto;
}

.welcome-card::before {
    content: '';
    display: block;
    width: 40px;
    height: 3px;
    background: var(--gold);
    margin: 0 auto 1.5rem;
    border-radius: 1px;
}

.welcome-icon {
    font-size: 3rem;
    margin-bottom: 0.8rem;
    opacity: 0.8;
}

.welcome-card h2 {
    font-family: 'STKaiti', 'KaiTi', 'Noto Serif SC', serif;
    font-size: 1.4rem;
    color: var(--text);
    margin-bottom: 0.8rem;
    letter-spacing: 0.08em;
}

.welcome-card p {
    color: var(--text-muted);
    font-size: 0.88rem;
    line-height: 2;
}

.category-chips {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 1.5rem;
}

.category-chip {
    padding: 0.35rem 0.9rem;
    border-radius: 2px;
    font-size: 0.8rem;
    border: 1px solid var(--gold);
    background: var(--gold-light);
    color: var(--text-muted);
    cursor: default;
    transition: var(--transition);
    font-family: 'STKaiti', 'KaiTi', serif;
    letter-spacing: 0.04em;
}

.category-chip:hover {
    border-color: var(--herb);
    color: var(--herb);
    background: var(--herb-light);
}
```

- [ ] **Step 4: 更新 welcome-card HTML**

找到 `.welcome-card` 中的内容，替换为：

```html
<div class="welcome-card">
    <div class="welcome-icon">🏥</div>
    <h2>杏林春暖 · 橘井泉香</h2>
    <p>大医精诚，悬壶济世。<br>
    无论您想了解中药药性、方剂配伍，<br>还是中医理论、针灸穴位，<br>我都能为您答疑解惑。</p>
    <div class="category-chips">
        <span class="category-chip">中药基础</span>
        <span class="category-chip">方剂学</span>
        <span class="category-chip">中医基础理论</span>
        <span class="category-chip">针灸学</span>
    </div>
</div>
```

- [ ] **Step 5: 提交**

```bash
git add static/index.html
git commit -m "style: redesign chat bubbles as 印章 + 引文格式, welcome as letter

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6: 重写输入区（砚台意象）与动画细节

**Files:**
- Modify: `static/index.html` — 输入区 CSS、动画

- [ ] **Step 1: 替换输入区 CSS**

找到 `/* === Chat Input === */` 区块，替换为：

```css
/* === Chat Input === */
.chat-input-container {
    padding: 1rem 1.5rem 1.2rem;
    border-top: 1px solid var(--border);
    background: var(--bg-card);
}

.source-filter {
    display: flex;
    align-items: center;
    margin-bottom: 0.6rem;
    font-size: 0.82rem;
    color: var(--text-muted);
}

.source-filter select {
    margin-left: 0.5rem;
    padding: 0.3rem 0.8rem;
    border-radius: 2px;
    border: 1.5px solid var(--border);
    background: var(--bg-sidebar);
    color: var(--text);
    font-family: inherit;
    font-size: 0.8rem;
    cursor: pointer;
    transition: var(--transition);
    outline: none;
}

.source-filter select:focus {
    border-color: var(--gold);
    box-shadow: var(--ink-spread);
}

.input-group {
    display: flex;
    position: relative;
}

.chat-input {
    flex: 1;
    padding: 0.75rem 3.2rem 0.75rem 1.2rem;
    border: 1.5px solid var(--border);
    border-radius: 3px;
    font-size: 0.95rem;
    resize: none;
    min-height: 48px;
    max-height: 160px;
    overflow-y: auto;
    background: #e8e0d5;
    color: #2c2416;
    font-family: inherit;
    transition: var(--transition);
    outline: none;
    line-height: 1.5;
}

body.dark-mode .chat-input {
    background: #2a2824;
    color: #d4c8b8;
}

.chat-input:focus {
    border-color: var(--gold);
    box-shadow: var(--ink-spread);
}

.chat-input::placeholder {
    color: var(--text-dim);
}

.send-btn {
    position: absolute;
    right: 6px;
    top: 50%;
    transform: translateY(-50%);
    width: 40px;
    height: 40px;
    background: var(--primary);
    color: #fff;
    border: none;
    border-radius: 3px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: var(--transition);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'STKaiti', 'KaiTi', serif;
    font-weight: 700;
    letter-spacing: 0.05em;
}

.send-btn:hover {
    transform: translateY(-50%) scale(1.06);
    box-shadow: 0 4px 12px rgba(196, 58, 49, 0.3);
}

.send-btn:active {
    transform: translateY(-50%) scale(0.96);
    transition: 0.08s ease;
}

.send-btn:disabled {
    background: var(--text-dim);
    cursor: not-allowed;
    box-shadow: none;
}

.send-btn:disabled:hover {
    transform: translateY(-50%) scale(1);
}

/* === Quick Replies === */
.quick-replies {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.7rem;
}

.quick-reply-btn {
    padding: 0.3rem 0.9rem;
    background: var(--gold-light);
    border: 1px solid var(--gold);
    border-radius: 2px;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 0.78rem;
    transition: var(--transition);
    font-family: 'STKaiti', 'KaiTi', 'Noto Serif SC', serif;
    letter-spacing: 0.03em;
}

.quick-reply-btn:hover {
    background: var(--gold-light);
    border-color: var(--primary);
    color: var(--primary);
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(196, 58, 49, 0.1);
}
```

- [ ] **Step 2: 替换 typing indicator 和 loading overlay CSS**

```css
/* === Typing Indicator === */
.typing-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 0.7rem 1.2rem;
    background: rgba(245, 240, 232, 0.6);
    border-left: 3px solid var(--gold);
    border-radius: 2px;
    border-top-right-radius: var(--radius);
    border-bottom-right-radius: var(--radius);
    margin-bottom: 1rem;
    box-shadow: var(--shadow);
}

.typing-indicator span {
    width: 4px;
    height: 14px;
    border-radius: 2px;
    background: var(--gold);
    animation: inkDip 1.2s infinite;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.15s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; }

@keyframes inkDip {
    0%, 60%, 100% { transform: scaleY(0.6); opacity: 0.4; }
    30% { transform: scaleY(1); opacity: 1; }
}

/* === Loading Overlay === */
.loading-overlay {
    position: absolute;
    inset: 0;
    background: rgba(245, 240, 232, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10;
    visibility: hidden;
    backdrop-filter: blur(3px);
    transition: var(--transition);
}
body.dark-mode .loading-overlay {
    background: rgba(26, 28, 31, 0.5);
}

.ink-spinner {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: radial-gradient(circle, var(--text-muted) 10%, transparent 60%);
    animation: inkSpread 1.2s ease-in-out infinite;
    opacity: 0.6;
}

@keyframes inkSpread {
    0%, 100% { transform: scale(0.8); opacity: 0.3; }
    50% { transform: scale(1.2); opacity: 0.7; }
}
```

- [ ] **Step 3: 替换 loading overlay HTML**

将 `.loading-overlay` 中的 spinner 替换为：

```html
<div class="loading-overlay" id="loadingOverlay">
    <div class="ink-spinner"></div>
</div>
```

- [ ] **Step 4: 提交**

```bash
git add static/index.html
git commit -m "style: redesign input area as 砚台, add ink animations

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 7: 更新 JS 中的主题切换与暗色模式逻辑

**Files:**
- Modify: `static/index.html` — 替换 `updateTheme` 函数、welcome card 重置逻辑、chat-history reset 逻辑

- [ ] **Step 1: 更新 `updateTheme` 函数**

找到 `updateTheme` 函数（约第 820-828 行），替换为：

```js
function updateTheme() {
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-dragon"></i>';
        themeToggle.title = '切换到日间模式';
    } else {
        document.body.classList.remove('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        themeToggle.title = '切换到夜读模式';
    }
}
```

- [ ] **Step 2: 更新 `resetChatHistory` 函数中的 welcome card HTML 以匹配新的设计**

找到 `resetChatHistory` 函数（约第 915-927 行），替换为：

```js
function resetChatHistory() {
    chatHistory.innerHTML =
        '<div class="welcome-card">' +
        '<div class="welcome-icon">🏥</div>' +
        '<h2>杏林春暖 · 橘井泉香</h2>' +
        '<p>大医精诚，悬壶济世。<br>' +
        '无论您想了解中药药性、方剂配伍，<br>还是中医理论、针灸穴位，<br>我都能为您答疑解惑。</p>' +
        '<div class="category-chips">' +
        '<span class="category-chip">中药基础</span>' +
        '<span class="category-chip">方剂学</span>' +
        '<span class="category-chip">中医基础理论</span>' +
        '<span class="category-chip">针灸学</span>' +
        '</div></div>';
}
```

- [ ] **Step 3: 更新 `addMessage` 中的 avatar HTML**

找到 `addMessage` 函数中的 avatar 部分（约第 1032-1037 行），替换为：

```js
if (type === 'user') {
    headerEl.innerHTML = '<div class="avatar"><i class="fas fa-user"></i></div><span>问</span>';
} else {
    headerEl.innerHTML = '<div class="avatar">藥</div><span>杏林</span>';
}
```

- [ ] **Step 4: 提交**

```bash
git add static/index.html
git commit -m "style: update JS theme toggle, welcome card, avatar labels

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 8: 最终验证与清理

**Files:**
- Modify: `static/index.html` — 删除备份文件

- [ ] **Step 1: 验证文件完整性**

```bash
wc -l static/index.html
```

确认文件行为有效 HTML。

- [ ] **Step 2: 启动服务进行手动验证**

```bash
python app.py &
sleep 2
echo "Server should be running on http://localhost:8080"
```

- [ ] **Step 3: 删除备份文件**

```bash
rm static/index.html.bak
```

- [ ] **Step 4: 提交并推送**

```bash
git add static/index.html
git commit -m "chore: remove backup file, final cleanup

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
git push
```

---

## Self-Review Results

1. **Spec coverage**: 所有设计要素都有对应任务 — 色彩/字体 (Task 2), 宣纸质感 (Task 2), Header 匾额 (Task 3), 侧边栏古籍目录 (Task 4), 宣纸笺主区域 (Task 5), 印章气泡 (Task 5), 砚台输入区 (Task 6), 徽动效 (Task 5/6), 夜读模式 (Task 2/7)
2. **Placeholder scan**: 无 TBD/TODO，所有步骤都有具体代码
3. **Type consistency**: JS 函数名保持与现有一致（`updateTheme`, `resetChatHistory`, `addMessage`），CSS class 名兼容
