(base) hy.joo@nautilus:~/2026/gitprojects/ai-memory-agent/frontend$ npm run dev

> ai-memory-agent-frontend@0.1.0 dev
> vite


  VITE v5.4.21  ready in 689 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://10.244.14.73:3000/
  ➜  Network: http://172.21.0.1:3000/
  ➜  Network: http://172.23.0.1:3000/
  ➜  press h + enter to show help
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/layout/MainLayout.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/auth/components/LoginForm.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/memory/components/MemoryList.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/memory/components/MemorySearch.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/project/components/ProjectManagement.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/chat/components/ChatRoom.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/layout/Sidebar.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/chat/components/MessageInput.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/api" from "src/features/chat/components/MembersPanel.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/Loading.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/Loading.tsx". Does the file exist? (x2)
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/Loading.tsx". Does the file exist? (x3)
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/Loading.tsx". Does the file exist? (x4)
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/EmptyState.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/EmptyState.tsx". Does the file exist? (x2)
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/EmptyState.tsx". Does the file exist? (x3)
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/EmptyState.tsx". Does the file exist? (x4)
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/chat/components/ContextSourcesModal.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/api" from "src/features/auth/api/authApi.ts". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/Loading.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/EmptyState.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/workspace/components/CreateRoomModal.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/chat/components/MessageItem.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/chat/components/SlashCommandMenu.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/ui/button.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/ui/input.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/ui/avatar.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/ui/scroll-area.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/ui/tooltip.tsx". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/api" from "src/features/memory/api/memoryApi.ts". Does the file exist?
2:25:51 AM [vite] Pre-transform error: Failed to resolve import "@/lib/api" from "src/features/chat/api/chatApi.ts". Does the file exist?
2:25:51 AM [vite] Internal server error: Failed to resolve import "@/lib/utils" from "src/components/layout/MainLayout.tsx". Does the file exist?
  Plugin: vite:import-analysis
  File: /home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/src/components/layout/MainLayout.tsx:5:19
  20 |  import { useUIStore } from "@/stores/uiStore";
  21 |  import { CreateRoomModal } from "@/features/workspace/components/CreateRoomModal";
  22 |  import { cn } from "@/lib/utils";
     |                      ^
  23 |  export function MainLayout() {
  24 |    _s();
      at TransformPluginContext._formatError (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49258:41)
      at TransformPluginContext.error (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49253:16)
      at normalizeUrl (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64307:23)
      at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
      at async file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64439:39
      at async Promise.all (index 7)
      at async TransformPluginContext.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64366:7)
      at async PluginContainer.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49099:18)
      at async loadAndTransform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:51978:27)
      at async viteTransformMiddleware (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:62106:24)
2:25:51 AM [vite] Internal server error: Failed to resolve import "@/lib/utils" from "src/features/chat/components/ChatRoom.tsx". Does the file exist?
  Plugin: vite:import-analysis
  File: /home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/src/features/chat/components/ChatRoom.tsx:15:19
  30 |  import { useUIStore } from "@/stores/uiStore";
  31 |  import { useWebSocket } from "@/hooks/useWebSocket";
  32 |  import { cn } from "@/lib/utils";
     |                      ^
  33 |  import { useQueryClient } from "@tanstack/react-query";
  34 |  export function ChatRoom() {
      at TransformPluginContext._formatError (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49258:41)
      at TransformPluginContext.error (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49253:16)
      at normalizeUrl (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64307:23)
      at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
      at async file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64439:39
      at async Promise.all (index 17)
      at async TransformPluginContext.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64366:7)
      at async PluginContainer.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49099:18)
      at async loadAndTransform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:51978:27)
      at async viteTransformMiddleware (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:62106:24)
2:25:52 AM [vite] Internal server error: Failed to resolve import "@/lib/utils" from "src/features/memory/components/MemorySearch.tsx". Does the file exist?
  Plugin: vite:import-analysis
  File: /home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/src/features/memory/components/MemorySearch.tsx:7:31
  22 |  import { EmptyState } from "@/components/common/EmptyState";
  23 |  import { useMemorySearch, useDeleteMemory } from "../hooks/useMemory";
  24 |  import { formatDate, cn } from "@/lib/utils";
     |                                  ^
  25 |  export function MemorySearch() {
  26 |    _s();
      at TransformPluginContext._formatError (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49258:41)
      at TransformPluginContext.error (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49253:16)
      at normalizeUrl (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64307:23)
      at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
      at async file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64439:39
      at async Promise.all (index 9)
      at async TransformPluginContext.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64366:7)
      at async PluginContainer.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49099:18)
      at async loadAndTransform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:51978:27)
      at async viteTransformMiddleware (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:62106:24)
