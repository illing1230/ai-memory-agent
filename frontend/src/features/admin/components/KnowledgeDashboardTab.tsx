import { Brain, FileText, AlertTriangle, Hash, Trophy, Clock } from 'lucide-react'
import { Loading } from '@/components/common/Loading'
import { useKnowledgeDashboard } from '../hooks/useAdmin'

const ENTITY_TYPE_COLORS: Record<string, string> = {
  person: 'bg-blue-500/20 text-blue-400',
  meeting: 'bg-purple-500/20 text-purple-400',
  project: 'bg-green-500/20 text-green-400',
  organization: 'bg-orange-500/20 text-orange-400',
  topic: 'bg-cyan-500/20 text-cyan-400',
  date: 'bg-pink-500/20 text-pink-400',
}

function HorizontalBar({ items, colorMap }: { items: Record<string, number>; colorMap?: Record<string, string> }) {
  const total = Object.values(items).reduce((a, b) => a + b, 0)
  if (total === 0) return <p className="text-sm text-foreground-secondary">데이터 없음</p>

  const defaultColors = ['bg-accent', 'bg-success', 'bg-warning', 'bg-info', 'bg-error', 'bg-purple-500', 'bg-pink-500']
  const keys = Object.keys(items)

  return (
    <div className="space-y-2">
      {keys.map((key, i) => {
        const pct = Math.max((items[key] / total) * 100, 2)
        const barColor = colorMap?.[key] || defaultColors[i % defaultColors.length]
        return (
          <div key={key} className="flex items-center gap-2">
            <span className="text-xs text-foreground-secondary w-24 truncate">{key}</span>
            <div className="flex-1 bg-background-secondary rounded-full h-5 overflow-hidden">
              <div
                className={`h-full rounded-full ${barColor} flex items-center justify-end pr-2 transition-all`}
                style={{ width: `${pct}%`, minWidth: '2rem' }}
              >
                <span className="text-xs font-medium text-white">{items[key]}</span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function KnowledgeDashboardTab() {
  const { data, isLoading } = useKnowledgeDashboard()

  if (isLoading) {
    return <div className="flex justify-center py-12"><Loading size="lg" /></div>
  }

  if (!data) return null

  const { memory_stats, hot_topics, stale_knowledge, contributions, document_stats } = data
  const totalStale = stale_knowledge.no_access_30d

  const summaryCards = [
    { label: '활성 메모리', value: memory_stats.active, icon: Brain, color: 'text-accent' },
    { label: '문서 수', value: document_stats.total, icon: FileText, color: 'text-success' },
    { label: '오래된 지식 (30d+)', value: totalStale, icon: AlertTriangle, color: 'text-warning' },
    { label: '핫 토픽', value: hot_topics.length, icon: Hash, color: 'text-info' },
  ]

  const importanceColors: Record<string, string> = {
    high: 'bg-error',
    medium: 'bg-warning',
    low: 'bg-success',
  }

  return (
    <div className="space-y-6">
      {/* 상단 요약 카드 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {summaryCards.map((card) => (
          <div key={card.label} className="card p-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-background-secondary ${card.color}`}>
                <card.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{card.value.toLocaleString()}</p>
                <p className="text-sm text-foreground-secondary">{card.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 최근 활동 */}
      <div className="card p-4">
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
          <Clock className="h-4 w-4 text-foreground-secondary" />
          최근 메모리 생성
        </h3>
        <div className="flex gap-6">
          <div>
            <p className="text-xl font-bold">{memory_stats.recent_7d}</p>
            <p className="text-xs text-foreground-secondary">최근 7일</p>
          </div>
          <div>
            <p className="text-xl font-bold">{memory_stats.recent_30d}</p>
            <p className="text-xs text-foreground-secondary">최근 30일</p>
          </div>
          <div>
            <p className="text-xl font-bold">{memory_stats.total}</p>
            <p className="text-xs text-foreground-secondary">전체</p>
          </div>
          <div>
            <p className="text-xl font-bold">{memory_stats.superseded}</p>
            <p className="text-xs text-foreground-secondary">대체됨</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 메모리 분포 - Scope */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold mb-3">Scope별 메모리</h3>
          <HorizontalBar items={memory_stats.by_scope} />
        </div>

        {/* 메모리 분포 - Category */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold mb-3">Category별 메모리</h3>
          <HorizontalBar items={memory_stats.by_category} />
        </div>

        {/* 메모리 분포 - Importance */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold mb-3">중요도별 메모리</h3>
          <HorizontalBar items={memory_stats.by_importance} colorMap={importanceColors} />
        </div>

        {/* 오래된 지식 */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-warning" />
            오래된 지식
          </h3>
          <div className="space-y-3">
            {[
              { label: '30일 미접근', value: stale_knowledge.no_access_30d, color: 'text-success' },
              { label: '60일 미접근', value: stale_knowledge.no_access_60d, color: 'text-warning' },
              { label: '90일 미접근', value: stale_knowledge.no_access_90d, color: 'text-error' },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="text-sm text-foreground-secondary">{item.label}</span>
                <span className={`text-lg font-bold ${item.color}`}>{item.value}</span>
              </div>
            ))}
            <div className="border-t border-border pt-2 flex items-center justify-between">
              <span className="text-sm text-foreground-secondary">낮은 중요도 + 미사용</span>
              <span className="text-lg font-bold text-error">{stale_knowledge.low_importance_stale}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 핫 토픽 TOP 15 */}
      <div className="card p-4">
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
          <Hash className="h-4 w-4 text-info" />
          핫 토픽 TOP {hot_topics.length}
        </h3>
        {hot_topics.length === 0 ? (
          <p className="text-sm text-foreground-secondary">엔티티 데이터 없음</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {hot_topics.map((topic, i) => (
              <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-background-secondary">
                <span className="text-xs font-mono text-foreground-secondary w-5">{i + 1}</span>
                <span className="text-sm font-medium flex-1 truncate">{topic.entity_name}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${ENTITY_TYPE_COLORS[topic.entity_type] || 'bg-gray-500/20 text-gray-400'}`}>
                  {topic.entity_type}
                </span>
                <span className="text-xs font-mono text-foreground-secondary">{topic.mention_count}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 기여도 랭킹 */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Trophy className="h-4 w-4 text-warning" />
            기여도 랭킹
          </h3>
          {contributions.length === 0 ? (
            <p className="text-sm text-foreground-secondary">데이터 없음</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-foreground-secondary text-xs">
                  <th className="text-left pb-2">#</th>
                  <th className="text-left pb-2">사용자</th>
                  <th className="text-right pb-2">생성</th>
                  <th className="text-right pb-2">활용</th>
                </tr>
              </thead>
              <tbody>
                {contributions.map((c, i) => (
                  <tr key={c.user_id} className="border-t border-border">
                    <td className="py-1.5 text-foreground-secondary">{i + 1}</td>
                    <td className="py-1.5 font-medium truncate max-w-[150px]">{c.user_name}</td>
                    <td className="py-1.5 text-right">{c.memories_created}</td>
                    <td className="py-1.5 text-right">{c.memories_accessed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* 문서 통계 */}
        <div className="card p-4 space-y-4">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <FileText className="h-4 w-4 text-success" />
            문서 통계
          </h3>
          <div className="flex gap-6">
            <div>
              <p className="text-xl font-bold">{document_stats.total}</p>
              <p className="text-xs text-foreground-secondary">전체 문서</p>
            </div>
            <div>
              <p className="text-xl font-bold">{document_stats.total_chunks}</p>
              <p className="text-xs text-foreground-secondary">전체 청크</p>
            </div>
          </div>
          <div>
            <h4 className="text-xs text-foreground-secondary mb-2">타입별</h4>
            <HorizontalBar items={document_stats.by_type} />
          </div>
          <div>
            <h4 className="text-xs text-foreground-secondary mb-2">상태별</h4>
            <HorizontalBar
              items={document_stats.by_status}
              colorMap={{ completed: 'bg-success', processing: 'bg-warning', failed: 'bg-error' }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
