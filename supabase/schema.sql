-- ==============================================================================
-- INDOMIEVERSE - Supabase Database Schema & Logic
-- Dialect: PostgreSQL (Supabase 15+)
-- ==============================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- 2. TABLES DEFINITION
-- ==============================================================================

-- User profile extending auth.users
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    flags JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Owned characters per user with progression level and XP
CREATE TABLE IF NOT EXISTS public.owned_characters (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    character_id TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1 CHECK (level >= 1),
    xp INTEGER NOT NULL DEFAULT 0 CHECK (xp >= 0 AND xp < 100),
    unlocked_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (user_id, character_id)
);

-- Master redeemable product codes
CREATE TABLE IF NOT EXISTS public.redeem_codes (
    code TEXT PRIMARY KEY,
    character_id TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Tracking of redeemed codes by user
CREATE TABLE IF NOT EXISTS public.used_codes (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    code TEXT NOT NULL REFERENCES public.redeem_codes(code) ON DELETE CASCADE,
    redeemed_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (user_id, code)
);

-- Chat sessions per user and character
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    character_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT 'Chat',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Chat message history
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    sender TEXT NOT NULL CHECK (sender IN ('user', 'bot')),
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Character relationship stats (affinity, trust, bond)
CREATE TABLE IF NOT EXISTS public.character_stats (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    character_id TEXT NOT NULL,
    affinity INTEGER NOT NULL DEFAULT 50 CHECK (affinity >= 0 AND affinity <= 100),
    trust INTEGER NOT NULL DEFAULT 50 CHECK (trust >= 0 AND trust <= 100),
    bond INTEGER NOT NULL DEFAULT 50 CHECK (bond >= 0 AND bond <= 100),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (user_id, character_id)
);

-- Admin system settings (AI models, endpoints, etc.)
CREATE TABLE IF NOT EXISTS public.system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- 3. DEFAULT SEED DATA
-- ==============================================================================

INSERT INTO public.redeem_codes (code, character_id, description) VALUES
    ('NOODLE-NUSA-2026', 'nusantara', 'Unlocks Nusantara character'),
    ('MYSTERY-GOLD-77',  'secret',    'Unlocks Secret Recipe character'),
    ('PEDAS-BOOST-10',   'pedas',     'Boosts Agent Pedas (+40 XP or unlock)'),
    ('ORIGINAL-WARM-01', 'original',  'Boosts Original (+40 XP or unlock)')
ON CONFLICT (code) DO NOTHING;

INSERT INTO public.system_settings (key, value) VALUES
    ('provider', 'builtin'),
    ('lm_url', 'http://localhost:1234/v1'),
    ('lm_model', ''),
    ('gm_model', 'gemini-2.5-flash'),
    ('gm_key', '')
ON CONFLICT (key) DO NOTHING;

-- ==============================================================================
-- 4. ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.owned_characters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.redeem_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.used_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.character_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_settings ENABLE ROW LEVEL SECURITY;

-- Helper function to check if current user is admin
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid() AND role = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Profiles: users can select/update their own profile; admins can view all
CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id OR public.is_admin());

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Owned characters: users manage their own characters
CREATE POLICY "Users can view their owned characters"
    ON public.owned_characters FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can modify their owned characters"
    ON public.owned_characters FOR ALL
    USING (auth.uid() = user_id);

-- Redeem codes: public can read active codes (or via RPC)
CREATE POLICY "Anyone can view active redeem codes"
    ON public.redeem_codes FOR SELECT
    USING (is_active = true);

-- Used codes: user can view their redeemed codes
CREATE POLICY "Users can view their used codes"
    ON public.used_codes FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert used codes"
    ON public.used_codes FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Chat sessions: user owns their sessions
CREATE POLICY "Users can manage their chat sessions"
    ON public.chat_sessions FOR ALL
    USING (auth.uid() = user_id);

-- Chat messages: user owns their messages
CREATE POLICY "Users can manage their chat messages"
    ON public.chat_messages FOR ALL
    USING (auth.uid() = user_id);

-- Character stats: user owns their character affinity stats
CREATE POLICY "Users can manage their character stats"
    ON public.character_stats FOR ALL
    USING (auth.uid() = user_id);

-- System settings: all authenticated users can view, only admin can update
CREATE POLICY "Authenticated users can view system settings"
    ON public.system_settings FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Admins can update system settings"
    ON public.system_settings FOR ALL
    TO authenticated
    USING (public.is_admin());

-- ==============================================================================
-- 5. TRIGGERS
-- ==============================================================================

