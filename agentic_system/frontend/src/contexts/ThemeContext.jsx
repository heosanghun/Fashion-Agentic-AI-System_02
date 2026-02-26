import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext({ theme: 'light', setTheme: () => {} });

const STORAGE_KEY = 'fashion-ai-theme';

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => {
    if (typeof window === 'undefined') return 'light';
    return window.localStorage.getItem(STORAGE_KEY) || 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    window.localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = (next) => {
    setThemeState((prev) => (next === 'dark' ? 'dark' : 'light'));
  };

  const toggleTheme = () => {
    setThemeState((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
