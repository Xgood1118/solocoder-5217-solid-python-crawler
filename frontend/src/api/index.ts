import type {
  Article,
  ArticleListResponse,
  CrawlStatus,
  CrawlTriggerRequest,
  CrawlTriggerResponse,
  ClearDataResponse,
  RefreshArticleResponse,
} from './types';

const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export async function getArticles(params: {
  page?: number;
  size?: number;
  source?: string;
  keyword?: string;
  sort?: string;
}): Promise<ArticleListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.size) searchParams.set('size', String(params.size));
  if (params.source) searchParams.set('source', params.source);
  if (params.keyword) searchParams.set('keyword', params.keyword);
  if (params.sort) searchParams.set('sort', params.sort);

  return request<ArticleListResponse>(`/articles?${searchParams.toString()}`);
}

export async function getArticle(id: string): Promise<Article> {
  return request<Article>(`/articles/${id}`);
}

export async function refreshArticle(id: string): Promise<RefreshArticleResponse> {
  return request<RefreshArticleResponse>(`/articles/${id}/refresh`, {
    method: 'POST',
  });
}

export async function getCrawlStatus(): Promise<CrawlStatus> {
  return request<CrawlStatus>('/crawl/status');
}

export async function triggerCrawl(mode: 'incremental' | 'full' = 'incremental'): Promise<CrawlTriggerResponse> {
  return request<CrawlTriggerResponse>('/crawl/trigger', {
    method: 'POST',
    body: JSON.stringify({ mode }),
  });
}

export async function clearData(): Promise<ClearDataResponse> {
  return request<ClearDataResponse>('/crawl/clear', {
    method: 'POST',
  });
}

export function createCrawlProgressStream(): EventSource {
  return new EventSource(`${API_BASE}/crawl/progress`);
}
