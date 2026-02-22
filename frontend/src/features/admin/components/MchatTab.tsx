import { useMchatStatus, useMchatChannels, useMchatUsers, useToggleMchatChannelSync } from '../hooks/useAdmin'
import { Loading } from '@/components/common/Loading'

export function MchatTab() {
  const { data: status, isLoading: statusLoading } = useMchatStatus()
  const { data: channels, isLoading: channelsLoading } = useMchatChannels()
  const { data: users, isLoading: usersLoading } = useMchatUsers()
  const toggleSync = useToggleMchatChannelSync()

  if (statusLoading) return <Loading />

  return (
    <div className="space-y-6">
      {/* 연결 상태 */}
      <div className="bg-surface rounded-lg border border-border p-4">
        <h3 className="text-sm font-semibold mb-3">연결 상태</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-foreground-secondary">상태: </span>
            <span className={
              status?.status === 'connected' ? 'text-green-500 font-medium' :
              status?.status === 'disconnected' ? 'text-yellow-500 font-medium' :
              'text-foreground-secondary font-medium'
            }>
              {status?.status === 'connected' ? 'Connected' :
               status?.status === 'disconnected' ? 'Disconnected' :
               'Disabled'}
            </span>
          </div>
          <div>
            <span className="text-foreground-secondary">URL: </span>
            <span className="font-mono text-xs">{status?.base_url || '-'}</span>
          </div>
          <div>
            <span className="text-foreground-secondary">Bot ID: </span>
            <span className="font-mono text-xs">{status?.bot_user_id || '-'}</span>
          </div>
          {status?.last_error && (
            <div className="col-span-2">
              <span className="text-foreground-secondary">Error: </span>
              <span className="text-red-400 text-xs">{status.last_error}</span>
            </div>
          )}
        </div>

        {/* 통계 */}
        {status?.stats && (
          <div className="mt-3 pt-3 border-t border-border">
            <div className="flex gap-6 text-sm">
              <div>
                <span className="text-foreground-secondary">수신: </span>
                <span className="font-medium">{status.stats.messages_received}</span>
              </div>
              <div>
                <span className="text-foreground-secondary">응답: </span>
                <span className="font-medium">{status.stats.messages_responded}</span>
              </div>
              <div>
                <span className="text-foreground-secondary">메모리 추출: </span>
                <span className="font-medium">{status.stats.memories_extracted}</span>
              </div>
              {status.stats.errors > 0 && (
                <div>
                  <span className="text-foreground-secondary">오류: </span>
                  <span className="text-red-400 font-medium">{status.stats.errors}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 채널 매핑 */}
      <div className="bg-surface rounded-lg border border-border p-4">
        <h3 className="text-sm font-semibold mb-3">
          채널 매핑 ({channels?.length || 0})
        </h3>
        {channelsLoading ? (
          <Loading />
        ) : !channels?.length ? (
          <p className="text-sm text-foreground-secondary">매핑된 채널이 없습니다</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-foreground-secondary text-left">
                  <th className="pb-2 pr-4">Mchat 채널</th>
                  <th className="pb-2 pr-4">Agent 대화방</th>
                  <th className="pb-2 pr-4">동기화</th>
                  <th className="pb-2">생성일</th>
                </tr>
              </thead>
              <tbody>
                {channels.map((ch) => (
                  <tr key={ch.id} className="border-b border-border/50">
                    <td className="py-2 pr-4">
                      <div className="font-medium">{ch.mchat_channel_name || ch.mchat_channel_id.slice(0, 8)}</div>
                      <div className="text-xs text-foreground-secondary font-mono">{ch.mchat_channel_id.slice(0, 12)}...</div>
                    </td>
                    <td className="py-2 pr-4">
                      <div>{ch.agent_room_name || '-'}</div>
                      <div className="text-xs text-foreground-secondary font-mono">{ch.agent_room_id.slice(0, 12)}...</div>
                    </td>
                    <td className="py-2 pr-4">
                      <button
                        onClick={() => toggleSync.mutate(ch.id)}
                        disabled={toggleSync.isPending}
                        className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                          ch.sync_enabled
                            ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                            : 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                        }`}
                      >
                        {ch.sync_enabled ? 'ON' : 'OFF'}
                      </button>
                    </td>
                    <td className="py-2 text-foreground-secondary text-xs">
                      {ch.created_at ? new Date(ch.created_at).toLocaleDateString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 사용자 매핑 */}
      <div className="bg-surface rounded-lg border border-border p-4">
        <h3 className="text-sm font-semibold mb-3">
          사용자 매핑 ({users?.length || 0})
        </h3>
        {usersLoading ? (
          <Loading />
        ) : !users?.length ? (
          <p className="text-sm text-foreground-secondary">매핑된 사용자가 없습니다</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-foreground-secondary text-left">
                  <th className="pb-2 pr-4">Mchat 사용자</th>
                  <th className="pb-2 pr-4">Agent 사용자</th>
                  <th className="pb-2">생성일</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-border/50">
                    <td className="py-2 pr-4">
                      <div className="font-medium">{u.mchat_username || 'unknown'}</div>
                      <div className="text-xs text-foreground-secondary font-mono">{u.mchat_user_id.slice(0, 12)}...</div>
                    </td>
                    <td className="py-2 pr-4">
                      <div>{u.agent_user_name || '-'}</div>
                      <div className="text-xs text-foreground-secondary">{u.agent_user_email || '-'}</div>
                    </td>
                    <td className="py-2 text-foreground-secondary text-xs">
                      {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
