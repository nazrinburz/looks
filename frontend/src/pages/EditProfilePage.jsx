import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../auth';
import './EditProfilePage.css';

export default function EditProfilePage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [bio, setBio] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [avatarError, setAvatarError] = useState('');

  // "Create profile" mode
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!user) { navigate('/auth'); return; }
    async function load() {
      const { data, error: e } = await api.get('/me/profile');
      if (e) {
        // No profile yet – switch to create mode
        setCreating(true);
      } else {
        setProfile(data);
        setBio(data.bio || '');
        setAvatarUrl(data.avatar_url || '');
      }
      setLoading(false);
    }
    load();
  }, [user, navigate]);

  async function handleSave(e) {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSaving(true);

    let result;
    if (creating) {
      result = await api.post('/profiles', { bio: bio.trim(), avatar_url: avatarUrl.trim() });
    } else {
      result = await api.patch(`/profiles/${profile.id}`, { bio: bio.trim(), avatar_url: avatarUrl.trim() });
    }

    setSaving(false);
    if (result.error) return setError(result.error);
    setSuccess(creating ? 'Profile created! Redirecting…' : 'Profile updated!');
    setCreating(false);
    setTimeout(() => navigate('/profile/me'), 1200);
  }

  function handleAvatarFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    setAvatarError('');
    if (!file.type.startsWith('image/')) {
      setAvatarError('Please choose an image file.');
      event.target.value = '';
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setAvatarError('Image must be 5 MB or smaller.');
      event.target.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') setAvatarUrl(reader.result);
    };
    reader.onerror = () => setAvatarError('Unable to read that image. Please try another file.');
    reader.readAsDataURL(file);
  }

  if (loading) {
    return (
      <div className="page-wrapper">
        <div className="page-loader"><div className="loader" /></div>
      </div>
    );
  }

  const previewAvatar = avatarUrl || `https://ui-avatars.com/api/?name=${user?.username}&background=262626&color=f5f5f5&size=300`;

  return (
    <div className="edit-page page-wrapper">
      <div className="container edit-container">
        <div className="card edit-card animate-fade-up">
          {/* Header */}
          <div className="edit-header">
            <h1 className="edit-title">
              {creating ? '✦ Create Your Profile' : '✏️ Edit Profile'}
            </h1>
            <p className="edit-subtitle">
              {creating
                ? 'Set up your profile for the community to rate.'
                : 'Update your bio and avatar.'}
            </p>
          </div>

          {error   && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <form id="edit-profile-form" onSubmit={handleSave}>
            {/* Avatar preview */}
            <div className="edit-avatar-section">
              <img
                src={previewAvatar}
                alt="Avatar preview"
                className="avatar avatar-xl"
                onError={(e) => { e.target.src = `https://ui-avatars.com/api/?name=${user?.username}&background=262626&color=f5f5f5&size=300`; }}
              />
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label" htmlFor="avatar-url">Avatar URL</label>
                <label className="btn btn-ghost btn-sm avatar-upload-label" htmlFor="avatar-file">
                  Choose picture from computer
                </label>
                <input
                  id="avatar-file"
                  type="file"
                  accept="image/*"
                  className="avatar-file-input"
                  onChange={handleAvatarFile}
                />
                <input
                  id="avatar-url"
                  type="url"
                  className="form-input"
                  placeholder="https://ui-avatars.com/api/?name=username"
                  value={avatarUrl}
                  onChange={(e) => setAvatarUrl(e.target.value)}
                />
                {avatarError && <p className="form-error">{avatarError}</p>}
                <p className="form-hint">
                  Choose an image from your computer, or paste an image URL.
                  Use an adult image you have permission to share.
                </p>
              </div>
            </div>

            {/* Bio */}
            <div className="form-group" style={{ marginTop: 'var(--space-5)' }}>
              <label className="form-label" htmlFor="profile-bio">Bio</label>
              <textarea
                id="profile-bio"
                className="form-textarea"
                placeholder="Tell the community about yourself…"
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                rows={4}
                maxLength={300}
              />
              <p className="form-hint">{bio.length} / 300</p>
            </div>

            {/* Actions */}
            <div className="edit-actions">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => navigate(creating ? '/' : '/profile/me')}
              >
                Cancel
              </button>
              <button
                id="save-profile-btn"
                type="submit"
                className="btn btn-primary"
                disabled={saving}
              >
                {saving ? 'Saving…' : creating ? 'Create Profile' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
