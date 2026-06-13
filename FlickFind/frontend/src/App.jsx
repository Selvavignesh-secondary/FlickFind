// src/App.jsx
import React, { useState,useEffect } from 'react';
import MovieCard from './components/MovieCard';
import WatchlistModal from './components/WatchlistModal';
import './App.css';

function App() {
  const [moodText, setMoodText] = useState("");
  const [chatHistory, setChatHistory] = useState([
    { role: "model", text: "Hey! I'm FlickFind AI. Tell me exactly what kind of movie experience or emotional vibe you're looking for tonight..." }
  ]);
  const [recommendations, setRecommendations] = useState([]);
  const [userProfile, setUserProfile] = useState({
    favorite_genres: ["sci-fi", "mystery", "thriller", "horror"],
    disliked_genres: ["romance", "comedy"],
    preferred_eras: []
  });
  const [loading, setLoading] = useState(false);

  // 🔐 Session Context Blocks
  const [currentUser, setCurrentUser] = useState(null); 
  const [authMode, setAuthMode] = useState("login"); 
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [usernameInput, setUsernameInput] = useState("");
  const [emailInput, setEmailInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [authError, setAuthError] = useState("");

  // 📁 Watchlist Sync Caches
  const [isWatchlistOpen, setIsWatchlistOpen] = useState(false);
  const [watchlistCache, setWatchlistCache] = useState([]); 

  const BACKEND_URL = "http://127.0.0.1:8000";

  // =====================================================================
  // 🔄 WATCHLIST DATABASE SYNC LIFECYCLE HOOK
  // =====================================================================
  useEffect(() => {
    const syncWatchlistOnAuth = async () => {
      if (!currentUser) return; // Stop if user logs out or session is empty

      try {
        const response = await fetch(`${BACKEND_URL}/api/v1/user/watchlist/${currentUser.user_id}`);
        if (!response.ok) throw new Error("Watchlist sync network breakdown");
        
        const persistentData = await response.json();
        setWatchlistCache(persistentData); // Sync the rich database items to the frontend cache state
      } catch (err) {
        console.error("❌ Failed to pull persistent watchlist from database:", err);
      }
    };

    syncWatchlistOnAuth();
  }, [currentUser]); // 🚀 Fires automatically the exact instant a user logs in or out

  const handleSendMood = async (e) => {
    e.preventDefault();
    if (!moodText.trim() || loading) return;

    const newUtterance = { role: "user", text: moodText };
    const updatedHistory = [...chatHistory, newUtterance];
    
    setChatHistory(updatedHistory);
    setMoodText("");
    setLoading(true);

    try {
      const url = currentUser 
        ? `${BACKEND_URL}/api/v1/recommend/mood?user_id=${currentUser.user_id}`
        : `${BACKEND_URL}/api/v1/recommend/mood`;

      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mood_text: moodText,
          chat_history: chatHistory,
          user_profile: userProfile
        })
      });

      const data = await response.json();
      setChatHistory([...updatedHistory, { role: "model", text: data.ai_followup_chat }]);
      
      if (data.is_context_sufficient && data.recommendations) {
        setRecommendations(data.recommendations);
      }
    } catch (err) {
      console.error("Discovery pipeline breakdown:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError("");
    const endpoint = authMode === "register" ? "/api/v1/auth/register" : "/api/v1/auth/login";
    
    const payload = authMode === "register" 
      ? { username: usernameInput, email: emailInput, password: passwordInput }
      : { username: usernameInput, password: passwordInput };

    try {
      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Authentication Failed");

      if (authMode === "login") {
        setCurrentUser({
          user_id: data.user_id,
          username: data.username,
          watcher_tier: data.watcher_tier
        });
        setShowAuthModal(false);
        setUsernameInput("");
        setPasswordInput("");
      } else {
        alert("Account registered successfully! Switching to sign in configuration.");
        setAuthMode("login");
      }
    } catch (err) {
      setAuthError(err.message);
    }
  };

  const handleMovieAction = async (movieId, actionType, extraData = {}) => {
    if (!currentUser) {
      setShowAuthModal(true);
      return;
    }

    const targetMovie = recommendations.find(m => m.id === movieId) || watchlistCache.find(m => m.id === movieId);

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/user/${actionType}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: currentUser.user_id,
          movie_id: movieId,
          ...extraData
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        if (actionType === "watchlist") {
          if (data.status === "added" && targetMovie) {
            setWatchlistCache(prev => [...prev, targetMovie]);
          } else {
            setWatchlistCache(prev => prev.filter(m => m.id !== movieId));
          }
        } else if (actionType === "dislike") {
          setRecommendations(prev => prev.filter(m => m.id !== movieId));
          setWatchlistCache(prev => prev.filter(m => m.id !== movieId));
        } else if (actionType === "watched") {
          if (data.updated_tier) {
            setCurrentUser(prev => ({ ...prev, watcher_tier: data.updated_tier }));
          }
          setRecommendations(prev => prev.filter(m => m.id !== movieId));
          setWatchlistCache(prev => prev.filter(m => m.id !== movieId));
        }
        alert(data.message);
      }
    } catch (err) {
      console.error("Action pipeline failed to dispatch:", err);
    }
  };

  return (
    <div className="app-container">
      <header className="main-header">
        <div className="logo-section">
          <h2>FlickFind<span className="dot">.chat</span></h2>
          {currentUser && <span className="tier-badge">{currentUser.watcher_tier}</span>}
        </div>
        <div className="auth-status-zone">
          {currentUser ? (
            <div className="user-profile-plate">
              <button className="btn-secondary watchlist-trigger" onClick={() => setIsWatchlistOpen(true)}>
                📁 View Watchlist ({watchlistCache.length})
              </button>
              <span>🍿 Welcome, <strong>{currentUser.username}</strong></span>
              <button className="btn-secondary" onClick={() => { setCurrentUser(null); setWatchlistCache([]); }}>Logout</button>
            </div>
          ) : (
            <button className="btn-primary" onClick={() => setShowAuthModal(true)}>Sign In / Register</button>
          )}
        </div>
      </header>

      <div className="main-layout">
        <aside className="sidebar-panel">
          <h3>⚙️ Taste Configuration</h3>
          <div className="input-group">
            <label>FAVORITE GENRES (COMMA SEPARATED)</label>
            <input 
              type="text" 
              value={userProfile.favorite_genres.join(', ')} 
              onChange={(e) => setUserProfile({...userProfile, favorite_genres: e.target.value.split(', ')})}
            />
          </div>
          <div className="input-group">
            <label>EXCLUDE GENRES</label>
            <input 
              type="text" 
              value={userProfile.disliked_genres.join(', ')} 
              onChange={(e) => setUserProfile({...userProfile, disliked_genres: e.target.value.split(', ')})}
            />
          </div>
        </aside>

        <main className="chat-interface">
          <div className="chat-window">
            {chatHistory.map((msg, idx) => (
              <div key={idx} className={`chat-bubble-row ${msg.role}`}>
                <div className="avatar-icon">{msg.role === "model" ? "🤖" : "👤"}</div>
                <div className="chat-bubble-text"><p>{msg.text}</p></div>
              </div>
            ))}
            {loading && (
              <div className="chat-bubble-row model">
                <div className="avatar-icon">🤖</div>
                <div className="chat-bubble-text loading-dots">Filtering lakhs of matching matrix variables...</div>
              </div>
            )}
          </div>
          <form onSubmit={handleSendMood} className="input-form-row">
            <input 
              type="text" 
              placeholder="Add layers to your mood prompt preference details here..." 
              value={moodText} 
              onChange={(e) => setMoodText(e.target.value)}
            />
            <button type="submit" className="send-btn">🚀</button>
          </form>
        </main>

        <section className="recommendations-panel">
          <h3>Recommendations Pool ({recommendations.length})</h3>
          <div className="cards-grid">
            {recommendations.map((movie) => (
              <MovieCard 
                key={movie.id} 
                movie={movie} 
                onAction={handleMovieAction} 
                isInWatchlist={watchlistCache.some(m => m.id === movie.id)} 
              />
            ))}
          </div>
        </section>
      </div>

      <WatchlistModal 
        isOpen={isWatchlistOpen}
        onClose={() => setIsWatchlistOpen(false)}
        watchlistItems={watchlistCache}
        onRemove={handleMovieAction}
      />

      {showAuthModal && (
        <div className="auth-overlay-backdrop">
          <div className="auth-modal-card">
            <h3>{authMode === "login" ? "Welcome Back to FlickFind" : "Create Cinephile Profile"}</h3>
            {authError && <div className="error-banner">{authError}</div>}
            <form onSubmit={handleAuthSubmit}>
              <div className="form-field">
                <label>Username</label>
                <input type="text" required value={usernameInput} onChange={e => setUsernameInput(e.target.value)} />
              </div>
              {authMode === "register" && (
                <div className="form-field">
                  <label>Email Address</label>
                  <input type="email" required value={emailInput} onChange={e => setEmailInput(e.target.value)} />
                </div>
              )}
              <div className="form-field">
                <label>Password</label>
                <input type="password" required value={passwordInput} onChange={e => setPasswordInput(e.target.value)} />
              </div>
              <button type="submit" className="btn-block">{authMode === "login" ? "Login" : "Sign Up"}</button>
            </form>
            <p className="toggle-auth-prompt" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>
              {authMode === "login" ? "Need an account? Sign up here" : "Already have an account? Login here"}
            </p>
            <button className="close-modal-btn" onClick={() => setShowAuthModal(false)}>Close Window</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;