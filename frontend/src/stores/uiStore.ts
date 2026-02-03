import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIState {
  sidebarOpen: boolean
  sidebarWidth: number
  theme: 'light' | 'dark' | 'system'
  createRoomModalOpen: boolean
  settingsModalOpen: boolean
  guidePanelOpen: boolean
  
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setSidebarWidth: (width: number) => void
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  setCreateRoomModalOpen: (open: boolean) => void
  setSettingsModalOpen: (open: boolean) => void
  setGuidePanelOpen: (open: boolean) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      sidebarWidth: 240,
      theme: 'light',
      createRoomModalOpen: false,
      settingsModalOpen: false,
      guidePanelOpen: false,
      
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
      setSidebarWidth: (sidebarWidth) => set({ sidebarWidth }),
      setTheme: (theme) => {
        const root = document.documentElement
        if (theme === 'dark') {
          root.classList.add('dark')
        } else if (theme === 'light') {
          root.classList.remove('dark')
        } else {
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
          if (prefersDark) {
            root.classList.add('dark')
          } else {
            root.classList.remove('dark')
          }
        }
        set({ theme })
      },
      setCreateRoomModalOpen: (createRoomModalOpen) => set({ createRoomModalOpen }),
      setSettingsModalOpen: (settingsModalOpen) => set({ settingsModalOpen }),
      setGuidePanelOpen: (guidePanelOpen) => set({ guidePanelOpen }),
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        sidebarWidth: state.sidebarWidth,
        theme: state.theme,
      }),
    }
  )
)
