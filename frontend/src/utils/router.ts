import { createSignal, onMount, onCleanup } from 'solid-js';

export function useRouter() {
  const [path, setPath] = createSignal(window.location.pathname);

  const handlePopState = () => {
    setPath(window.location.pathname);
  };

  onMount(() => {
    window.addEventListener('popstate', handlePopState);
  });

  onCleanup(() => {
    window.removeEventListener('popstate', handlePopState);
  });

  const navigate = (newPath: string) => {
    if (newPath === path()) return;
    window.history.pushState({}, '', newPath);
    setPath(newPath);
  };

  const params = (): Record<string, string> => {
    return {};
  };

  return { path, navigate, params };
}

export function useParams(pattern: string, pathname: string): Record<string, string> {
  const params: Record<string, string> = {};
  const patternParts = pattern.split('/').filter(Boolean);
  const pathParts = pathname.split('/').filter(Boolean);

  if (patternParts.length !== pathParts.length) return params;

  for (let i = 0; i < patternParts.length; i++) {
    if (patternParts[i].startsWith(':')) {
      const key = patternParts[i].slice(1);
      params[key] = decodeURIComponent(pathParts[i]);
    } else if (patternParts[i] !== pathParts[i]) {
      return {};
    }
  }

  return params;
}

export function matchPath(pattern: string, pathname: string): boolean {
  const patternParts = pattern.split('/').filter(Boolean);
  const pathParts = pathname.split('/').filter(Boolean);

  if (patternParts.length !== pathParts.length) return false;

  for (let i = 0; i < patternParts.length; i++) {
    if (patternParts[i].startsWith(':')) continue;
    if (patternParts[i] !== pathParts[i]) return false;
  }

  return true;
}


