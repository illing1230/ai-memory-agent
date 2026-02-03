import { useState } from 'react'
import { X, ChevronRight, MessageSquare, Brain, Shield, Bot, ChevronDown } from 'lucide-react'
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
  content: React.ReactNode
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
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>AI Memory Agent 웹 대시보드 접속</strong>
              <p>브라우저에서 AI Memory Agent 대시보드에 접속합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>Agent Marketplace 이동</strong>
              <p>사이드바에서 "Agent" → "Marketplace"를 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>Agent Instance 생성</strong>
              <p>원하는 Agent Type을 선택하고 "Instance 생성" 버튼을 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">4</span>
              <strong>API Key 확인</strong>
              <p>생성된 Agent Instance의 API Key를 복사합니다. 이 API Key는 SDK 연동에 필요합니다.</p>
            </div>
          </div>
        ),
      },
      {
        title: 'API Key 관리',
        description: 'API Key를 생성하고 관리하는 방법',
        content: (
          <div className="space-y-4">
            <p>API Key는 Agent Instance를 생성할 때 자동으로 생성됩니다.</p>
            <div className="warning-box">
              <strong>⚠️ 중요:</strong> API Key는 안전하게 보관하세요. 유출 시 타인이 귀하의 Agent Instance에 접근할 수 있습니다.
            </div>
          </div>
        ),
      },
      {
        title: '메모리 저장',
        description: 'SDK를 사용하여 메모리를 저장하는 방법',
        content: (
          <div className="space-y-4">
            <pre><code>{`from ai_memory_agent_sdk import AIMemoryAgentSyncClient

client = AIMemoryAgentSyncClient(
    api_key="your_api_key",
    base_url="http://localhost:8000",
    agent_id="your_agent_id"
)

result = client.send_memory(
    content="사용자가 커피를 좋아합니다",
    metadata={
        "source": "chatbot",
        "category": "preference"
    }
)`}</code></pre>
          </div>
        ),
      },
      {
        title: '메모리 검색',
        description: 'SDK를 사용하여 메모리를 검색하는 방법',
        content: (
          <div className="space-y-4">
            <p>SDK를 통한 메모리 검색 기능은 현재 개발 중입니다. 웹 대시보드의 "지식 센터" → "검색"을 이용해주세요.</p>
          </div>
        ),
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
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>새 대화방 만들기</strong>
              <p>사이드바의 "대화방" 섹션에서 "+" 버튼을 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>대화방 정보 입력</strong>
              <p>대화방 이름과 유형(개인/프로젝트/부서)을 선택합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>대화방 생성</strong>
              <p>"생성" 버튼을 클릭하여 대화방을 만듭니다.</p>
            </div>
          </div>
        ),
      },
      {
        title: '메모리 소스 설정',
        description: '대화방에서 사용할 메모리 소스를 설정하는 방법',
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>메모리 소스 버튼 클릭</strong>
              <p>대화방 헤더의 "📦 메모리 소스" 텍스트를 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>메모리 소스 선택</strong>
              <p>다음 메모리 소스 중에서 선택할 수 있습니다:</p>
              <ul>
                <li><strong>이 대화방:</strong> 현재 대화방의 메모리 사용</li>
                <li><strong>다른 대화방:</strong> 다른 대화방의 메모리 사용</li>
                <li><strong>개인 전체:</strong> 개인 모든 메모리 사용 (⚠️ 주의 필요)</li>
                <li><strong>프로젝트:</strong> 특정 프로젝트의 메모리 사용</li>
                <li><strong>부서:</strong> 특정 부서의 메모리 사용</li>
              </ul>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>설정 저장</strong>
              <p>"저장" 버튼을 클릭하여 설정을 적용합니다.</p>
            </div>
            <div className="tip-box">
              <strong>💡 팁:</strong> 메모리 소스를 적절히 설정하면 AI가 관련성 높은 정보를 더 빠르게 찾을 수 있습니다.
            </div>
          </div>
        ),
      },
      {
        title: '대화방 공유',
        description: '대화방을 다른 사용자와 공유하는 방법',
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>공유 버튼 클릭</strong>
              <p>대화방 헤더의 공유 버튼을 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>공유 대상 선택</strong>
              <p>공유할 사용자 또는 그룹을 선택합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>권한 설정</strong>
              <p>공유 대상의 권한을 설정합니다:</p>
              <ul>
                <li><strong>멤버:</strong> 메시지 전송 및 메모리 저장 가능</li>
                <li><strong>조회자:</strong> 메모리만 조회 가능</li>
              </ul>
            </div>
            <div className="step">
              <span className="step-number">4</span>
              <strong>공유 완료</strong>
              <p>"공유" 버튼을 클릭하여 공유를 완료합니다.</p>
            </div>
          </div>
        ),
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
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>검색 페이지 이동</strong>
              <p>사이드바에서 "지식 센터" → "검색"을 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>검색어 입력</strong>
              <p>검색창에 찾고자 하는 키워드를 입력합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>필터 적용</strong>
              <p>필요한 경우 다음 필터를 적용할 수 있습니다:</p>
              <ul>
                <li><strong>데이터 타입:</strong> 메모리, 메시지, 로그</li>
                <li><strong>범위:</strong> 개인, 프로젝트, 부서, 대화방</li>
                <li><strong>기간:</strong> 특정 기간 내의 메모리</li>
              </ul>
            </div>
            <div className="step">
              <span className="step-number">4</span>
              <strong>검색 결과 확인</strong>
              <p>검색 결과를 확인하고 필요한 메모리를 클릭하여 상세 내용을 봅니다.</p>
            </div>
            <div className="tip-box">
              <strong>💡 팁:</strong> 시맨틱 검색을 지원하므로 정확한 키워드가 아니어도 관련 내용을 찾을 수 있습니다.
            </div>
          </div>
        ),
      },
      {
        title: '메모리 관리',
        description: '메모리를 조회하고 삭제하는 방법',
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>지식 목록 페이지 이동</strong>
              <p>사이드바에서 "지식 센터" → "지식 목록"을 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>메모리 목록 확인</strong>
              <p>저장된 모든 메모리 목록을 확인합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>메모리 삭제</strong>
              <p>삭제할 메모리의 휴지통 아이콘을 클릭합니다.</p>
            </div>
            <div className="warning-box">
              <strong>⚠️ 주의:</strong> 삭제된 메모리는 복구할 수 없습니다. 신중하게 삭제하세요.
            </div>
          </div>
        ),
      },
      {
        title: '문서 업로드',
        description: 'PDF, TXT 파일을 업로드하는 방법',
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>문서 업로드 페이지 이동</strong>
              <p>사이드바에서 "지식 센터" → "문서 업로드"를 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>파일 선택</strong>
              <p>"파일 선택" 버튼을 클릭하여 업로드할 파일을 선택합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>파일 업로드</strong>
              <p>"업로드" 버튼을 클릭하여 파일을 업로드합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">4</span>
              <strong>처리 완료 확인</strong>
              <p>파일이 청크로 분할되고 벡터화됩니다. 처리가 완료되면 "완료" 상태로 표시됩니다.</p>
            </div>
            <div className="feature-box">
              <strong>지원 파일 형식:</strong>
              <ul>
                <li>PDF (.pdf)</li>
                <li>텍스트 파일 (.txt)</li>
                <li>최대 파일 크기: 50MB</li>
              </ul>
            </div>
          </div>
        ),
      },
      {
        title: '문서 미리보기',
        description: '업로드된 문서를 미리보는 방법',
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>문서 목록 확인</strong>
              <p>문서 업로드 페이지에서 업로드된 문서 목록을 확인합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>문서 클릭</strong>
              <p>미리보기할 문서를 클릭하거나 눈(Eye) 아이콘을 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>문서 내용 확인</strong>
              <p>우측 패널에서 문서 내용을 청크별로 확인할 수 있습니다.</p>
            </div>
            <div className="step">
              <span className="step-number">4</span>
              <strong>패널 닫기</strong>
              <p>X 버튼을 클릭하여 미리보기 패널을 닫습니다.</p>
            </div>
          </div>
        ),
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
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>지식 권한 페이지 이동</strong>
              <p>사이드바에서 "권한 관리" → "지식 권한"을 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>메모리 선택</strong>
              <p>권한을 설정할 메모리를 선택합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>권한 설정</strong>
              <p>다음 권한을 설정할 수 있습니다:</p>
              <ul>
                <li><strong>읽기:</strong> 메모리 조회 권한</li>
                <li><strong>쓰기:</strong> 메모리 수정 권한</li>
                <li><strong>삭제:</strong> 메모리 삭제 권한</li>
              </ul>
            </div>
            <div className="step">
              <span className="step-number">4</span>
              <strong>접근 대상 설정</strong>
              <p>권한을 부여할 사용자 또는 그룹을 선택합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">5</span>
              <strong>권한 저장</strong>
              <p>"저장" 버튼을 클릭하여 권한 설정을 적용합니다.</p>
            </div>
          </div>
        ),
      },
      {
        title: '프로젝트',
        description: '프로젝트를 생성하고 관리하는 방법',
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>프로젝트 페이지 이동</strong>
              <p>사이드바에서 "권한 관리" → "프로젝트"를 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>프로젝트 생성</strong>
              <p>"새 프로젝트" 버튼을 클릭하고 프로젝트 정보를 입력합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>팀원 초대</strong>
              <p>프로젝트에 참여할 팀원을 초대합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">4</span>
              <strong>역할 할당</strong>
              <p>팀원에게 적절한 역할을 할당합니다:</p>
              <ul>
                <li><strong>관리자:</strong> 모든 권한</li>
                <li><strong>멤버:</strong> 메모리 읽기/쓰기</li>
                <li><strong>조회자:</strong> 메모리 읽기만</li>
              </ul>
            </div>
          </div>
        ),
      },
      {
        title: '공유 설정',
        description: '메모리와 문서를 공유하는 방법',
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>공유할 항목 선택</strong>
              <p>공유할 메모리 또는 문서를 선택합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>공유 버튼 클릭</strong>
              <p>공유 버튼(Share2 아이콘)을 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>공유 대상 선택</strong>
              <p>공유할 사용자 또는 그룹을 선택합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">4</span>
              <strong>권한 설정</strong>
              <p>공유 대상의 권한을 설정합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">5</span>
              <strong>공유 완료</strong>
              <p>"공유" 버튼을 클릭하여 공유를 완료합니다.</p>
            </div>
            <div className="tip-box">
              <strong>💡 팁:</strong> 공유된 항목은 "지식 권한" 페이지에서 관리할 수 있습니다.
            </div>
          </div>
        ),
      },
    ],
  },
]

