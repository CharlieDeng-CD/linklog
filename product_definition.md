Product Requirement Document (PRD): LinkLog (MVP)（已更名）
Version: 2.0 Status: Ready for Development

1. Executive Summary (项目概述)
LinkLog 是一个基于 AI 的渐进式知识图谱生成器。它旨在解决自学者在接触新领域（如编程）时，因缺乏“前置知识”（Unknown Unknowns）而产生的认知障碍。 核心价值： 不是给用户堆砌资源，而是帮用户理清依赖关系，识别出为了达成目标必须先掌握的“隐形知识”。

2. Core Problem (核心痛点)
盲区焦虑： 用户不知道自己不知道什么（Unknown Unknowns）。

路径缺失： 现有的教程通常是线性的，无法展示知识点之间的立体依赖关系（例如：学 React 前必须懂 ES6）。

信息过载： 用户不需要“所有知识”，只需要“当前路径上的关键知识”。

3. User & Context (用户与场景)
Target User: 具有明确目标但缺乏路径的自学者（例如：想用 Cursor 做 App 的产品经理）。

User Story:

作为用户，我希望输入一个具体的学习目标（如“开发个人博客”）。

系统能为我生成一个包含 3-5 个核心步骤的初始图谱。

当我点击某个我不懂的节点（如“环境配置”）时，系统能展开显示它的前置知识（如“终端命令”）。

点击具体知识点，我能看到“为什么这很重要”的简短解释。

4. MVP Scope & Features (功能范围)
4.1. Intelligent Input (智能输入)
UI: 极简首页，包含一个大输入框。

Logic: 接收自然语言输入，发送给后端 API。

4.2. Progressive Graph Engine (渐进式图谱引擎)
UI: 使用 React Flow 展示节点。

Interaction:

初始加载: 根据用户 Query 生成 Level 1 节点（顶层分类）。

点击展开: 点击 Node，触发 API 请求，基于该 Node 的上下文生成 Level 2 子节点。

节点状态: 区分 Goal (目标)、Action (行动)、Prerequisite (前置知识/卡点)。

视觉区分: Prerequisite 节点需要高亮显示（例如红色或橙色警告色），代表这是必须攻克的难点。

4.3. Context Sidebar (上下文导师)
UI: 点击节点后，右侧滑出侧边栏 (Drawer)。

Content:

Definition: 一句话通俗解释。

Context: 结合用户最初的目标，解释“为什么要学这个”。

Action: 一个微小的行动建议（如：一条具体的指令代码）。

5. Technical Stack & Constraints (技术栈与约束)
Frontend: Next.js (App Router), React Flow (可视化库), TailwindCSS (样式), Lucide React (图标).

Backend: Next.js API Routes (Serverless Functions).

AI Integration: OpenAI API (gpt-4o-mini 或 gpt-3.5-turbo，追求响应速度).

Data Structure (Crucial):

系统必须强制 LLM 输出严格的 JSON 格式，以适配 React Flow。

JSON Schema 示例约束:

JSON

{
  "nodes": [
    { "id": "1", "type": "customNode", "data": { "label": "...", "category": "prerequisite" }, "position": { "x": 0, "y": 0 } }
  ],
  "edges": [
    { "id": "e1-2", "source": "1", "target": "2" }
  ]
}
6. Success Criteria (验收标准)
这部分用于验证 Cursor 写的代码是否达标：

6.1. Functionality (功能可用性)
[ ] JSON 容错性: AI 生成的 JSON 即使偶尔缺少字段，前端渲染也不会白屏/崩溃（需要有 Error Boundary 和默认值处理）。

[ ] 无限展开能力: 用户可以理论上无限点击叶子节点，系统能持续生成下一层级，没有硬编码的层级限制。

[ ] 节点去重: 展开子节点时，如果该概念已在图谱中存在，不应重复生成两个一样的节点。

6.2. Experience (交互体验)
[ ] Streaming/Loading 状态: 在 AI 生成节点的 2-3 秒等待期内，必须有明确的 Loading 动画（如骨架屏或 Spinner），不能让用户以为卡死了。

[ ] 自适应布局: 每次生成新节点后，图谱应自动调整布局 (Auto Layout)，防止节点重叠遮挡。

6.3. Quality (生成质量)
[ ] 上下文一致性: 子节点的解释必须回溯到最初的 User Goal。

Bad: 点击“API”，解释“API 是应用程序接口...”。

Good: 点击“API”，解释“在你的博客项目中，API 负责帮你从后台拿文章数据...”。

7. Development Prompt Strategy (给 Cursor 的提示词策略)
System Prompt 设定: "You are an expert technical mentor. Your goal is to break down complex goals into a dependency graph. Focus on identifying 'unknown unknowns' and prerequisites."

Temperature: 设置为 0.2 - 0.4，保证 JSON 结构的稳定性。

8. example UI
Picture 1: https://gemini.google.com/share/9780df099827
Picture 2: https://gemini.google.com/share/aa78a3335793