import { Component, createResource, createSignal } from 'solid-js'
import { getArticles } from '../api'
import { enabledSources, toggleSource, toggleFavorite, isFavorite } from '../store/preferences'
import type { ArticleListItem } from '../types'

const sources = [
  { id: 'huxiu', name: '虎嗅' },
  { id: '36kr', name: '36氪' },
  { id: 'infoq', name: 'InfoQ' },
  { id: 'juejin', name: '掘金' },
]

const sortOptions = [
  { value: 'publish_time', label: '按时间' },
  { value: 'heat', label: '按热度' },
  { value: 'crawled_at', label: '按抓取时间' },
]

interface Props {
  navigate: (path: string) => void
}

const ArticleListPage: Component<Props> = (props) => {
  const [page, setPage] = createSignal(1)
  const [pageSize] = createSignal(20)
  const [keyword, setKeyword] = createSignal('')
  const [sort, setSort] = createSignal('publish_time')

  const [articlesResource, { refetch }] = createResource(
    () => ({
      page: page(),
      size: pageSize(),
      source: enabledSources().join(','),
      keyword: keyword() || undefined,
      sort: sort(),
    }),
    (params) => getArticles(params),
  )

  const handleSearch = (e: Event) => {
    e.preventDefault()
    setPage(1)
    refetch()
  }

  const handleSourceToggle = (sourceId: string) => {
    toggleSource(sourceId)
    setPage(1)
  }

  const totalPages = () => {
    const data = articlesResource()
    if (!data) return 0
    return Math.ceil(data.total / pageSize())
  }

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
      <div class="filters">
        <form onSubmit={handleSearch} class="filter-group">
          <label class="filter-label">搜索</label>
          <input
            type="text"
            class="filter-input"
            placeholder="搜索标题或摘要..."
            value={keyword()}
            onInput={(e) => setKeyword(e.target.value)}
          />
          <button type="submit" style={{ display: 'none' }}>搜索</button>
        </form>

        <div class="filter-group">
          <label class="filter-label">排序</label>
          <select
            class="filter-input"
            value={sort()}
            onChange={(e) => setSort(e.target.value)}
          >
            {sortOptions.map(opt => (
              <option value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div style="margin-bottom: 1rem;">
        <span class="filter-label" style="margin-right: 0.75rem;">关注来源：</span>
        <div class="source-filters" style="display: inline-flex;">
          {sources.map(source => (
            <button
              class={`source-filter-btn ${enabledSources().includes(source.id) ? 'active' : ''}`}
              onClick={() => handleSourceToggle(source.id)}
              title={enabledSources().includes(source.id) ? '点击取消关注' : '点击关注'}
            >
              {source.name}
            </button>
          ))}
        </div>
      </div>

      <div class="articles-list">
        {articlesResource.loading && (
          <div class="loading">加载中...</div>
        )}

        {articlesResource.error && (
          <div class="error">加载失败：{articlesResource.error.message}</div>
        )}

        {articlesResource() && articlesResource()!.items.length === 0 && (
          <div class="empty">
            <p>暂无文章</p>
            <p style="font-size: 0.875rem; margin-top: 0.5rem;">
              {enabledSources().length === 0
                ? '请先选择关注的来源'
                : '抓取任务可能还未完成，请稍后再试'}
            </p>
          </div>
        )}

        {articlesResource() && articlesResource()!.items.map((article: ArticleListItem) => (
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
            {article.tags.length > 0 && (
              <div class="article-tags">
                {article.tags.map(tag => (
                  <span class="tag" key={tag}>{tag}</span>
                ))}
              </div>
            )}
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem;">
              <span style="font-size: 0.75rem; color: var(--text-muted);">
                抓取于 {formatDate(article.crawled_at)}
              </span>
              <button
                class={`icon-btn ${isFavorite(article.id) ? 'favorite' : ''}`}
                onClick={(e) => { e.stopPropagation(); toggleFavorite(article.id) }}
                title={isFavorite(article.id) ? '取消收藏' : '收藏'}
              >
                {isFavorite(article.id) ? '❤️' : '🤍'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {articlesResource() && totalPages() > 1 && (
        <div class="pagination">
          <button
            class="page-btn"
            disabled={page() === 1}
            onClick={() => setPage(p => Math.max(1, p - 1))}
          >
            上一页
          </button>
          {Array.from({ length: Math.min(5, totalPages()) }, (_, i) => {
            let pageNum: number
            const total = totalPages()
            const current = page()
            if (total <= 5) {
              pageNum = i + 1
            } else if (current <= 3) {
              pageNum = i + 1
            } else if (current >= total - 2) {
              pageNum = total - 4 + i
            } else {
              pageNum = current - 2 + i
            }
            return (
              <button
                class={`page-btn ${pageNum === current ? 'active' : ''}`}
                onClick={() => setPage(pageNum)}
                key={pageNum}
              >
                {pageNum}
              </button>
            )
          })}
          <button
            class="page-btn"
            disabled={page() === totalPages()}
            onClick={() => setPage(p => Math.min(totalPages(), p + 1))}
          >
            下一页
          </button>
        </div>
      )}

      {articlesResource() && (
        <div style="text-align: center; margin-top: 1rem; color: var(--text-secondary); font-size: 0.875rem;">
          共 {articlesResource()!.total} 篇文章
        </div>
      )}
    </div>
  )
}

export default ArticleListPage