-- Automatically create profile and grant starter characters on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    v_role TEXT := 'user';
BEGIN
    -- Check if first user or configured admin
    IF NEW.email ILIKE '%admin%' OR NEW.email ILIKE 'brilyannf@gmail.com' OR (SELECT count(*) FROM public.profiles) = 0 THEN
        v_role := 'admin';
    END IF;

    -- 1. Create profile
    INSERT INTO public.profiles (id, email, role, flags)
    VALUES (NEW.id, NEW.email, v_role, '{}'::jsonb);

    -- 2. Starter Characters: Original (Lv 4, 62 XP), Pedas (Lv 2, 30 XP)
    INSERT INTO public.owned_characters (user_id, character_id, level, xp)
    VALUES
        (NEW.id, 'original', 4, 62),
        (NEW.id, 'pedas', 2, 30);

    -- 3. Initial stats for starter characters
    INSERT INTO public.character_stats (user_id, character_id, affinity, trust, bond)
    VALUES
        (NEW.id, 'original', 50, 50, 50),
        (NEW.id, 'pedas', 50, 50, 50);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger attached to Supabase auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==============================================================================
-- 6. RPC STORED PROCEDURES (BUSINESS LOGIC)
-- ==============================================================================

-- Stored Procedure: Redeem Code
CREATE OR REPLACE FUNCTION public.redeem_code(p_code TEXT)
RETURNS JSONB AS $$
DECLARE
    v_uid UUID := auth.uid();
    v_clean_code TEXT;
    v_char_id TEXT;
    v_owned RECORD;
    v_is_duplicate BOOLEAN := false;
    v_new_lv INTEGER := 1;
    v_new_xp INTEGER := 0;
