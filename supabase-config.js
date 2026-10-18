/**
 * INDOMIEVERSE - Supabase Client Configuration
 * 
 * To connect to your Supabase project:
 * 1. Open Supabase Dashboard (https://supabase.com/dashboard)
 * 2. Go to Project Settings -> API
 * 3. Copy the "Project URL" and the "anon public" key
 * 4. Paste them below, or enter them directly through the Account settings in the app!
 */

window.SUPABASE_CONFIG = {
  // Replace with your Supabase Project URL:
  url: window.localStorage.getItem('iv_supabase_url') || '',
  // Replace with your Supabase Anon Public API Key:
  anonKey: window.localStorage.getItem('iv_supabase_anon_key') || ''
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
