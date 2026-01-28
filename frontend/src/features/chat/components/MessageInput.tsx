import { useState, useRef, useEffect, KeyboardEvent, useCallback } from 'react'
import { Send, Paperclip, AtSign } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui'
import { SlashCommandMenu, type SlashCommand } from './SlashCommandMenu'

interface MessageInputProps {
  onSend: (content: string) => void
  disabled?: boolean
  placeholder?: string
  onTyping?: () => void
}

const SLASH_COMMANDS: SlashCommand[] = [
  { command: 'remember', label: '메모리 저장', description: '이 채팅방에 메모리 저장', icon: '📝' },
  { command: 'search', label: '메모리 검색', description: '저장된 메모리에서 검색', icon: '🔍' },
  { command: 'forget', label: '메모리 삭제', description: '메모리 삭제', icon: '🗑️' },
  { command: 'members', label: '멤버 목록', description: '채팅방 멤버 보기', icon: '👥' },
  { command: 'invite', label: '멤버 초대', description: '새 멤버 초대', icon: '➕' },
  { command: 'help', label: '도움말', description: '사용 가능한 명령어 보기', icon: '❓' },
]

export function MessageInput({ 
  onSend, 
  disabled = false, 
  placeholder = '메시지 입력... / 로 명령어',
  onTyping,
}: MessageInputProps) {
  const [value, setValue] = useState('')
  const [showSlashMenu, setShowSlashMenu] = useState(false)
  const [slashFilter, setSlashFilter] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const filteredCommands = SLASH_COMMANDS.filter((cmd) =>
    cmd.command.toLowerCase().includes(slashFilter.toLowerCase()) ||
    cmd.label.toLowerCase().includes(slashFilter.toLowerCase())
  )

  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`
    }
  }, [value])

  useEffect(() => {
    if (value.startsWith('/')) {
      const afterSlash = value.slice(1).split(' ')[0]
      if (!value.includes(' ')) {
        setSlashFilter(afterSlash)
        setShowSlashMenu(true)
        setSelectedIndex(0)
      } else {
        setShowSlashMenu(false)
      }
    } else {
      setShowSlashMenu(false)
      setSlashFilter('')
    }
  }, [value])

  // 타이핑 이벤트 디바운스
  const handleTyping = useCallback(() => {
    if (!onTyping) return
    
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current)
    }
    
    onTyping()
    
    typingTimeoutRef.current = setTimeout(() => {
      // 타이핑 종료 (3초 후)
    }, 3000)
  }, [onTyping])

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    setShowSlashMenu(false)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (showSlashMenu) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev < filteredCommands.length - 1 ? prev + 1 : 0))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : filteredCommands.length - 1))
      } else if (e.key === 'Enter' && filteredCommands.length > 0) {
        e.preventDefault()
        handleSelectCommand(filteredCommands[selectedIndex])
      } else if (e.key === 'Escape') {
        setShowSlashMenu(false)
      }
    } else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSelectCommand = (cmd: SlashCommand) => {
    setValue(`/${cmd.command} `)
    setShowSlashMenu(false)
    textareaRef.current?.focus()
  }

  const insertMention = () => {
    const pos = textareaRef.current?.selectionStart || value.length
    const newValue = value.slice(0, pos) + '@ai ' + value.slice(pos)
    setValue(newValue)
    textareaRef.current?.focus()
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value)
    handleTyping()
  }

  return (
    <div className="relative border-t border-border bg-background p-3">
      {showSlashMenu && filteredCommands.length > 0 && (
        <div className="absolute bottom-full left-3 right-3 mb-2">
          <SlashCommandMenu
            commands={filteredCommands}
            selectedIndex={selectedIndex}
            onSelect={handleSelectCommand}
          />
        </div>
      )}

      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className={cn(
              'w-full resize-none rounded-lg border border-border bg-background-secondary',
              'px-3 py-2 pr-20 text-sm',
              'placeholder:text-foreground-muted',
              'focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-all duration-150'
            )}
          />
          
          <div className="absolute right-2 bottom-1.5 flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-foreground-muted hover:text-foreground"
              onClick={insertMention}
              disabled={disabled}
              title="AI 멘션 (@ai)"
            >
              <AtSign className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-foreground-muted hover:text-foreground"
              disabled={disabled}
              title="파일 첨부"
            >
              <Paperclip className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <Button onClick={handleSend} disabled={disabled || !value.trim()} size="icon" className="shrink-0">
          <Send className="h-4 w-4" />
        </Button>
      </div>

      <div className="mt-1.5 flex items-center gap-3 text-xs text-foreground-muted">
        <span><kbd className="px-1 py-0.5 rounded bg-background-tertiary">Enter</kbd> 전송</span>
        <span><kbd className="px-1 py-0.5 rounded bg-background-tertiary">Shift+Enter</kbd> 줄바꿈</span>
        <span><kbd className="px-1 py-0.5 rounded bg-background-tertiary">/</kbd> 명령어</span>
      </div>
    </div>
  )
}
