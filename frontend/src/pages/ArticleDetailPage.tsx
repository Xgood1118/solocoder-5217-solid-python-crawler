import { Component, createResource, createSignal } from 'solid-js'
import { getArticle, refreshArticle } from '../api'
import { toggleFavorite, isFavorite } from '../store/preferences'
import { useParams } from '../utils/router'

interface Props {
  path: string
  navigate: (path: string) => void
}

const ArticleDetailPage: Component<Props> = (props) => {
  const params = () => useParams('/article/:id', props.path)
  const articleId = () => params().id || ''

  const [articleResource, { refetch }] = createResource(articleId, (id) => {
    if (!id) return Promise.reject('No article id')
    return getArticle(id)
  })

  const [refreshing, setRefreshing] = createSignal(false)

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      const result = await refreshArticle(articleId())
      if (result.success) {
        refetch()
      }
    } finally {
      setRefreshing(false)
    }
  }

  const article = () => articleResource()

  return (
    <div>
      <div style="margin-bottom: 1rem;">
        <a href="/" onClick={(e) => { e.preventDefault(); props.navigate('/') }}>← 返回列表</a>
      </div>

      {articleResource.loading && (
        <div class="loading">加载中...</div>
      )}

      {articleResource.error && (
        <div class="error">加载失败：{articleResource.error.message}</div>
      )}

      {article() && (
        <div class="card" style="padding: 2rem;">
          <div class="detail-header">
            <div class="article-meta">
              <span class="source-badge">{article()!.source_name}</span>
              {article()!.author && <span>作者：{article()!.author}</span>}
              {article()!.publish_time && <span>发布：{formatDate(article()!.publish_time)}</span>}
              {article()!.heat != null && <span>🔥 {article()!.heat}</span>}
            </div>
            <h1 style="font-size: 1.75rem; margin: 1rem 0;">{article()!.title}</h1>
            {article()!.tags && article()!.tags.length > 0 && (
              <div class="article-tags">
                {article()!.tags.map(tag => (
                  <span class="tag" key={tag}>{tag}</span>
                ))}
              </div>
            )}
          </div>

          <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
            <button
              class={`icon-btn ${isFavorite(articleId()) ? 'favorite' : ''}`}
              onClick={() => toggleFavorite(articleId())}
              title={isFavorite(articleId()) ? '取消收藏' : '收藏'}
              style="width: auto; padding: 0.5rem 1rem;"
            >
              {isFavorite(articleId()) ? '❤️ 已收藏' : '🤍 收藏'}
            </button>
            <button
              class="icon-btn"
              onClick={handleRefresh}
              disabled={refreshing()}
              style="width: auto; padding: 0.5rem 1rem;"
            >
              {refreshing() ? '刷新中...' : '🔄 重新抓取'}
            </button>
            <a
              href={article()!.url}
              target="_blank"
              rel="noopener noreferrer"
              class="icon-btn"
              style="width: auto; padding: 0.5rem 1rem; text-decoration: none;"
            >
              🔗 查看原文
            </a>
          </div>

          {article()!.error && (
            <div style="padding: 1rem; background: var(--bg-tertiary); border-radius: var(--radius-sm); margin-bottom: 1rem; color: var(--danger-color);">
              抓取错误：{article()!.error}
            </div>
          )}

          {article()!.summary && (
            <div style="padding: 1rem; background: var(--bg-secondary); border-radius: var(--radius-sm); margin-bottom: 1.5rem;">
              <strong>摘要：</strong>{article()!.summary}
            </div>
          )}

          {article()!.content ? (
            <div class="detail-content" innerHTML={article()!.content} />
          ) : (
            <div class="empty">
              <p>暂无全文内容</p>
              <p style="font-size: 0.875rem; margin-top: 0.5rem;">
                你可以点击上方"重新抓取"按钮尝试获取全文，或直接查看原文链接。
              </p>
            </div>
          )}

          <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border-color); font-size: 0.875rem; color: var(--text-muted);">
            <p>抓取时间：{formatDate(article()!.crawled_at)}</p>
            <p>原文链接：<a href={article()!.url} target="_blank" rel="noopener noreferrer">{article()!.url}</a></p>
          </div>
        </div>
      )}
    </div>
  )
}

export default ArticleDetailPage
