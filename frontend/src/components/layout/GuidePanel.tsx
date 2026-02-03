import { X, ChevronRight, MessageSquare, Brain, Shield, Bot } from 'lucide-react'
import { Button, ScrollArea } from '@/components/ui'

interface GuideCategory {
  id: string
  title: string
  icon: React.ElementType
  items: GuideItem[]
}

interface GuideItem {
  title: string
  description: string
  url: string
}

const guideCategories: GuideCategory[] = [
  {
    id: 'sdk',
    title: 'SDK 연동 가이드',
    icon: Bot,
    items: [
      {
        title: 'Agent Instance 생성',
        description: 'SDK를 사용하여 Agent Instance를 생성하는 방법',
        url: '/docs/agent-integration-guide.html#agent-instance-생성',
      },
      {
        title: 'API Key 관리',
        description: 'API Key를 생성하고 관리하는 방법',
        url: '/docs/agent-integration-guide.html#api-key-관리',
      },
      {
        title: '메모리 저장',
        description: 'SDK를 사용하여 메모리를 저장하는 방법',
        url: '/docs/agent-integration-guide.html#메모리-저장',
      },
      {
        title: '메모리 검색',
        description: 'SDK를 사용하여 메모리를 검색하는 방법',
        url: '/docs/agent-integration-guide.html#메모리-검색',
      },
    ],
  },
  {
    id: 'chat',
    title: '대화방',
    icon: MessageSquare,
    items: [
      {
        title: '대화방 생성',
        description: '새로운 대화방을 만드는 방법',
        url: '/docs/agent-integration-guide.html#대화방-생성',
      },
      {
        title: '메모리 소스 설정',
        description: '대화방에서 사용할 메모리 소스를 설정하는 방법',
        url: '/docs/agent-integration-guide.html#메모리-소스-설정',
      },
      {
        title: '대화방 공유',
        description: '대화방을 다른 사용자와 공유하는 방법',
        url: '/docs/agent-integration-guide.html#대화방-공유',
      },
    ],
  },
  {
    id: 'memory',
    title: '지식 센터',
    icon: Brain,
    items: [
      {
        title: '메모리 검색',
        description: '저장된 메모리를 검색하는 방법',
        url: '/docs/agent-integration-guide.html#메모리-검색',
      },
      {
        title: '메모리 관리',
        description: '메모리를 조회하고 삭제하는 방법',
        url: '/docs/agent-integration-guide.html#메모리-관리',
      },
      {
        title: '문서 업로드',
        description: 'PDF, TXT 파일을 업로드하는 방법',
        url: '/docs/agent-integration-guide.html#문서-업로드',
      },
      {
        title: '문서 미리보기',
        description: '업로드된 문서를 미리보는 방법',
        url: '/docs/agent-integration-guide.html#문서-미리보기',
      },
    ],
  },
  {
    id: 'permission',
    title: '권한 관리',
    icon: Shield,
    items: [
      {
        title: '지식 권한',
        description: '메모리의 접근 권한을 관리하는 방법',
        url: '/docs/agent-integration-guide.html#지식-권한',
      },
      {
        title: '프로젝트',
        description: '프로젝트를 생성하고 관리하는 방법',
        url: '/docs/agent-integration-guide.html#프로젝트',
      },
      {
        title: '공유 설정',
        description: '메모리와 문서를 공유하는 방법',
        url: '/docs/agent-integration-guide.html#공유-설정',
      },
    ],
  },
]

interface GuidePanelProps {
  isOpen: boolean
  onClose: () => void
}

export function GuidePanel({ isOpen, onClose }: GuidePanelProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-y-0 right-0 w-[700px] bg-background border-l border-border shadow-xl flex flex-col z-50">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-accent" />
          <h2 className="font-semibold">사용 가이드</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-5 w-5" />
        </Button>
      </div>

      {/* 가이드 내용 */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-6">
          {guideCategories.map((category) => {
            const Icon = category.icon
            return (
              <div key={category.id}>
                <div className="flex items-center gap-2 mb-3">
                  <Icon className="h-5 w-5 text-accent" />
                  <h3 className="font-semibold text-base">{category.title}</h3>
                </div>
                <div className="space-y-2 ml-7">
                  {category.items.map((item, index) => (
                    <a
                      key={index}
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block p-3 rounded-lg border border-border hover:bg-background-hover transition-colors group"
                    >
                      <div className="flex items-start gap-2">
                        <ChevronRight className="h-4 w-4 text-accent mt-0.5 shrink-0 group-hover:translate-x-1 transition-transform" />
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium mb-1 group-hover:text-accent transition-colors">
                            {item.title}
                          </h4>
                          <p className="text-xs text-foreground-muted leading-relaxed">
                            {item.description}
                          </p>
                        </div>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </ScrollArea>

      {/* 푸터 */}
      <div className="border-t border-border px-4 py-3 bg-background-secondary">
        <p className="text-xs text-foreground-muted text-center">
          자세한 내용은{' '}
          <a
            href="/docs/agent-integration-guide.html"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            전체 가이드 문서
          </a>
          를 확인하세요
        </p>
      </div>
    </div>
  )
}
