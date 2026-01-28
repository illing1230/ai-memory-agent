import { cn } from '@/lib/utils'

export interface SlashCommand {
  command: string
  label: string
  description: string
  icon: string
}

interface SlashCommandMenuProps {
  commands: SlashCommand[]
  selectedIndex: number
  onSelect: (command: SlashCommand) => void
}

export function SlashCommandMenu({ commands, selectedIndex, onSelect }: SlashCommandMenuProps) {
  return (
    <div className="bg-background border border-border rounded-lg shadow-popup overflow-hidden animate-slide-up">
      <div className="px-3 py-2 border-b border-border">
        <span className="text-xs font-medium text-foreground-secondary">명령어</span>
      </div>
      <div className="max-h-[240px] overflow-y-auto py-1">
        {commands.map((cmd, index) => (
          <button
            key={cmd.command}
            onClick={() => onSelect(cmd)}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 text-left transition-colors duration-100',
              index === selectedIndex ? 'bg-accent-muted' : 'hover:bg-background-hover'
            )}
          >
            <span className="text-lg">{cmd.icon}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm text-foreground">/{cmd.command}</span>
                <span className="text-xs text-foreground-tertiary">{cmd.label}</span>
              </div>
              <p className="text-xs text-foreground-secondary truncate">{cmd.description}</p>
            </div>
          </button>
        ))}
      </div>
      <div className="px-3 py-1.5 border-t border-border bg-background-secondary">
        <span className="text-xs text-foreground-muted">
          <kbd className="px-1 py-0.5 rounded bg-background-tertiary">↑↓</kbd> 이동
          {' · '}
          <kbd className="px-1 py-0.5 rounded bg-background-tertiary">Enter</kbd> 선택
          {' · '}
          <kbd className="px-1 py-0.5 rounded bg-background-tertiary">Esc</kbd> 취소
        </span>
      </div>
    </div>
  )
}
