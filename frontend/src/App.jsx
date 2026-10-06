import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './auth';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import ProfilePage from './pages/ProfilePage';
import ReviewPage from './pages/ReviewPage';
import EditProfilePage from './pages/EditProfilePage';
import AuthPage from './pages/AuthPage';
import { ThemeProvider } from './theme';

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Navbar />
          <Routes>
            <Route path="/"                          element={<Home />} />
            <Route path="/auth"                      element={<AuthPage />} />
            <Route path="/profile/me"                element={<ProfilePage />} />
            <Route path="/profile/create"            element={<EditProfilePage />} />
            <Route path="/profile/:id"               element={<ProfilePage />} />
            <Route path="/profile/:id/review"        element={<ReviewPage />} />
            <Route path="/profile/:id/edit"          element={<EditProfilePage />} />
            <Route path="*"                          element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

function NotFound() {
  return (
    <div className="page-wrapper">
      <div className="container">
        <div className="empty-state" style={{ paddingTop: 'var(--space-16)' }}>
          <div className="empty-state-icon">🔍</div>
          <h3>Page not found</h3>
          <p>The page you're looking for doesn't exist.</p>
          <a href="/" className="btn btn-primary" style={{ marginTop: 'var(--space-6)', display: 'inline-flex' }}>
            Go Home
          </a>
        </div>
      </div>
    </div>
  );
}
