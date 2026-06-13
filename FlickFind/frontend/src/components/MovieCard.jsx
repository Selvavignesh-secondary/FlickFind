// src/components/MovieCard.jsx
import React, { useState } from 'react';

export default function MovieCard({ movie, onAction, isInWatchlist }) {
  const [activePanel, setActivePanel] = useState(null); // 'watched' | 'dislike' | null
  const [rating, setRating] = useState(5);
  const [review, setReview] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [customReason, setCustomReason] = useState("");

  const handleWatchedSubmit = (e) => {
    e.preventDefault();
    onAction(movie.id, "watched", { rating: parseFloat(rating), critic_review: review });
    setActivePanel(null);
    setReview("");
  };

  const handleDislikeSubmit = (e) => {
    e.preventDefault();
    const finalReason = rejectionReason === "OTHER" ? customReason : rejectionReason;
    onAction(movie.id, "dislike", { rejection_reason: finalReason || "Not interested" });
    setActivePanel(null);
    setRejectionReason("");
    setCustomReason("");
  };

  return (
    <div className="movie-card-element">
      {/* 🏗️ Row 1: Horizontal Identity (Poster Frame + Unclamped Context Data) */}
      <div className="card-top-identity-row">
        <div className="card-poster-side">
          {movie.poster_path ? (
            <img 
              src={`https://image.tmdb.org/t/p/w500${movie.poster_path}`} 
              alt={movie.title} 
              className="movie-poster-img"
              onError={(e) => { 
                e.target.src = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=300&q=80"; 
              }}
            />
          ) : (
            <div className="poster-placeholder">🎬</div>
          )}
        </div>

        <div className="card-content-side">
          <div className="card-header-row">
            <h4 className="movie-title">
              {movie.title} <span className="year">({movie.release_year})</span>
            </h4>
            <span className="rating-badge">⭐ {movie.imdb_rating || "N/A"}</span>
          </div>
          
          <p className="meta-text">⏳ {movie.runtime || "Unknown"} mins</p>
          <p className="summary-text">{movie.hybrid_summary || movie.overview}</p>
          
          <div className="studio-metadata-block">
            <div className="meta-data-node">
              <span className="label">Director</span>
              <span className="value">{movie.director || "Unknown"}</span>
            </div>
            <div className="meta-data-node">
              <span className="label">Music Composer</span>
              <span className="value">{movie.music || "Unknown"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 🏗️ Row 2: Full-Width Persistent Action Dashboards (Never hidden or clipped) */}
      {activePanel === null && (
        <div className="card-action-dashboard">
          <button 
            onClick={() => onAction(movie.id, "watchlist")} 
            className={`action-btn watchlist-btn ${isInWatchlist ? "in-watchlist" : ""}`}
          >
            {isInWatchlist ? "❌ Saved to Queue" : "⏳ Save Watchlist"}
          </button>
          <button onClick={() => setActivePanel("watched")} className="action-btn watched-btn">
            ✅ Watched It
          </button>
          <button onClick={() => setActivePanel("dislike")} className="action-btn dislike-btn">
            🚫 Not Interested
          </button>
        </div>
      )}

      {/* 📝 Full-Width Inline Input Dropdown: Watched Log Entry */}
      {activePanel === "watched" && (
        <form onSubmit={handleWatchedSubmit} className="inline-feedback-form">
          <h5>Log to Cinephile Profile History</h5>
          <div className="form-row-flex">
            <select value={rating} onChange={(e) => setRating(e.target.value)}>
              {[5, 4, 3, 2, 1].map(n => <option key={n} value={n}>{n}★</option>)}
            </select>
            <input 
              type="text"
              placeholder="Share thoughts on pacing, acting, tone match..."
              value={review}
              required
              onChange={(e) => setReview(e.target.value)}
            />
          </div>
          <div className="form-actions-row">
            <button type="submit" className="action-confirm-btn">Save Log</button>
            <button type="button" onClick={() => setActivePanel(null)} className="action-cancel-btn">Cancel</button>
          </div>
        </form>
      )}

      {/* 🚫 Full-Width Inline Input Dropdown: Mute Tuning Form */}
      {activePanel === "dislike" && (
        <form onSubmit={handleDislikeSubmit} className="inline-feedback-form">
          <h5>Mute Suggestion from Feed</h5>
          <div className="form-row-flex">
            <select value={rejectionReason} required onChange={(e) => setRejectionReason(e.target.value)}>
              <option value="">Select specific reason...</option>
              <option value="Too mainstream/commercial">Too mainstream/commercial</option>
              <option value="Not in the mood for this genre">Not in the mood for this genre</option>
              <option value="Pacing is too slow/boring">Pacing is too slow/boring</option>
              <option value="Already watched this recently">Already watched this recently</option>
              <option value="OTHER">Other reason (Specify below)...</option>
            </select>
          </div>

          {rejectionReason === "OTHER" && (
            <input 
              type="text"
              placeholder="Type your exact custom feedback reason here..."
              value={customReason}
              required
              className="custom-reason-input"
              onChange={(e) => setCustomReason(e.target.value)}
            />
          )}

          <div className="form-actions-row">
            <button type="submit" className="action-confirm-btn reject-confirm">Confirm Mute</button>
            <button type="button" onClick={() => setActivePanel(null)} className="action-cancel-btn">Cancel</button>
          </div>
        </form>
      )}
    </div>
  );
}