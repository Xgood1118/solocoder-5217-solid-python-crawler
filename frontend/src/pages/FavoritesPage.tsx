import { Component, createSignal, createEffect, For } from 'solid-js'
import { favorites, toggleFavorite } from '../store/preferences'

interface Props {
  navigate: (path: string) => void
}

const FavoritesPage: Component<Props> = (props) => {
  const [articles, setArticles] = createSignal<any[]>([])
  const [loading, setLoading] = createSignal(true)
  const [error, setError] = createSignal<string | null>(null)

  const loadFavorites = async () => {
    setLoading(true)
    setError(null)
    try {
      const favIds = favorites()
      const loaded: any[] = []
      for (const id of favIds) {
        try {
          const res = await fetch(`/api/articles/${id}`)
          if (res.ok) {
            const article = await res.json()
            loaded.push(article)
          }
        } catch {
          // skip
        }
      }
      setArticles(loaded)
    } catch (e: any) {
      setError(e.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  createEffect(() => {
    loadFavorites()
  })

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const goToDetail = (id: string) => {
    props.navigate(`/article/${id}`)
  }

  return (
    <div>
      <h2 style="margin-bottom: 1.5rem;">我的收藏</h2>

      {loading() && (
        <div class="loading">加载中...</div>
      )}

      {error() && (
        <div class="error">{error()}</div>
      )}

      {!loading() && !error() && articles().length === 0 && (
        <div class="empty">
          <p>还没有收藏任何文章</p>
          <a href="/" onClick={(e) => { e.preventDefault(); props.navigate('/') }} style="margin-top: 1rem; display: inline-block;">
            去看看文章 →
          </a>
        </div>
      )}

      <For each={articles()}>
        {(article: any) => (
          <div class="card" key={article.id} onClick={() => goToDetail(article.id)} style="cursor: pointer;">
            <div class="article-meta">
              <span class="source-badge">{article.source_name}</span>
              {article.author && <span>作者：{article.author}</span>}
              {article.publish_time && <span>发布：{formatDate(article.publish_time)}</span>}
              {article.heat != null && <span>🔥 {article.heat}</span>}
            </div>
            <h3 class="article-title">
              <a href={`/article/${article.id}`} onClick={(e) => { e.stopPropagation(); e.preventDefault(); goToDetail(article.id) }}>
                {article.title}
              </a>
            </h3>
            {article.summary && (
              <p class="article-summary">{article.summary}</p>
            )}
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem;">
              <span style="font-size: 0.75rem; color: var(--text-muted);">
                抓取于 {formatDate(article.crawled_at)}
              </span>
              <button
                class="icon-btn favorite"
                onClick={(e) => {
                  e.stopPropagation()
                  toggleFavorite(article.id)
                  setArticles(prev => prev.filter(a => a.id !== article.id))
                }}
                title="取消收藏"
              >
                ❤️
              </button>
            </div>
          </div>
        )}
      </For>
    </div>
  )
}

export default FavoritesPage
