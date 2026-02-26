import { useTheme } from '../contexts/ThemeContext';
import './ThemeToggle.css';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggleTheme}
      title={theme === 'light' ? '다크 모드로 전환' : '라이트 모드로 전환'}
      aria-label={theme === 'light' ? '다크 모드' : '라이트 모드'}
    >
      <span className="theme-toggle-icon" aria-hidden="true">
        {theme === 'light' ? '🌙' : '☀️'}
      </span>
      <span className="theme-toggle-label">
        {theme === 'light' ? '다크' : '라이트'}
      </span>
    </button>
  );
}
