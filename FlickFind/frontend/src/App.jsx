import React, { useState } from 'react';
import { Film, Search, Sparkles, AlertCircle, Clock, Star } from 'lucide-react';

function App() {
  // 🧭 State Hooks for our User Inputs and API Pipeline
  const [moodText, setMoodText] = useState('');
  const [movies, setMovies] = useState([]);
  const [aiReasoning, setAiReasoning] = useState(''); // 🌟 FIXED: Declared missing state hook!
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // 🔌 Async API Handler to strike our FastAPI Semantic endpoint
  const handleSemanticSearch = async (e) => {
    e.preventDefault();
    if (!moodText.trim()) return;

    setIsLoading(true);
    setErrorMessage('');
    setAiReasoning(''); // Clear previous text on fresh search
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/recommend/mood', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mood_text: moodText }),
      });

      const data = await response.json();

      if (data.status === 'error' || data.status === 'failed') {
        setErrorMessage(data.message || 'The database processing engine returned a signature conflict.');
        setMovies([]);
        setAiReasoning('');
      } else {
        setMovies(data.recommendations || []);
        setAiReasoning(data.ai_reasoning || ''); // 🚀 Safely updates state now!
      }
    } catch (error) {
      console.error('API Handshake Failure:', error);
      setErrorMessage('Could not connect to the backend server. Make sure your FastAPI terminal is running on port 8000.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-bg text-gray-100 flex flex-col px-4 sm:px-8 py-12">
      
      {/* 🎬 Header Section */}
      <header className="max-w-4xl w-full mx-auto text-center mb-12">
        <div className="inline-flex items-center gap-2 bg-dark-surface border border-gray-800 px-4 py-2 rounded-full text-sm text-accent-primary mb-4 shadow-sm">
          <Sparkles className="w-4 h-4" />
          <span>Layer 3 Generative Reasoning Engine Active</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight mb-3 bg-gradient-to-r from-white via-gray-200 to-gray-500 bg-clip-text text-transparent">
          FlickFind<span className="text-accent-primary">.ai</span>
        </h1>
        <p className="text-gray-400 text-lg max-w-xl mx-auto">
          Skip the generic keyword filtering. Type how you feel, and let high-dimensional vector math surface your next cinematic watch.
        </p>
      </header>

      {/* 🔍 Search Interactive Block */}
      <main className="max-w-4xl w-full mx-auto flex-1">
        <form onSubmit={handleSemanticSearch} className="mb-12">
          <div className="relative bg-dark-surface border border-gray-800 rounded-2xl p-2 flex items-center shadow-xl focus-within:border-accent-primary/5 transition-all duration-200">
            <Search className="w-6 h-6 text-gray-500 ml-4 flex-shrink-0" />
            <input
              type="text"
              value={moodText}
              onChange={(e) => setMoodText(e.target.value)}
              placeholder="e.g., I want an intense space voyage that makes me question reality with sharp plot twists after 2010"
              className="w-full bg-transparent border-0 outline-none px-4 py-3 text-gray-200 placeholder-gray-600 font-medium text-base sm:text-lg focus:ring-0"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !moodText.trim()}
              className="bg-accent-primary text-white font-semibold px-6 py-3 rounded-xl hover:bg-opacity-90 active:scale-[0.98] disabled:opacity-40 disabled:scale-100 transition-all flex items-center gap-2 shadow-md cursor-pointer flex-shrink-0"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Scan Catalog</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* ❌ System Level Error Modals */}
        {errorMessage && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl flex items-start gap-3 mb-8 max-w-2xl mx-auto text-sm animate-fadeIn">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">{errorMessage}</p>
          </div>
        )}

        {/* 🎬 Semantic Matching Results Catalog Grid */}
        <div>
          {movies.length > 0 ? (
            <div>
              <h2 className="text-sm font-semibold tracking-wider uppercase text-gray-500 mb-6 flex items-center gap-2">
                <Film className="w-4 h-4" />
                <span>Top Mathematical Matches ({movies.length})</span>
              </h2>

              {/* 🧠 Glowing AI Conversational Reasoning Panel */}
              {aiReasoning && (
                <div className="bg-gray-900 border border-indigo-500/30 rounded-2xl p-6 mb-8 text-gray-200 shadow-xl border-l-4 border-l-indigo-500">
                  <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm mb-3 tracking-wide uppercase">
                    <Sparkles className="w-4 h-4 fill-current animate-pulse" />
                    <span>FlickFind AI Analyst Breakdown</span>
                  </div>
                  <p className="text-base leading-relaxed text-gray-300 font-medium italic">
                    "{aiReasoning}"
                  </p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {movies.map((movie) => (
                  <div 
                    key={movie.id} 
                    className="bg-dark-surface border border-gray-800 hover:border-gray-700/60 rounded-2xl p-6 shadow-md transition-all duration-200 flex flex-col group animate-slideUp"
                  >
                    <div className="flex justify-between items-start gap-4 mb-3">
                      <h3 className="text-xl font-bold text-white group-hover:text-accent-primary transition-colors duration-150">
                        {movie.title}
                      </h3>
                      <div className="flex items-center gap-1 bg-yellow-500/10 text-yellow-500 font-bold px-2 py-1 rounded-md text-xs border border-yellow-500/20 flex-shrink-0">
                        <Star className="w-3 h-3 fill-current" />
                        <span>{movie.imdb_rating}</span>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs font-semibold text-gray-400 mb-4">
                      <span className="text-gray-500">{movie.release_year}</span>
                      <span>{movie.age_rating || 'Not Rated'}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {movie.runtime} mins
                      </span>
                    </div>

                    <p className="text-gray-400 text-sm leading-relaxed mb-6 flex-1 line-clamp-4">
                      {movie.synopsis}
                    </p>

                    <div className="pt-4 border-t border-gray-800 text-xs">
                      <span className="text-gray-500 block mb-1 uppercase tracking-wider font-bold">Director</span>
                      <span className="text-gray-300 font-medium">{movie.director}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            !isLoading && (
              <div className="text-center py-16 border border-dashed border-gray-800 rounded-2xl max-w-xl mx-auto bg-dark-surface/30">
                <Film className="w-10 h-10 text-gray-700 mx-auto mb-3" />
                <p className="text-gray-500 font-medium">Your recommendation feed is currently blank.</p>
                <p className="text-gray-600 text-xs max-w-xs mx-auto mt-1">
                  Type an emotional preference prompt above to cross-reference our vector collection.
                </p>
              </div>
            )
          )}
        </div>
      </main>
    </div>
  );
}

export default App;