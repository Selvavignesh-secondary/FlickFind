import React, { useState } from 'react';
import { Film, Search, Sparkles, AlertCircle, Clock, Star, MessageSquare } from 'lucide-react';

function App() {
  // 🧭 State Hooks for our User Inputs and API Pipeline
  const [moodText, setMoodText] = useState('');
  const [movies, setMovies] = useState([]);
  const [aiFollowupChat, setAiFollowupChat] = useState(''); 
  const [isContextSufficient, setIsContextSufficient] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // 🔌 Async API Handler to strike our FastAPI Semantic endpoint
  const handleSemanticSearch = async (e) => {
    e.preventDefault();
    if (!moodText.trim()) return;

    setIsLoading(true);
    setErrorMessage('');
    setAiFollowupChat('');
    setMovies([]);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/recommend/mood', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mood_text: moodText }),
      });

      if (!response.ok) {
        throw new Error(`HTTP network malfunction error: ${response.status}`);
      }

      const data = await response.json();

      // Synchronized parsing matching the backend's ChattedRecommendationResponse schema contract
      setIsContextSufficient(data.is_context_sufficient);
      
      if (data.is_context_sufficient === false) {
        // Handle Gate Branch A: Prompt was too vague, populate chat follow-up prompt
        setAiFollowupChat(data.ai_followup_chat || "Could you add more specific themes or details?");
        setMovies([]);
      } else {
        // Handle Gate Branch B: Context was golden, parse high-density movie nodes
        setMovies(data.recommendations || []);
        setAiFollowupChat(data.ai_followup_chat || ''); 
      }
    } catch (error) {
      console.error('API Handshake Failure:', error);
      setErrorMessage('Could not connect to the backend server. Verify your FastAPI development container port 8000 is listening.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0c10] text-gray-100 flex flex-col px-4 sm:px-8 py-12">
      
      {/* 🎬 Header Section */}
      <header className="max-w-4xl w-full mx-auto text-center mb-12">
        <div className="inline-flex items-center gap-2 bg-[#1f2833] border border-gray-800 px-4 py-2 rounded-full text-sm text-[#66fcf1] mb-4 shadow-sm">
          <Sparkles className="w-4 h-4" />
          <span>Layer 3 Generative Reasoning Engine Active</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight mb-3 bg-gradient-to-r from-white via-gray-200 to-gray-500 bg-clip-text text-transparent">
          FlickFind<span className="text-[#66fcf1]">.ai</span>
        </h1>
        <p className="text-gray-400 text-lg max-w-xl mx-auto">
          Skip the generic keyword filtering. Type how you feel, and let high-dimensional vector math surface your next cinematic watch.
        </p>
      </header>

      {/* 🔍 Search Interactive Block */}
      <main className="max-w-4xl w-full mx-auto flex-1">
        <form onSubmit={handleSemanticSearch} className="mb-12">
          <div className="relative bg-[#1f2833] border border-gray-800 rounded-2xl p-2 flex items-center shadow-xl focus-within:border-[#66fcf1]/30 transition-all duration-200">
            <Search className="w-6 h-6 text-gray-500 ml-4 flex-shrink-0" />
            <input
              type="text"
              value={moodText}
              onChange={(e) => setMoodText(e.target.value)}
              placeholder="e.g., A gritty, neon-lit cyberpunk detective thriller with philosophical themes"
              className="w-full bg-transparent border-0 outline-none px-4 py-3 text-gray-200 placeholder-gray-600 font-medium text-base sm:text-lg focus:ring-0"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !moodText.trim()}
              className="bg-[#45f3ff] text-black font-bold px-6 py-3 rounded-xl hover:bg-opacity-90 active:scale-[0.98] disabled:opacity-40 disabled:scale-100 transition-all flex items-center gap-2 shadow-md cursor-pointer flex-shrink-0"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
              ) : (
                <span>Scan Catalog</span>
              )}
            </button>
          </div>
        </form>

        {/* ❌ System Level Error Modals */}
        {errorMessage && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl flex items-start gap-3 mb-8 max-w-2xl mx-auto text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">{errorMessage}</p>
          </div>
        )}

        {/* 🚧 Branch A UI: AI Seeks More Context Context Feedback */}
        {!isContextSufficient && aiFollowupChat && (
          <div className="bg-gray-900 border border-amber-500/30 rounded-2xl p-6 mb-8 text-gray-200 shadow-xl border-l-4 border-l-amber-500 max-w-2xl mx-auto">
            <div className="flex items-center gap-2 text-amber-400 font-bold text-sm mb-3 tracking-wide uppercase">
              <MessageSquare className="w-4 h-4 fill-current" />
              <span>Cinema Concierge Needs More Info</span>
            </div>
            <p className="text-base leading-relaxed text-gray-300 font-medium">
              "{aiFollowupChat}"
            </p>
          </div>
        )}

        {/* 🎬 Branch B UI: Semantic Matching Results Catalog Grid */}
        <div>
          {movies.length > 0 && (
            <div>
              {/* 🧠 Glowing AI Conversational Reasoning Panel */}
              {aiFollowupChat && (
                <div className="bg-gray-900 border border-indigo-500/30 rounded-2xl p-6 mb-8 text-gray-200 shadow-xl border-l-4 border-l-indigo-500">
                  <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm mb-3 tracking-wide uppercase">
                    <Sparkles className="w-4 h-4 fill-current animate-pulse" />
                    <span>FlickFind AI Analyst Breakdown</span>
                  </div>
                  <p className="text-base leading-relaxed text-gray-300 font-medium italic">
                    "{aiFollowupChat}"
                  </p>
                </div>
              )}

              <h2 className="text-sm font-semibold tracking-wider uppercase text-gray-500 mb-6 flex items-center gap-2">
                <Film className="w-4 h-4" />
                <span>Top Mathematical Matches ({movies.length})</span>
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {movies.map((movie, index) => {
                  // Resolve fallback posters utilizing standard placeholder links if missing
                  const posterSrc = movie.poster_path 
                    ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` 
                    : (movie.poster_url || "https://via.placeholder.com/500x750?text=Movie+Poster");

                  return (
                    <div 
                      key={movie.id || index} 
                      className="bg-[#1f2833] border border-gray-800 hover:border-gray-700/60 rounded-2xl overflow-hidden shadow-md transition-all duration-200 flex flex-col group"
                    >
                      {/* Integrated Movie Visual Card Segment */}
                      <img 
                        src={posterSrc} 
                        alt={movie.title}
                        className="w-full h-48 object-cover group-hover:scale-[1.01] transition-transform duration-200"
                      />
                      
                      <div className="p-6 flex flex-col flex-1">
                        <div className="flex justify-between items-start gap-4 mb-3">
                          <h3 className="text-xl font-bold text-white group-hover:text-[#66fcf1] transition-colors duration-150">
                            {movie.title}
                          </h3>
                          <div className="flex items-center gap-1 bg-yellow-500/10 text-yellow-500 font-bold px-2 py-1 rounded-md text-xs border border-yellow-500/20 flex-shrink-0">
                            <Star className="w-3 h-3 fill-current" />
                            <span>{movie.imdb_rating || 'N/A'}</span>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs font-semibold text-gray-400 mb-4">
                          <span className="text-gray-500">{movie.release_year}</span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {movie.runtime ? `${movie.runtime} mins` : 'Length N/A'}
                          </span>
                        </div>

                        {/* Synchronized with hybrid_summary reasoning data column block */}
                        <p className="text-gray-400 text-sm leading-relaxed mb-6 flex-1">
                          {movie.hybrid_summary}
                        </p>

                        <div className="pt-4 border-t border-gray-800 text-xs mt-auto">
                          <span className="text-gray-500 block mb-1 uppercase tracking-wider font-bold">Director</span>
                          <span className="text-gray-300 font-medium">{movie.director || 'Unknown Director'}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {movies.length === 0 && !isLoading && isContextSufficient && (
            <div className="text-center py-16 border border-dashed border-gray-800 rounded-2xl max-w-xl mx-auto bg-dark-surface/30">
              <Film className="w-10 h-10 text-gray-700 mx-auto mb-3" />
              <p className="text-gray-500 font-medium">Your recommendation feed is currently blank.</p>
              <p className="text-gray-600 text-xs max-w-xs mx-auto mt-1">
                Type an emotional preference prompt above to cross-reference our vector collection.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;