2:25:52 AM [vite] Internal server error: Failed to resolve import "@/lib/utils" from "src/features/memory/components/MemoryList.tsx". Does the file exist?
  Plugin: vite:import-analysis
  File: /home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/src/features/memory/components/MemoryList.tsx:7:31
  22 |  import { EmptyState } from "@/components/common/EmptyState";
  23 |  import { useMemories, useDeleteMemory } from "../hooks/useMemory";
  24 |  import { formatDate, cn } from "@/lib/utils";
     |                                  ^
  25 |  export function MemoryList() {
  26 |    _s();
      at TransformPluginContext._formatError (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49258:41)
      at TransformPluginContext.error (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49253:16)
      at normalizeUrl (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64307:23)
      at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
      at async file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64439:39
      at async Promise.all (index 9)
      at async TransformPluginContext.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64366:7)
      at async PluginContainer.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49099:18)
      at async loadAndTransform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:51978:27)
      at async viteTransformMiddleware (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:62106:24)
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/layout/Sidebar.tsx". Does the file exist?
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/Loading.tsx". Does the file exist?
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/Loading.tsx". Does the file exist? (x2)
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/chat/components/ContextSourcesModal.tsx". Does the file exist?
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/Loading.tsx". Does the file exist?
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/api" from "src/features/chat/components/MembersPanel.tsx". Does the file exist?
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/workspace/components/CreateRoomModal.tsx". Does the file exist?
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/EmptyState.tsx". Does the file exist?
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/EmptyState.tsx". Does the file exist? (x2)
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/EmptyState.tsx". Does the file exist? (x3)
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/chat/components/MessageInput.tsx". Does the file exist?
2:25:52 AM [vite] Internal server error: Failed to resolve import "@/lib/utils" from "src/features/project/components/ProjectManagement.tsx". Does the file exist?
  Plugin: vite:import-analysis
  File: /home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/src/features/project/components/ProjectManagement.tsx:16:19
  31 |  import { Loading } from "@/components/common/Loading";
  32 |  import { EmptyState } from "@/components/common/EmptyState";
  33 |  import { cn } from "@/lib/utils";
     |                      ^
  34 |  import { get, post, del } from "@/lib/api";
  35 |  export function ProjectManagement() {
      at TransformPluginContext._formatError (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49258:41)
      at TransformPluginContext.error (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49253:16)
      at normalizeUrl (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64307:23)
      at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
      at async file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64439:39
      at async Promise.all (index 8)
      at async TransformPluginContext.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64366:7)
      at async PluginContainer.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49099:18)
      at async loadAndTransform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:51978:27)
      at async viteTransformMiddleware (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:62106:24)
2:25:52 AM [vite] Internal server error: Failed to resolve import "@/lib/utils" from "src/features/auth/components/LoginForm.tsx". Does the file exist?
  Plugin: vite:import-analysis
  File: /home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/src/features/auth/components/LoginForm.tsx:7:19
  22 |  import { useAuthStore } from "../store/authStore";
  23 |  import { login, register } from "../api/authApi";
  24 |  import { cn } from "@/lib/utils";
     |                      ^
  25 |  export function LoginForm() {
  26 |    _s();
      at TransformPluginContext._formatError (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49258:41)
      at TransformPluginContext.error (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49253:16)
      at normalizeUrl (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64307:23)
      at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
      at async file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64439:39
      at async Promise.all (index 9)
      at async TransformPluginContext.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64366:7)
      at async PluginContainer.transform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49099:18)
      at async loadAndTransform (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:51978:27)
      at async viteTransformMiddleware (file:///home/hy.joo/2026/gitprojects/ai-memory-agent/frontend/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:62106:24)
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/Loading.tsx". Does the file exist?
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/features/chat/components/SlashCommandMenu.tsx". Does the file exist?
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/utils" from "src/components/common/EmptyState.tsx". Does the file exist?
2:25:52 AM [vite] Pre-transform error: Failed to resolve import "@/lib/api" from "src/features/auth/api/authApi.ts". Does the file exist?