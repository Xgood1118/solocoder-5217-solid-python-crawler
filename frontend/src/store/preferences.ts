import { createSignal, createEffect } from 'solid-js';

const STORAGE_KEY = 'news_aggregator_preferences';

interface Preferences {
  enabledSources: string[];
  darkMode: boolean;
  favorites: string[];
}

const defaultPreferences: Preferences = {
  enabledSources: ['huxiu', '36kr', 'infoq', 'juejin'],
  darkMode: false,
  favorites: [],
};

function loadPreferences(): Preferences {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      return { ...defaultPreferences, ...JSON.parse(saved) };
    }
  } catch {
    // ignore
  }
  return { ...defaultPreferences };
}

const prefs = loadPreferences();

export const [enabledSources, setEnabledSources] = createSignal<string[]>(prefs.enabledSources);
export const [darkMode, setDarkMode] = createSignal<boolean>(prefs.darkMode);
export const [favorites, setFavorites] = createSignal<string[]>(prefs.favorites);

createEffect(() => {
  const prefs: Preferences = {
    enabledSources: enabledSources(),
    darkMode: darkMode(),
    favorites: favorites(),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
});

createEffect(() => {
  if (darkMode()) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
});

export function toggleSource(source: string) {
  const current = enabledSources();
  if (current.includes(source)) {
    setEnabledSources(current.filter(s => s !== source));
  } else {
    setEnabledSources([...current, source]);
  }
}

export function toggleFavorite(articleId: string) {
  const current = favorites();
  if (current.includes(articleId)) {
    setFavorites(current.filter(id => id !== articleId));
  } else {
    setFavorites([...current, articleId]);
  }
}

export function isFavorite(articleId: string): boolean {
  return favorites().includes(articleId);
}
