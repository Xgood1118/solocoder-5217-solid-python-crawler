import { Component, createSignal, onMount, onCleanup, createResource } from 'solid-js'
import { getCrawlStatus, triggerCrawl, clearData, createCrawlProgressStream } from '../api'
import type { CrawlStatus as CrawlStatusType } from '../types'

const CrawlStatusPage: Component = () => {
  const [status, setStatus] = createSignal<CrawlStatusType | null>(null)
  const [loading, setLoading] = createSignal(true)
  const [error, setError] = createSignal<string | null>(null)
  const [actionLoading, setActionLoading] = createSignal(false)

  let eventSource: EventSource | null = null

  const loadStatus = async () => {
    try {
      const data = await getCrawlStatus()
      setStatus(data)
      setError(null)
    } catch (e: any) {
      setError(e.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  onMount(() => {
    loadStatus()

    try {
      eventSource = createCrawlProgressStream()
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setStatus(prev => {
            if (!prev) return prev
            return {
              ...prev,
              is_running: data.is_running,
              current_source: data.current_source,
              progress: data.progress,
              total_sources: data.total_sources,
              completed_sources: data.completed_sources,
              total_articles: data.total_articles,
              last_crawl_time: data.last_crawl_time,
              last_crawl_duration: data.last_crawl_duration,
            }
          })
        } catch {
          // ignore parse errors
        }
      }
      eventSource.onerror = () => {
        // connection error, will retry
      }
    } catch {
      // SSE not supported, fall back to polling
    }
  })

  onCleanup(() => {
    if (eventSource) {
      eventSource.close()
    }
  })

  const handleTriggerCrawl = async (mode: 'incremental' | 'full') => {
    setActionLoading(true)
    try {
      const result = await triggerCrawl(mode)
      if (result.success) {
        setTimeout(loadStatus, 500)
      } else {
        alert(result.message)
      }
    } catch (e: any) {
      alert('触发失败：' + e.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleClearData = async () => {
    if (!confirm('确定要清空所有文章数据吗？')) return
    setActionLoading(true)
    try {
      const result = await clearData()
      if (result.success) {
        loadStatus()
      }
    } catch (e: any) {
      alert('清空失败：' + e.message)
    } finally {
      setActionLoading(false)
    }
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '从未'
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  }

  const formatDuration = (seconds?: number) => {
    if (seconds == null) return '-'
    if (seconds < 60) return `${seconds.toFixed(1)} 秒`
    return `${Math.floor(seconds / 60)} 分 ${(seconds % 60).toFixed(0)} 秒`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'green'
      case 'running':
        return 'yellow'
      case 'failed':
        return 'red'
      default:
        return 'gray'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'success':
        return '成功'
      case 'running':
        return '运行中'
      case 'failed':
        return '失败'
      case 'skipped':
        return '跳过'
      default:
        return '空闲'
    }
  }

  return (
    <div>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <h2>抓取状态</h2>
        <div style="display: flex; gap: 0.5rem;">
          <button
            class="icon-btn"
            style="width: auto; padding: 0.5rem 1rem;"
            onClick={() => handleTriggerCrawl('incremental')}
            disabled={actionLoading() || status()?.is_running}
          >
            ⚡ 立即抓取
          </button>
          <button
            class="icon-btn"
            style="width: auto; padding: 0.5rem 1rem;"
            onClick={() => handleTriggerCrawl('full')}
            disabled={actionLoading() || status()?.is_running}
          >
            🔄 全量重抓
          </button>
          <button
            class="icon-btn"
            style="width: auto; padding: 0.5rem 1rem; color: var(--danger-color);"
            onClick={handleClearData}
            disabled={actionLoading()}
          >
            🗑️ 清空数据
          </button>
        </div>
      </div>

      {loading() && (
        <div class="loading">加载中...</div>
      )}

      {error() && (
        <div class="error">{error()}</div>
      )}

      {status() && (
        <>
          <div class="card" style="margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
              <div>
                <span class={`status-indicator status-${status()!.is_running ? 'yellow' : 'green'}`}></span>
                <strong>{status()!.is_running ? '抓取进行中' : '系统空闲'}</strong>
              </div>
              <div style="color: var(--text-secondary); font-size: 0.875rem;">
                总文章数：<strong>{status()!.total_articles}</strong>
              </div>
            </div>

            {status()!.is_running && (
              <div style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.875rem; margin-bottom: 0.25rem;">
                  <span>当前源：{status()!.current_source || '-'}</span>
                  <span>{status()!.completed_sources}/{status()!.total_sources} 个源</span>
                </div>
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    style={{ width: `${(status()!.progress * 100).toFixed(0)}%` }}
                  ></div>
                </div>
              </div>
            )}

            <div class="grid grid-2" style="font-size: 0.875rem;">
              <div>
                <span style="color: var(--text-secondary);">上次抓取时间：</span>
                {formatDate(status()!.last_crawl_time)}
              </div>
              <div>
                <span style="color: var(--text-secondary);">上次抓取耗时：</span>
                {formatDuration(status()!.last_crawl_duration)}
              </div>
            </div>
          </div>

          <h3 style="margin-bottom: 1rem;">数据源状态</h3>
          <div class="grid grid-4" style="margin-bottom: 2rem;">
            {Object.entries(status()!.sources).map(([sourceId, sourceStatus]) => (
              <div
                class={`source-status-card ${sourceStatus.status}`}
                key={sourceId}
              >
                <div class="source-status-header">
                  <span class="source-status-name">{sourceStatus.source_name}</span>
                  <span class={`status-indicator status-${getStatusColor(sourceStatus.status)}`}></span>
                </div>
                <div style="font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.8;">
                  <div>状态：{getStatusText(sourceStatus.status)}</div>
                  <div>文章数：{sourceStatus.article_count}</div>
                  <div>上次成功：{formatDate(sourceStatus.last_success_time)}</div>
                  {sourceStatus.last_error && (
                    <div style="color: var(--danger-color); margin-top: 0.5rem; font-size: 0.75rem;">
                      错误：{sourceStatus.last_error}
                    </div>
                  )}
                  {sourceStatus.consecutive_failures > 0 && (
                    <div style="color: var(--warning-color); font-size: 0.75rem;">
                      连续失败：{sourceStatus.consecutive_failures} 次
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <h3 style="margin-bottom: 1rem;">最近抓取日志</h3>
          <div class="card" style="padding: 0;">
            {status()!.recent_logs.length === 0 ? (
              <div class="empty">暂无日志</div>
            ) : (
              status()!.recent_logs.map((log, index) => (
                <div class="log-entry" key={index}>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                      <span class={`status-indicator status-${getStatusColor(log.status)}`}></span>
                      <strong>{log.source}</strong>
                      <span style="margin-left: 0.5rem;">{getStatusText(log.status)}</span>
                      {log.article_count > 0 && (
                        <span style="margin-left: 0.5rem; color: var(--success-color);">
                          +{log.article_count} 篇
                        </span>
                      )}
                    </div>
                    <span class="log-time">{formatDate(log.timestamp)}</span>
                  </div>
                  <div style="margin-top: 0.25rem;">
                    <span class="log-time">
                      耗时 {formatDuration(log.duration_seconds)}
                    </span>
                    {log.error && (
                      <span style="color: var(--danger-color); margin-left: 1rem; font-size: 0.75rem;">
                        错误：{log.error}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default CrawlStatusPage
