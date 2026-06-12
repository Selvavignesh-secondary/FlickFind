import React, { useState, useEffect, useRef } from 'react';
import { Film, Send, Sparkles, AlertCircle, Clock, Star, FilmIcon, User, Settings } from 'lucide-react';

function App() {
  // 💬 Conversational State Thread Arrays
  const [messages, setMessages] = useState([
    { role: 'model', text: "Hey! I'm FlickFind AI. Tell me exactly what kind of movie experience or emotional vibe you're looking for tonight..." }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [movies, setMovies] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // ⚙️ Persistent User Taste Profile Configs (Saved right in the browser)
  const [favoriteGenres, setFavoriteGenres] = useState(() => JSON.parse(localStorage.getItem('ff_fav_genres')) || []);
  const [dislikedGenres, setDislikedGenres] = useState(() => JSON.parse(localStorage.getItem('ff_dis_genres')) || []);
  const [preferredEras, setPreferredEras] = useState(() => JSON.parse(localStorage.getItem('ff_eras')) || ['Modern']);
  const [showSettings, setShowSettings] = useState(false);

  const chatEndRef = useRef(null);

  useEffect(() => {
    localStorage.setItem('ff_fav_genres', JSON.stringify(favoriteGenres));
    localStorage.setItem('ff_dis_genres', JSON.stringify(dislikedGenres));
    localStorage.setItem('ff_eras', JSON.stringify(preferredEras));
  }, [favoriteGenres, dislikedGenres, preferredEras]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userText = inputValue.trim();
    setInputValue('');
    setErrorMessage('');

    // Append the user's message bubble to the visible active stream layout
    const updatedHistory = [...messages, { role: 'user', text: userText }];
    setMessages(updatedHistory);
    setIsLoading(true);

    // Format request payload including background preference profile matrices
    const requestPayload = {
      mood_text: userText,
      chat_history: updatedHistory.slice(0, -1), // Everything except the very last entry
      user_profile: {
        favorite_genres: favoriteGenres,
        disliked_genres: dislikedGenres,
        preferred_eras: preferredEras,
        taste_description: ""
      }
    };

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/recommend/mood', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestPayload),
      });

      if (!response.ok) throw new Error("Backend server connectivity fault.");
      const data = await response.json();

      // Append AI response statement bubble to chat grid layout stream
      setMessages(prev => [...prev, { role: 'model', text: data.ai_followup_chat }]);
      
      if (data.is_context_sufficient && data.recommendations.length > 0) {
        setMovies(data.recommendations);
      } else {
        setMovies([]); // Keep results clear if still in conversational gathering loop
      }
    } catch (err) {
      setErrorMessage("Lost contact with backend engine container. Ensure port 8000 is listening.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0c10] text-gray-100 flex flex-col md:flex-row h-screen overflow-hidden">
      
      {/* 🛠️ LEFT SIDE PANEL: User Profile Taste Hub Preferences Settings */}
      <aside className="w-full md:w-80 bg-[#1f2833] border-b md:border-b-0 md:border-r border-gray-800 p-6 flex flex-col h-auto md:h-full overflow-y-auto flex-shrink-0">
        <div className="flex items-center gap-2 mb-6">
          <Settings className="w-5 h-5 text-[#66fcf1]" />
          <h2 className="font-bold text-lg text-white">Taste Configuration</h2>
        </div>

        <div className="space-y-6 flex-1">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">Favorite Genres (Comma Separated)</label>
            <input 
              type="text" 
              placeholder="e.g., Sci-Fi, Mystery" 
              value={favoriteGenres.join(', ')}
              onChange={(e) => setFavoriteGenres(e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
              className="w-full bg-[#0b0c10] border border-gray-800 rounded-xl px-4 py-2.5 text-sm outline-none text-gray-200 focus:border-[#66fcf1]/50 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">Exclude Genres</label>
            <input 
              type="text" 
              placeholder="e.g., Horror, Comedy" 
              value={dislikedGenres.join(', ')}
              onChange={(e) => setDislikedGenres(e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
              className="w-full bg-[#0b0c10] border border-gray-800 rounded-xl px-4 py-2.5 text-sm outline-none text-gray-200 focus:border-[#66fcf1]/50 transition-all"
            />
          </div>
        </div>
        
        <div className="mt-auto pt-6 border-t border-gray-800 text-xs text-gray-500 text-center font-medium">
          FlickFind.ai Pipeline Layer 3 Live
        </div>
      </aside>

      {/* 💬 MIDDLE PANEL: Interactive Chat Stream Timeline View */}
      <section className="flex-1 flex flex-col h-full bg-[#0b0c10] relative">
        <header className="p-4 border-b border-gray-900 bg-[#0b0c10]/80 backdrop-blur flex items-center justify-between">
          <div>
            <h1 className="font-black text-xl tracking-tight text-white">FlickFind<span className="text-[#66fcf1]">.chat</span></h1>
            <p className="text-xs text-gray-500 font-medium">Conversational Semantic Discovery Model</p>
          </div>
        </header>

        {/* Dynamic Bubble Scroller Element Window */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 max-w-3xl w-full mx-auto">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 border ${msg.role === 'user' ? 'bg-[#1f2833] border-gray-700' : 'bg-indigo-950/50 border-indigo-500/30 text-[#66fcf1]'}`}>
                {msg.role === 'user' ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
              </div>
              <div className={`p-4 rounded-2xl text-sm leading-relaxed ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none shadow-md' : 'bg-[#1f2833] border border-gray-800 text-gray-200 rounded-tl-none shadow-sm'}`}>
                {msg.text}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3 mr-auto items-center text-gray-500 text-xs font-semibold tracking-wide bg-[#1f2833]/40 border border-gray-800/50 px-4 py-2.5 rounded-full animate-pulse">
              <div className="w-3 h-3 border-2 border-gray-500 border-t-transparent rounded-full animate-spin" />
              <span>Analyzing full context window logs...</span>
            </div>
          )}
          {errorMessage && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl flex items-center gap-2 text-xs">
              <AlertCircle className="w-4 h-4" />
              <span>{errorMessage}</span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Sticky Form Entry Action Deck Base Element */}
        <div className="p-4 border-t border-gray-900 bg-[#0b0c10]">
          <form onSubmit={handleSendMessage} className="max-w-3xl w-full mx-auto relative flex items-center bg-[#1f2833] border border-gray-800 rounded-xl p-1.5 focus-within:border-[#66fcf1]/30 transition-all">
            <input 
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Add more layers to your mood prompt preference details here..."
              className="flex-1 bg-transparent border-0 outline-none px-4 py-2.5 text-sm text-gray-200 placeholder-gray-600"
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !inputValue.trim()} className="bg-[#45f3ff] hover:bg-opacity-90 active:scale-95 text-black p-2.5 rounded-lg transition-all flex items-center justify-center flex-shrink-0 disabled:opacity-30 disabled:scale-100 cursor-pointer">
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </section>

      {/* 🎬 RIGHT PANEL: Live Hydrated Movie Card Stream Recommendation Sheet */}
      <section className="w-full md:w-[32rem] bg-[#0b0c10] border-t md:border-t-0 md:border-l border-gray-900 p-6 flex flex-col h-auto md:h-full overflow-y-auto flex-shrink-0">
        <h2 className="text-sm font-bold tracking-wider uppercase text-gray-500 mb-4 flex items-center gap-2">
          <Film className="w-4 h-4 text-[#66fcf1]" />
          <span>Semantic Selections ({movies.length})</span>
        </h2>
        
        {movies.length > 0 ? (
          <div className="space-y-4">
            {movies.map((movie, index) => {
              const posterSrc = movie.poster_path 
                ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` 
                : "https://via.placeholder.com/500x750?text=No+Artwork";

              return (
                <div key={movie.id || index} className="bg-[#1f2833] border border-gray-800 rounded-xl overflow-hidden shadow-md group flex flex-col">
                  <img src={posterSrc} alt={movie.title} className="w-full h-40 object-cover" />
                  <div className="p-4 flex flex-col flex-1">
                    <div className="flex justify-between items-start gap-2 mb-2">
                      <h3 className="font-bold text-white text-base group-hover:text-[#66fcf1] transition-colors">{movie.title}</h3>
                      <div className="flex items-center gap-0.5 bg-yellow-500/10 text-yellow-500 font-bold px-1.5 py-0.5 rounded text-[10px] border border-yellow-500/20 flex-shrink-0">
                        <Star className="w-2.5 h-2.5 fill-current" />
                        <span>{movie.imdb_rating.toFixed(1)}</span>
                      </div>
                    </div>
                    <div className="flex gap-3 text-[11px] text-gray-500 mb-2 font-semibold">
                      <span>{movie.release_year}</span>
                      <span>{movie.runtime} mins</span>
                    </div>
                    <p className="text-gray-400 text-xs leading-relaxed mb-4 flex-1">{movie.hybrid_summary}</p>
                    <div className="pt-3 border-t border-gray-800 grid grid-cols-2 gap-2 text-[10px] text-gray-400">
                      <div><span className="text-gray-500 block font-bold uppercase tracking-wide mb-0.5">Director</span>{movie.director}</div>
                      <div><span className="text-gray-500 block font-bold uppercase tracking-wide mb-0.5">Music</span>{movie.music_composer}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center py-12 border border-dashed border-gray-900 rounded-2xl bg-[#1f2833]/10 px-4">
            <FilmIcon className="w-8 h-8 text-gray-800 mb-2" />
            <p className="text-gray-500 text-xs font-medium max-w-xs">Chat with the analyst concierge on the left. Once context is adequate, cards populate here.</p>
          </div>
        )}
      </section>

    </div>
  );
}

export default App;