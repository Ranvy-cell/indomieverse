/**
 * INDOMIEVERSE - Supabase Client Configuration
 * Connected to project: tkmfryalsieprckapsfd
 */

window.SUPABASE_CONFIG = {
  // Supabase Project URL:
  url: window.localStorage.getItem('iv_supabase_url') || 'https://tkmfryalsieprckapsfd.supabase.co',
  // Supabase Anon Public API Key:
  anonKey: window.localStorage.getItem('iv_supabase_anon_key') || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRrbWZyeWFsc2llcHJja2Fwc2ZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIzMDcwNjMsImV4cCI6MjEwNzg4MzA2M30.cp1BRIq1yyP4R8FBqmmwj-lPY8B8JcZI33kie-4Z15I'
};

// Initialize Supabase client if credentials exist and SDK is loaded
(function initSupabase() {
  if (window.supabase && window.supabase.createClient && window.SUPABASE_CONFIG.url && window.SUPABASE_CONFIG.anonKey) {
    try {
      window.sbClient = window.supabase.createClient(window.SUPABASE_CONFIG.url, window.SUPABASE_CONFIG.anonKey, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true
        }
      });
      console.log('[Supabase] Initialized successfully with project:', window.SUPABASE_CONFIG.url);
    } catch (err) {
      console.error('[Supabase] Initialization error:', err);
    }
  } else {
    window.sbClient = null;
  }
})();
