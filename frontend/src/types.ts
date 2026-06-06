export interface Article {
  id: string;
  title: string;
  source: string;
  source_name: string;
  url: string;
  author?: string;
  publish_time?: string;
  summary?: string;
  content?: string;
  tags: string[];
  heat?: number;
  crawled_at: string;
  error?: string;
}

export interface ArticleListItem {
  id: string;
  title: string;
  source: string;
  source_name: string;
  url: string;
  author?: string;
  publish_time?: string;
  summary?: string;
  tags: string[];
  heat?: number;
  crawled_at: string;
}

export interface ArticleListResponse {
  total: number;
  page: number;
  size: number;
  items: ArticleListItem[];
}

export interface CrawlSourceStatus {
  source: string;
  source_name: string;
  last_crawl_time?: string;
  last_success_time?: string;
  last_failure_time?: string;
  last_error?: string;
  consecutive_failures: number;
  article_count: number;
  status: string;
}

export interface CrawlLogEntry {
  source: string;
  timestamp: string;
  status: string;
  duration_seconds: number;
  article_count: number;
  error?: string;
}

export interface CrawlStatus {
  is_running: boolean;
  current_source?: string;
  progress: number;
  total_sources: number;
  completed_sources: number;
  last_crawl_time?: string;
  last_crawl_duration?: number;
  total_articles: number;
  sources: Record<string, CrawlSourceStatus>;
  recent_logs: CrawlLogEntry[];
}

export interface CrawlTriggerRequest {
  mode: 'incremental' | 'full';
}

export interface CrawlTriggerResponse {
  success: boolean;
  message: string;
  task_id?: string;
}

export interface ClearDataResponse {
  success: boolean;
  message: string;
  cleared_count: number;
}

export interface RefreshArticleResponse {
  success: boolean;
  message: string;
  article?: Article;
}