interface GuidePanelProps {
  isOpen: boolean
  onClose: () => void
}

export function GuidePanel({ isOpen, onClose }: GuidePanelProps) {
  const [selectedItem, setSelectedItem] = useState<GuideItem | null>(null)
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
    sdk: true,
    chat: false,
    memory: false,
    permission: false,
  })

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories((prev) => ({ ...prev, [categoryId]: !prev[categoryId] }))
  }

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
        <div className="p-4">
          {selectedItem ? (
            <div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedItem(null)}
                className="mb-4"
              >
                ← 목록으로 돌아가기
              </Button>
              <h3 className="text-lg font-semibold mb-2">{selectedItem.title}</h3>
              <p className="text-sm text-foreground-muted mb-4">{selectedItem.description}</p>
              <div className="space-y-4">{selectedItem.content}</div>
            </div>
          ) : (
            <div className="space-y-6">
              {guideCategories.map((category) => {
                const Icon = category.icon
                return (
                  <div key={category.id}>
                    <button
                      onClick={() => toggleCategory(category.id)}
                      className="flex items-center gap-2 w-full mb-3"
                    >
                      {expandedCategories[category.id] ? (
                        <ChevronDown className="h-4 w-4 text-accent" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-accent" />
                      )}
                      <Icon className="h-5 w-5 text-accent" />
                      <h3 className="font-semibold text-base">{category.title}</h3>
                    </button>
                    {expandedCategories[category.id] && (
                      <div className="space-y-2 ml-7">
                        {category.items.map((item, index) => (
                          <button
                            key={index}
                            onClick={() => setSelectedItem(item)}
                            className="w-full text-left p-3 rounded-lg border border-border hover:bg-background-hover transition-colors group"
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
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
