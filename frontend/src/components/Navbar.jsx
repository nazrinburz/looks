import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth';
import { useTheme } from '../theme';
import './Navbar.css';

export default function Navbar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  function handleLogout() {
    logout();
    navigate('/');
  }

  function isActive(path) {
    return location.pathname === path ? 'nav-link active' : 'nav-link';
  }

  return (
    <nav className="navbar">
      <div className="container navbar-inner">
        {/* Logo */}
        <button className="navbar-logo" onClick={() => navigate('/')}>
          <span className="navbar-logo-icon">✦</span>
          <span className="navbar-logo-text">LooksApp</span>
        </button>

        {/* Nav links */}
        <div className="navbar-nav">
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          >
            <span aria-hidden="true">{theme === 'dark' ? '☀' : '☾'}</span>
          </button>
          {user ? (
            <>
              <span className="nav-username">@{user.username}</span>
              <button className={isActive('/profile/me')} onClick={() => navigate('/profile/me')}>
                My Profile
              </button>
              <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <button className={isActive('/')} onClick={() => navigate('/')}>
                Browse
              </button>
              <button className="btn btn-primary btn-sm" onClick={() => navigate('/auth')}>
                Login / Signup
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
