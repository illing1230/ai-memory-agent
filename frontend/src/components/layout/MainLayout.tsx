import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { useUIStore } from '@/stores/uiStore'
import { CreateRoomModal } from '@/features/workspace/components/CreateRoomModal'
import { cn } from '@/lib/utils'

export function MainLayout() {
  const { sidebarOpen, createRoomModalOpen, setCreateRoomModalOpen } = useUIStore()

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      <Sidebar />
      <main className={cn('flex-1 flex flex-col overflow-hidden', 'transition-all duration-200')}>
        <Outlet />
      </main>
      <CreateRoomModal open={createRoomModalOpen} onClose={() => setCreateRoomModalOpen(false)} />
    </div>
  )
}
