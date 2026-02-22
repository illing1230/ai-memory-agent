import { useState, useEffect } from 'react'
import { X, ChevronRight, MessageSquare, Brain, Shield, Bot, ChevronDown, ArrowLeft, FileText } from 'lucide-react'
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
    title: 'Agent 연동 가이드',
    icon: Bot,
    items: [
      {
        title: 'Agent Type 등록',
        description: '나만의 Agent Type을 등록하는 방법',
        content: (
          <div className="space-y-4">
            <p>Agent를 사용하려면 먼저 Agent Type을 등록해야 합니다.</p>
            <div className="step">
              <span className="step-number">1</span>
              <strong>Agent 등록 페이지 이동</strong>
              <p>사이드바에서 "Agent" → "Agent 등록"을 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>"Agent 등록" 버튼 클릭</strong>
              <p>상단의 "Agent 등록" 버튼을 클릭하면 등록 모달이 열립니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>Agent 정보 입력</strong>
              <p>다음 항목을 입력합니다:</p>
              <ul>
                <li><strong>이름</strong> (필수): Agent 이름</li>
                <li><strong>설명</strong>: Agent 용도 설명</li>
                <li><strong>버전</strong>: 기본값 1.0.0</li>
                <li><strong>기능</strong>: 쉼표로 구분 (예: memory, message, log)</li>
                <li><strong>공개 범위</strong>: private / project / department / public</li>
              </ul>
            </div>
            <div className="step">
              <span className="step-number">4</span>
              <strong>등록 완료</strong>
              <p>등록된 Agent Type은 Marketplace에 표시되며, 공개 범위에 따라 다른 사용자도 사용할 수 있습니다.</p>
            </div>
          </div>
        ),
      },
      {
        title: 'Agent Instance 생성',
        description: '등록된 Agent Type으로 Instance를 생성하는 방법',
        content: (
          <div className="space-y-4">
            <p>Agent Type을 등록한 후, Instance를 생성하여 API Key를 발급받습니다.</p>
            <div className="step">
              <span className="step-number">1</span>
              <strong>Agent Marketplace 이동</strong>
              <p>사이드바에서 "Agent" → "Marketplace"를 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>Agent Instance 생성</strong>
              <p>원하는 Agent Type을 선택하고 "Instance 생성" 버튼을 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>Instance 이름 입력</strong>
              <p>Instance 이름을 입력하고 생성합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">4</span>
              <strong>API Key 확인</strong>
              <p>"내 Agent Instances" 탭에서 생성된 Instance의 API Key를 복사합니다. 이 API Key는 SDK 연동에 필요합니다.</p>
            </div>
            <div className="warning-box">
              <strong>⚠️ 중요:</strong> API Key는 안전하게 보관하세요. 유출 시 타인이 귀하의 Agent Instance에 접근할 수 있습니다.
            </div>
          </div>
        ),
      },
      {
        title: 'SDK 설치',
        description: 'pip로 AI Memory Agent SDK를 설치하는 방법',
        content: (
          <div className="space-y-4">
            <p>Agent API 또는 Client API를 사용하려면 SDK를 설치해야 합니다.</p>
            <h4 className="font-semibold text-sm">pip 설치</h4>
            <pre><code>{`pip install ai-memory-agent-sdk`}</code></pre>
            <h4 className="font-semibold text-sm">소스 코드에서 설치 (개발 모드)</h4>
            <pre><code>{`cd ai-memory-agent
pip install -e ai_memory_agent_sdk`}</code></pre>
            <h4 className="font-semibold text-sm">환경 변수 설정</h4>
            <pre><code>{`# .env
AI_MEMORY_AGENT_API_KEY=your_api_key
AI_MEMORY_AGENT_URL=http://localhost:8000`}</code></pre>
          </div>
        ),
      },
      {
        title: 'Agent 클래스 (Agent API)',
        description: 'LLM 호출 + 메모리 통합을 한 번에 처리하는 Agent 클래스',
        content: (
          <div className="space-y-4">
            <p>Agent 클래스는 LLM 호출, 대화 관리, 메모리 저장/검색을 통합한 Agent API입니다.</p>
            <pre><code>{`from ai_memory_agent_sdk import Agent

agent = Agent(
    api_key="your_api_key",
    base_url="http://localhost:8000",
    agent_id="your_agent_id",
    llm_provider="openai",  # openai / anthropic / ollama
    llm_url="http://localhost:8080/v1",
    llm_api_key="your_llm_key",
    model="your-model-name",
)

# 대화 (자동으로 메시지 저장 + 메모리 검색)
response = agent.message("안녕하세요!")

# 수동 메모리 추출
agent.memory()

# 메모리 검색
results = agent.search("커피 선호도")

# 대화 초기화
agent.clear()`}</code></pre>
          </div>
        ),
      },
      {
        title: '메모리 저장 (Client API)',
        description: 'Client를 사용하여 메모리를 직접 저장하는 방법',
        content: (
          <div className="space-y-4">
            <p>Client API를 사용하면 메모리, 메시지, 로그를 직접 저장할 수 있습니다.</p>
            <pre><code>{`from ai_memory_agent_sdk import AIMemoryAgentSyncClient

client = AIMemoryAgentSyncClient(
    api_key="your_api_key",
    base_url="http://localhost:8000",
    agent_id="your_agent_id"
)

# 메모리 저장
client.send_memory(
    content="사용자가 커피를 좋아합니다",
    metadata={"category": "preference"}
)

# 메시지 저장
client.send_message(content="안녕하세요!")

# 로그 저장
client.send_log(content="작업 완료")`}</code></pre>
          </div>
        ),
      },
      {
        title: '메모리 검색',
        description: 'SDK를 사용하여 메모리를 검색하는 방법',
        content: (
          <div className="space-y-4">
            <p>시맨틱 검색으로 관련 메모리를 찾을 수 있습니다.</p>
            <pre><code>{`from ai_memory_agent_sdk import AIMemoryAgentSyncClient

client = AIMemoryAgentSyncClient(
    api_key="your_api_key",
    base_url="http://localhost:8000",
    agent_id="your_agent_id"
)

# 메모리 검색
results = client.search_memories(
    query="커피 선호도",
    context_sources={
        "chat_rooms": ["room_id_1"]
    },
    limit=10
)

for r in results["results"]:
    print(f"[{r['score']:.3f}] {r['content']}")`}</code></pre>
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
        title: '@ai로 AI에게 질문하기',
        description: '대화방에서 AI에게 질문하는 방법',
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>@ai 입력</strong>
              <p>메시지 입력창에 <code>@ai</code>를 입력한 후 질문을 작성합니다.</p>
              <p className="text-xs text-foreground-muted mt-1">예: <code>@ai 이 프로젝트의 배포 절차를 알려줘</code></p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>AI 응답 확인</strong>
              <p>AI가 다음 정보를 참고하여 답변합니다:</p>
              <ul>
                <li><strong>최근 대화 내용</strong> (최우선)</li>
                <li><strong>연결된 RAG 문서</strong> (높은 우선순위)</li>
                <li><strong>설정된 메모리 소스</strong> (보조)</li>
              </ul>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>자동 메모리 추출</strong>
              <p>AI 응답 후, 대화에서 중요한 정보가 자동으로 메모리로 추출/저장됩니다.</p>
            </div>
            <div className="tip-box">
              <strong>💡 팁:</strong> 문서를 대화방에 연결하면 AI가 문서 내용을 참고하여 더 정확한 답변을 제공합니다.
            </div>
          </div>
        ),
      },
      {
        title: '슬래시 커맨드',
        description: '대화방에서 사용할 수 있는 슬래시 커맨드 목록',
        content: (
          <div className="space-y-4">
            <p>메시지 입력창에 <code>/</code>를 입력하면 사용 가능한 커맨드가 표시됩니다.</p>
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 pr-4">커맨드</th>
                  <th className="text-left py-2">설명</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border">
                  <td className="py-2 pr-4"><code>/remember &lt;내용&gt;</code></td>
                  <td className="py-2">개인 + 대화방 메모리로 저장</td>
                </tr>
                <tr className="border-b border-border">
                  <td className="py-2 pr-4"><code>/memory</code></td>
                  <td className="py-2">최근 대화에서 메모리 자동 추출</td>
                </tr>
                <tr className="border-b border-border">
                  <td className="py-2 pr-4"><code>/search &lt;검색어&gt;</code></td>
                  <td className="py-2">저장된 메모리 검색</td>
                </tr>
                <tr className="border-b border-border">
                  <td className="py-2 pr-4"><code>/forget &lt;검색어&gt;</code></td>
                  <td className="py-2">메모리 삭제</td>
                </tr>
                <tr className="border-b border-border">
                  <td className="py-2 pr-4"><code>/members</code></td>
                  <td className="py-2">대화방 멤버 목록</td>
                </tr>
                <tr className="border-b border-border">
                  <td className="py-2 pr-4"><code>/invite &lt;이메일&gt;</code></td>
                  <td className="py-2">멤버 초대 (관리자)</td>
                </tr>
                <tr>
                  <td className="py-2 pr-4"><code>/help</code></td>
                  <td className="py-2">도움말</td>
                </tr>
              </tbody>
            </table>
            <div className="tip-box">
              <strong>💡 팁:</strong> <code>/memory</code>는 <code>@ai</code> 없이 일반 대화만 한 경우에도 수동으로 메모리를 추출할 수 있습니다. 중복 메모리는 자동으로 건너뜁니다.
            </div>
          </div>
        ),
      },
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
              <p>대화방 이름을 입력합니다.</p>
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
                <li><strong>범위:</strong> 개인, 대화방</li>
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
        title: '문서-대화방 연결',
        description: '업로드된 문서를 대화방에 연결하여 RAG로 활용하는 방법',
        content: (
          <div className="space-y-4">
            <div className="step">
              <span className="step-number">1</span>
              <strong>대화방 설정 열기</strong>
              <p>대화방 헤더의 설정(톱니바퀴) 아이콘을 클릭합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <strong>문서 연결</strong>
              <p>"문서 연결" 섹션에서 연결할 문서를 선택합니다.</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <strong>AI 응답에서 문서 활용</strong>
              <p>연결된 문서는 <code>@ai</code> 질문 시 자동으로 참조됩니다. AI가 문서 내용을 기반으로 더 정확한 답변을 제공합니다.</p>
            </div>
            <div className="feature-box">
              <strong>참고:</strong> 하나의 문서를 여러 대화방에 연결할 수 있고, 하나의 대화방에 여러 문서를 연결할 수 있습니다 (다대다 관계).
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

type DocView = 'usage-guide' | 'agent-guide'

const docViewConfig: Record<DocView, { title: string; url: string }> = {
  'usage-guide': { title: '사용 가이드 (전체)', url: '/guide.html' },
  'agent-guide': { title: 'Agent 연동 가이드 (전체)', url: '/docs/agent-integration-guide.html' },
}

interface GuidePanelProps {
  isOpen: boolean
  onClose: () => void
  initialView?: 'list' | 'agent-guide-doc' | 'usage-guide-doc'
}

export function GuidePanel({ isOpen, onClose, initialView }: GuidePanelProps) {
  const [selectedItem, setSelectedItem] = useState<GuideItem | null>(null)
  const [docView, setDocView] = useState<DocView | null>(null)
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
    sdk: true,
    chat: false,
    memory: false,
    permission: false,
  })

  useEffect(() => {
    if (isOpen && initialView) {
      if (initialView === 'agent-guide-doc') {
        setDocView('agent-guide')
        setSelectedItem(null)
      } else if (initialView === 'usage-guide-doc') {
        setDocView('usage-guide')
        setSelectedItem(null)
      } else {
        setDocView(null)
      }
    }
    if (!isOpen) {
      setDocView(null)
      setSelectedItem(null)
    }
  }, [isOpen, initialView])

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories((prev) => ({ ...prev, [categoryId]: !prev[categoryId] }))
  }

  if (!isOpen) return null

  const handleBackToList = () => {
    setDocView(null)
    setSelectedItem(null)
  }

  return (
    <div className="fixed inset-y-0 right-0 w-[700px] bg-background border-l border-border shadow-xl flex flex-col z-50">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          {docView ? (
            <>
              <Button variant="ghost" size="sm" onClick={handleBackToList} className="gap-1 px-2">
                <ArrowLeft className="h-4 w-4" />
                돌아가기
              </Button>
              <span className="text-sm font-medium text-foreground-muted">
                {docViewConfig[docView].title}
              </span>
            </>
          ) : (
            <>
              <Bot className="h-5 w-5 text-accent" />
              <h2 className="font-semibold">사용 가이드</h2>
            </>
          )}
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-5 w-5" />
        </Button>
      </div>

      {/* docView: iframe */}
      {docView ? (
        <iframe
          src={docViewConfig[docView].url}
          className="flex-1 w-full border-0"
          title={docViewConfig[docView].title}
        />
      ) : (
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
              <div className="space-y-4 guide-content">{selectedItem.content}</div>
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

          {/* 전체 문서 보기 링크 */}
          {!selectedItem && (
            <div className="mt-8 pt-6 border-t border-border space-y-3">
              <h4 className="text-sm font-semibold text-foreground-muted mb-3">전체 문서 보기</h4>
              <button
                onClick={() => setDocView('usage-guide')}
                className="w-full flex items-center gap-2 p-3 rounded-lg border border-border hover:bg-background-hover transition-colors text-left"
              >
                <FileText className="h-4 w-4 text-accent shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">사용 가이드 (전체)</p>
                  <p className="text-xs text-foreground-muted">메모리 관리, 문서, 검색, 에이전트 활용</p>
                </div>
              </button>
              <button
                onClick={() => setDocView('agent-guide')}
                className="w-full flex items-center gap-2 p-3 rounded-lg border border-border hover:bg-background-hover transition-colors text-left"
              >
                <FileText className="h-4 w-4 text-accent shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">Agent 연동 가이드 (전체)</p>
                  <p className="text-xs text-foreground-muted">Agent 클래스, 클라이언트 API, 코드 예시</p>
                </div>
              </button>
            </div>
          )}
        </div>
      </ScrollArea>
      )}
    </div>
  )
}
