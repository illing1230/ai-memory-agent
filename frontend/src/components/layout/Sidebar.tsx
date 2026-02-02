import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  ChevronDown,
  ChevronRight,
  MessageSquare,
  Search,
  Plus,
  Settings,
  Brain,
  List,
  Briefcase,
  FileText,
  PanelLeftClose,
  PanelLeft,
  LogOut,
  Shield,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button, Tooltip, ScrollArea, Avatar } from '@/components/ui'
import { useUIStore } from '@/stores/uiStore'
import { useAuthStore } from '@/features/auth/store/authStore'
import { useChatRooms } from '@/features/chat/hooks/useChat'
import type { ChatRoom } from '@/types'

export function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { sidebarOpen, toggleSidebar, setCreateRoomModalOpen } = useUIStore()
  const { user, logout } = useAuthStore()
  const { data: chatRooms = [], isLoading } = useChatRooms()

  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    chatRooms: true,
    memory: true,
  })

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }))
  }

  const isActive = (path: string) => location.pathname === path
  const isActivePrefix = (path: string) => location.pathname.startsWith(path)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  if (!sidebarOpen) {
    return (
      <div className="flex flex-col items-center py-3 px-1 border-r border-border bg-background-secondary w-12">
        <Tooltip content="사이드바 열기" side="right">
          <Button variant="ghost" size="icon-sm" onClick={toggleSidebar}>
            <PanelLeft className="h-4 w-4" />
          </Button>
        </Tooltip>
        
        <div className="mt-4 space-y-1">
          <Tooltip content="채팅" side="right">
            <Button
              variant="ghost"
              size="icon"
              className={cn(isActivePrefix('/chat') && 'bg-background-active')}
              onClick={() => navigate('/chat')}
            >
              <MessageSquare className="h-4 w-4" />
            </Button>
          </Tooltip>
          
          <Tooltip content="메모리" side="right">
            <Button
              variant="ghost"
              size="icon"
              className={cn(isActivePrefix('/memory') && 'bg-background-active')}
              onClick={() => navigate('/memory/search')}
            >
              <Brain className="h-4 w-4" />
            </Button>
          </Tooltip>

          <Tooltip content="프로젝트" side="right">
            <Button
              variant="ghost"
              size="icon"
              className={cn(isActive('/projects') && 'bg-background-active')}
              onClick={() => navigate('/projects')}
            >
              <Briefcase className="h-4 w-4" />
            </Button>
          </Tooltip>

          <Tooltip content="문서 관리" side="right">
            <Button
              variant="ghost"
              size="icon"
              className={cn(isActive('/documents') && 'bg-background-active')}
              onClick={() => navigate('/documents')}
            >
              <FileText className="h-4 w-4" />
            </Button>
          </Tooltip>

          <Tooltip content="채팅방 관리" side="right">
            <Button
              variant="ghost"
              size="icon"
              className={cn(isActive('/chatrooms') && 'bg-background-active')}
              onClick={() => navigate('/chatrooms')}
            >
              <MessageSquare className="h-4 w-4" />
            </Button>
          </Tooltip>

          {user?.role === 'admin' && (
            <Tooltip content="관리자" side="right">
              <Button
                variant="ghost"
                size="icon"
                className={cn(isActive('/admin') && 'bg-background-active')}
                onClick={() => navigate('/admin')}
              >
                <Shield className="h-4 w-4" />
              </Button>
            </Tooltip>
          )}
        </div>

        <div className="mt-auto">
          <Tooltip content="로그아웃" side="right">
            <Button variant="ghost" size="icon" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </Tooltip>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full w-sidebar border-r border-border bg-background-secondary">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <Button
          variant="ghost"
          className="flex items-center gap-2 px-2 h-auto hover:bg-background-hover"
          onClick={() => navigate('/chat')}
        >
          <div className="flex items-center justify-center w-6 h-6 rounded bg-accent text-white">
            <Brain className="h-3.5 w-3.5" />
          </div>
          <span className="font-semibold text-sm">Memory Agent</span>
        </Button>
        <Tooltip content="사이드바 접기" side="bottom">
          <Button variant="ghost" size="icon-sm" onClick={toggleSidebar}>
            <PanelLeftClose className="h-4 w-4" />
          </Button>
        </Tooltip>
      </div>

      {/* Quick Search */}
      <div className="px-2 py-2">
        <Button
          variant="ghost"
          className="w-full justify-start gap-2 text-foreground-secondary h-8"
          onClick={() => navigate('/memory/search')}
        >
          <Search className="h-4 w-4" />
          <span className="text-sm">메모리 검색...</span>
          <kbd className="ml-auto text-xs bg-background-tertiary px-1.5 py-0.5 rounded">⌘K</kbd>
        </Button>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 px-2">
        <nav className="space-y-1 py-2">
          {/* Chat Rooms Section */}
          <SidebarSection
            title="채팅방"
            icon={MessageSquare}
            expanded={expandedSections.chatRooms}
            onToggle={() => toggleSection('chatRooms')}
            action={
              <Button
                variant="ghost"
                size="icon-sm"
                className="opacity-0 group-hover:opacity-100"
                onClick={(e) => {
                  e.stopPropagation()
                  setCreateRoomModalOpen(true)
                }}
              >
                <Plus className="h-3.5 w-3.5" />
              </Button>
            }
          >
            {isLoading ? (
              <div className="px-2 py-1 text-xs text-foreground-muted">로딩 중...</div>
            ) : chatRooms.length === 0 ? (
              <div className="px-2 py-1 text-xs text-foreground-muted">채팅방이 없습니다</div>
            ) : (
              chatRooms.map((room: ChatRoom) => (
                <SidebarItem
                  key={room.id}
                  to={`/chat/${room.id}`}
                  icon={MessageSquare}
                  label={room.name}
                  active={location.pathname === `/chat/${room.id}`}
                />
              ))
            )}
          </SidebarSection>

          {/* Memory Section */}
          <SidebarSection
            title="메모리"
            icon={Brain}
            expanded={expandedSections.memory}
            onToggle={() => toggleSection('memory')}
          >
            <SidebarItem
              to="/memory/search"
              icon={Search}
              label="검색"
              active={isActive('/memory/search')}
            />
            <SidebarItem
              to="/memory/list"
              icon={List}
              label="목록"
              active={isActive('/memory/list')}
            />
          </SidebarSection>

          {/* Projects - 단일 항목 */}
          <SidebarItem
            to="/projects"
            icon={Briefcase}
            label="프로젝트 관리"
            active={isActive('/projects')}
          />

          {/* Documents - 단일 항목 */}
          <SidebarItem
            to="/documents"
            icon={FileText}
            label="문서 관리"
            active={isActive('/documents')}
          />

          {/* Chat Room Management - 단일 항목 */}
          <SidebarItem
            to="/chatrooms"
            icon={MessageSquare}
            label="채팅방 관리"
            active={isActive('/chatrooms')}
          />

          {/* Admin - admin role만 표시 */}
          {user?.role === 'admin' && (
            <SidebarItem
              to="/admin"
              icon={Shield}
              label="관리자"
              active={isActive('/admin')}
            />
          )}
        </nav>
      </ScrollArea>

      {/* User & Footer */}
      <div className="border-t border-border p-2 space-y-1">
        {/* User Info */}
        {user && (
          <div className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-background-hover">
            <Avatar alt={user.name} fallback={user.name.charAt(0)} size="sm" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user.name}</p>
              <p className="text-xs text-foreground-muted truncate">{user.email}</p>
            </div>
          </div>
        )}

        {/* Settings & Logout */}
        <div className="flex gap-1">
          <Button
            variant="ghost"
            className="flex-1 justify-start gap-2 text-foreground-secondary"
            onClick={() => useUIStore.getState().setSettingsModalOpen(true)}
          >
            <Settings className="h-4 w-4" />
            <span className="text-sm">설정</span>
          </Button>
          <Tooltip content="로그아웃" side="top">
            <Button variant="ghost" size="icon" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </Tooltip>
        </div>
      </div>
    </div>
  )
}

interface SidebarSectionProps {
  title: string
  icon: React.ElementType
  expanded: boolean
  onToggle: () => void
  action?: React.ReactNode
  children: React.ReactNode
}

function SidebarSection({ title, icon: Icon, expanded, onToggle, action, children }: SidebarSectionProps) {
  return (
    <div className="group">
      <button
        onClick={onToggle}
        className="flex items-center gap-1 w-full px-2 py-1 text-sm text-foreground-secondary hover:bg-background-hover rounded-md transition-colors"
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <Icon className="h-3.5 w-3.5 mr-1" />
        <span className="flex-1 text-left font-medium">{title}</span>
        {action}
      </button>
      {expanded && <div className="ml-4 mt-1 space-y-0.5">{children}</div>}
    </div>
  )
}

interface SidebarItemProps {
  to: string
  icon: React.ElementType
  label: string
  active?: boolean
}

function SidebarItem({ to, icon: Icon, label, active }: SidebarItemProps) {
  return (
    <Link to={to} className={cn('sidebar-item', active && 'active')}>
      <Icon className="h-4 w-4 shrink-0" />
      <span className="truncate">{label}</span>
    </Link>
  )
}
