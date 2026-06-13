// src/components/WatchlistModal.jsx
import React from 'react';

export default function WatchlistModal({ isOpen, onClose, watchlistItems, onRemove }) {
  if (!isOpen) return null;

  return (
    <div className="auth-overlay-backdrop modal-zIndex">
      <div className="watchlist-modal-container">
        <div className="modal-header-row">
          <h3>Curated Watchlist ({watchlistItems.length})</h3>
          <button onClick={onClose} className="close-corner-x">✕</button>
        </div>
        
        <div className="watchlist-scroll-shelf">
          {watchlistItems.length === 0 ? (
            <p className="empty-state-text">Your watchlist is currently empty. Add movies while chatting with FlickFind AI!</p>
          ) : (
            watchlistItems.map((movie) => (
              <div key={movie.id} className="movie-card-element watchlist-rich-row">
                {movie.poster_path && (
                  <div className="watchlist-row-poster">
                    <img 
                      src={`https://image.tmdb.org/t/p/w200${movie.poster_path}`} 
                      alt={movie.title} 
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  </div>
                )}
                <div className="watchlist-row-content">
                  <div className="card-header-row">
                    <h4>{movie.title} <span className="year">({movie.release_year})</span></h4>
                    <span className="rating-badge">⭐ {movie.imdb_rating}</span>
                  </div>
                  <p className="meta-text">🎬 Dir: {movie.director} | ⏳ {movie.runtime} mins</p>
                  <p className="summary-text line-clamp-2">{movie.hybrid_summary}</p>
                  <button 
                    onClick={() => onRemove(movie.id, "watchlist")} 
                    className="remove-shelf-item-btn"
                  >
                    🗑️ Remove From Watchlist
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
        
        <button onClick={onClose} className="btn-block close-watchlist-btn">
          Back to Discovery Chat
        </button>
      </div>
    </div>
  );
}