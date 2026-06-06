import { Component, Match, Switch, createSignal, onMount, onCleanup } from 'solid-js'
import { darkMode, setDarkMode } from './store/preferences'
import ArticleListPage from './pages/ArticleListPage'
import ArticleDetailPage from './pages/ArticleDetailPage'
import CrawlStatusPage from './pages/CrawlStatusPage'
import FavoritesPage from './pages/FavoritesPage'
import { matchPath } from './utils/router'

const App: Component = () => {
  const [currentPath, setCurrentPath] = createSignal(window.location.pathname)

  onMount(() => {
    const handlePopState = () => setCurrentPath(window.location.pathname)
    window.addEventListener('popstate', handlePopState)
    onCleanup(() => window.removeEventListener('popstate', handlePopState))
  })

  const navigate = (path: string) => {
    if (path === currentPath()) return
    window.history.pushState({}, '', path)
    setCurrentPath(path)
    window.scrollTo(0, 0)
  }

  const isActive = (path: string, end = false) => {
    if (end) return currentPath() === path
    return currentPath().startsWith(path)
  }

  const linkProps = (path: string) => ({
    href: path,
    onClick: (e: MouseEvent) => {
      e.preventDefault()
      navigate(path)
    },
  })

  return (
    <div class="app">
      <header class="header">
        <div class="container header-content">
          <a {...linkProps('/')} class="logo">
            技术新闻聚合
          </a>
          <nav class="nav">
            <a
              {...linkProps('/')}
              class={`nav-link ${isActive('/', true) ? 'active' : ''}`}
            >
              首页
            </a>
            <a
              {...linkProps('/favorites')}
              class={`nav-link ${isActive('/favorites') ? 'active' : ''}`}
            >
              收藏
            </a>
            <a
              {...linkProps('/crawl-status')}
              class={`nav-link ${isActive('/crawl-status') ? 'active' : ''}`}
            >
              抓取状态
            </a>
            <button
              class="icon-btn"
              onClick={() => setDarkMode(!darkMode())}
              title={darkMode() ? '切换到亮色模式' : '切换到暗色模式'}
            >
              {darkMode() ? '☀️' : '🌙'}
            </button>
          </nav>
        </div>
      </header>
      <main class="main">
        <div class="container">
          <Switch>
            <Match when={currentPath() === '/'}>
              <ArticleListPage navigate={navigate} />
            </Match>
            <Match when={matchPath('/article/:id', currentPath())}>
              <ArticleDetailPage path={currentPath()} navigate={navigate} />
            </Match>
            <Match when={currentPath() === '/favorites'}>
              <FavoritesPage navigate={navigate} />
            </Match>
            <Match when={currentPath() === '/crawl-status'}>
              <CrawlStatusPage />
            </Match>
          </Switch>
        </div>
      </main>
    </div>
  )
}

export default App