BEGIN
    IF v_uid IS NULL THEN
        RETURN jsonb_build_object('ok', false, 'error', 'Login required');
    END IF;

    v_clean_code := UPPER(TRIM(p_code));

    -- Check if code exists and is active
    SELECT character_id INTO v_char_id
    FROM public.redeem_codes
    WHERE code = v_clean_code AND is_active = true;

    IF v_char_id IS NULL THEN
        RETURN jsonb_build_object('ok', false, 'error', 'Code not recognised. Check for typos and try again.');
    END IF;

    -- Check if user already used this code
    IF EXISTS (SELECT 1 FROM public.used_codes WHERE user_id = v_uid AND code = v_clean_code) THEN
        RETURN jsonb_build_object('ok', false, 'error', 'This code was already redeemed.');
    END IF;

    -- Check if character is already owned
    SELECT * INTO v_owned
    FROM public.owned_characters
    WHERE user_id = v_uid AND character_id = v_char_id;

    IF FOUND THEN
        v_is_duplicate := true;
        v_new_lv := v_owned.level;
        v_new_xp := v_owned.xp + 40;
        IF v_new_xp >= 100 THEN
            v_new_xp := v_new_xp - 100;
            v_new_lv := v_new_lv + 1;
        END IF;

        UPDATE public.owned_characters
        SET level = v_new_lv, xp = v_new_xp
        WHERE user_id = v_uid AND character_id = v_char_id;
    ELSE
        v_is_duplicate := false;
        v_new_lv := 1;
        v_new_xp := 0;

        INSERT INTO public.owned_characters (user_id, character_id, level, xp)
        VALUES (v_uid, v_char_id, v_new_lv, v_new_xp);

        INSERT INTO public.character_stats (user_id, character_id, affinity, trust, bond)
        VALUES (v_uid, v_char_id, 50, 50, 50)
        ON CONFLICT (user_id, character_id) DO NOTHING;
    END IF;

    -- Record used code
    INSERT INTO public.used_codes (user_id, code)
    VALUES (v_uid, v_clean_code);

    RETURN jsonb_build_object(
        'ok', true,
        'characterId', v_char_id,
        'duplicate', v_is_duplicate,
        'progress', jsonb_build_array(v_new_lv, v_new_xp)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Helper to compute mood and stage based on affinity
CREATE OR REPLACE FUNCTION public.compute_stat_status(p_affinity INT)
RETURNS JSONB AS $$
DECLARE
    v_mood TEXT;
    v_stage TEXT;
BEGIN
    -- Mood calculation
    IF p_affinity >= 80 THEN v_mood := 'Delighted';
    ELSIF p_affinity >= 55 THEN v_mood := 'Warm';
    ELSIF p_affinity >= 35 THEN v_mood := 'Neutral';
    ELSE v_mood := 'Upset';
    END IF;

    -- Stage calculation
    IF p_affinity < 30 THEN v_stage := 'Stranger';
    ELSIF p_affinity < 50 THEN v_stage := 'Acquaintance';
    ELSIF p_affinity < 70 THEN v_stage := 'Friend';
    ELSIF p_affinity < 90 THEN v_stage := 'Close Friend';
    ELSE v_stage := 'Best Friend';
    END IF;

    RETURN jsonb_build_object('mood', v_mood, 'stage', v_stage);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Stored Procedure: Get Chat State
CREATE OR REPLACE FUNCTION public.get_chat_state(p_character_id TEXT, p_session_id BIGINT DEFAULT NULL)
RETURNS JSONB AS $$
DECLARE
    v_uid UUID := auth.uid();
    v_sid BIGINT := p_session_id;
    v_stats RECORD;
    v_status JSONB;
    v_sessions JSONB;
    v_messages JSONB;
    v_sess_count INT;
BEGIN
    IF v_uid IS NULL THEN
        RETURN jsonb_build_object('ok', false, 'error', 'Login required');
    END IF;

    -- Ensure session exists
    IF v_sid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public.chat_sessions WHERE id = v_sid AND user_id = v_uid AND character_id = p_character_id) THEN
        v_sid := NULL;
    END IF;

    IF v_sid IS NULL THEN
        SELECT id INTO v_sid
        FROM public.chat_sessions
        WHERE user_id = v_uid AND character_id = p_character_id
        ORDER BY id DESC LIMIT 1;

        IF v_sid IS NULL THEN
            SELECT count(*) + 1 INTO v_sess_count
            FROM public.chat_sessions
            WHERE user_id = v_uid AND character_id = p_character_id;

            INSERT INTO public.chat_sessions (user_id, character_id, title)
            VALUES (v_uid, p_character_id, 'Chat ' || v_sess_count)
            RETURNING id INTO v_sid;
        END IF;
    END IF;

    -- Fetch stats
    SELECT affinity, trust, bond INTO v_stats
    FROM public.character_stats
    WHERE user_id = v_uid AND character_id = p_character_id;

    IF NOT FOUND THEN
        v_stats.affinity := 50;
        v_stats.trust := 50;
        v_stats.bond := 50;
    END IF;

    v_status := public.compute_stat_status(v_stats.affinity);

    -- Fetch sessions
    SELECT COALESCE(jsonb_agg(jsonb_build_object('id', id, 'title', title) ORDER BY id), '[]'::jsonb)
    INTO v_sessions
    FROM public.chat_sessions
    WHERE user_id = v_uid AND character_id = p_character_id;

    -- Fetch messages
    SELECT COALESCE(jsonb_agg(jsonb_build_object('id', id, 'sender', sender, 'text', text) ORDER BY id), '[]'::jsonb)
    INTO v_messages
    FROM public.chat_messages
    WHERE session_id = v_sid;

    RETURN jsonb_build_object(
        'ok', true,
        'sessionId', v_sid,
        'stats', jsonb_build_object(
            'affinity', v_stats.affinity,
            'trust', v_stats.trust,
            'bond', v_stats.bond,
            'mood', v_status->>'mood',
            'stage', v_status->>'stage'
        ),
        'sessions', v_sessions,
        'messages', v_messages
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Stored Procedure: Save Chat Turn & Update Stats
CREATE OR REPLACE FUNCTION public.save_chat_turn(
    p_character_id TEXT,
    p_session_id BIGINT,
    p_user_message TEXT,
    p_bot_reply TEXT,
    p_affinity_delta INT[]
)
RETURNS JSONB AS $$
DECLARE
    v_uid UUID := auth.uid();
    v_sid BIGINT := p_session_id;
    v_cur_a INT;
    v_cur_t INT;
    v_cur_b INT;
    v_new_a INT;
    v_new_t INT;
    v_new_b INT;
    v_status JSONB;
    v_char RECORD;
    v_new_xp INT;
BEGIN
    IF v_uid IS NULL THEN
        RETURN jsonb_build_object('ok', false, 'error', 'Login required');
    END IF;

    -- Verify session belongs to user
    IF v_sid IS NULL OR NOT EXISTS (SELECT 1 FROM public.chat_sessions WHERE id = v_sid AND user_id = v_uid) THEN
        INSERT INTO public.chat_sessions (user_id, character_id, title)
        VALUES (v_uid, p_character_id, 'Chat')
        RETURNING id INTO v_sid;
    END IF;

    -- Insert user & bot messages
    INSERT INTO public.chat_messages (session_id, user_id, sender, text)
    VALUES
        (v_sid, v_uid, 'user', p_user_message),
        (v_sid, v_uid, 'bot', p_bot_reply);

    -- Get current stats
    SELECT affinity, trust, bond INTO v_cur_a, v_cur_t, v_cur_b
    FROM public.character_stats
    WHERE user_id = v_uid AND character_id = p_character_id;

    IF NOT FOUND THEN
        v_cur_a := 50; v_cur_t := 50; v_cur_b := 50;
    END IF;

    -- Apply delta (clamped between 0 and 100)
    v_new_a := GREATEST(0, LEAST(100, v_cur_a + COALESCE(p_affinity_delta[1], 1)));
    v_new_t := GREATEST(0, LEAST(100, v_cur_t + COALESCE(p_affinity_delta[2], 1)));
    v_new_b := GREATEST(0, LEAST(100, v_cur_b + COALESCE(p_affinity_delta[3], 1)));

    INSERT INTO public.character_stats (user_id, character_id, affinity, trust, bond, updated_at)
    VALUES (v_uid, p_character_id, v_new_a, v_new_t, v_new_b, now())
    ON CONFLICT (user_id, character_id) DO UPDATE
    SET affinity = v_new_a, trust = v_new_t, bond = v_new_b, updated_at = now();

    v_status := public.compute_stat_status(v_new_a);

    -- Award small XP for chatting (+5 XP, cap at 99 before leveling)
    SELECT * INTO v_char
    FROM public.owned_characters
    WHERE user_id = v_uid AND character_id = p_character_id;

    IF FOUND THEN
        v_new_xp := LEAST(99, v_char.xp + 5);
        UPDATE public.owned_characters
        SET xp = v_new_xp
        WHERE user_id = v_uid AND character_id = p_character_id;
    ELSE
        v_new_xp := 5;
    END IF;

    RETURN jsonb_build_object(
        'ok', true,
        'sessionId', v_sid,
        'stats', jsonb_build_object(
            'affinity', v_new_a,
            'trust', v_new_t,
            'bond', v_new_b,
            'mood', v_status->>'mood',
            'stage', v_status->>'stage'
        ),
        'progress', jsonb_build_array(COALESCE(v_char.level, 1), v_new_xp)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Stored Procedure: Create New Session
CREATE OR REPLACE FUNCTION public.new_chat_session(p_character_id TEXT)
RETURNS JSONB AS $$
DECLARE
    v_uid UUID := auth.uid();
    v_sid BIGINT;
    v_count INT;
BEGIN
    IF v_uid IS NULL THEN RETURN jsonb_build_object('ok', false, 'error', 'Login required'); END IF;

    SELECT count(*) + 1 INTO v_count
    FROM public.chat_sessions
    WHERE user_id = v_uid AND character_id = p_character_id;

    INSERT INTO public.chat_sessions (user_id, character_id, title)
    VALUES (v_uid, p_character_id, 'Chat ' || v_count)
    RETURNING id INTO v_sid;

    RETURN public.get_chat_state(p_character_id, v_sid);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Stored Procedure: Delete Chat Session
CREATE OR REPLACE FUNCTION public.delete_chat_session(p_session_id BIGINT)
RETURNS JSONB AS $$
DECLARE
    v_uid UUID := auth.uid();
    v_char_id TEXT;
BEGIN
    IF v_uid IS NULL THEN RETURN jsonb_build_object('ok', false, 'error', 'Login required'); END IF;

    SELECT character_id INTO v_char_id
    FROM public.chat_sessions
    WHERE id = p_session_id AND user_id = v_uid;

    IF v_char_id IS NULL THEN
        RETURN jsonb_build_object('ok', false, 'error', 'Session not found');
    END IF;

    DELETE FROM public.chat_sessions WHERE id = p_session_id AND user_id = v_uid;

    RETURN public.get_chat_state(v_char_id, NULL);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Stored Procedure: Update User Flags (missions, achievements)
CREATE OR REPLACE FUNCTION public.update_user_flags(p_flags JSONB)
RETURNS JSONB AS $$
DECLARE
    v_uid UUID := auth.uid();
BEGIN
    IF v_uid IS NULL THEN RETURN jsonb_build_object('ok', false, 'error', 'Login required'); END IF;

    UPDATE public.profiles
    SET flags = p_flags, updated_at = now()
    WHERE id = v_uid;

    RETURN jsonb_build_object('ok', true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
