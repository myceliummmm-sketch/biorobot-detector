const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_ANON_KEY
);

module.exports = async (req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Credentials', true);
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
    res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const { telegramId, username, firstName, lastName, languageCode, isDemo } = req.body;

        // Handle demo/fallback mode for browser testing
        if (isDemo || !telegramId) {
            const demoUser = {
                telegram_id: Math.floor(Math.random() * 1000000) + 999999,
                username: 'demo_user',
                first_name: 'Demo',
                last_name: 'User',
                language_code: 'ru'
            };

            // Create demo user in database
            const { data: user, error: userError } = await supabase
                .from('users')
                .upsert(demoUser, { onConflict: 'telegram_id' })
                .select()
                .single();

            if (userError) {
                console.error('Demo user creation error:', userError);
                return res.status(500).json({ error: 'Failed to create demo user' });
            }

            // Create session for demo user
            const sessionToken = Math.random().toString(36).substring(2) + Date.now().toString(36);
            const { data: session, error: sessionError } = await supabase
                .from('sessions')
                .insert({
                    user_id: user.id,
                    session_token: sessionToken,
                    expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
                })
                .select()
                .single();

            if (sessionError) {
                console.error('Demo session creation error:', sessionError);
                return res.status(500).json({ error: 'Failed to create demo session' });
            }

            return res.status(200).json({
                sessionId: session.session_token,
                user: user
            });
        }

        // Handle real Telegram authentication
        if (!telegramId) {
            return res.status(400).json({ error: 'Telegram ID is required' });
        }

        // Create or update user
        const userData = {
            telegram_id: telegramId,
            username: username || null,
            first_name: firstName || null,
            last_name: lastName || null,
            language_code: languageCode || 'ru'
        };

        const { data: user, error: userError } = await supabase
            .from('users')
            .upsert(userData, { onConflict: 'telegram_id' })
            .select()
            .single();

        if (userError) {
            console.error('User creation error:', userError);
            return res.status(500).json({ error: 'Failed to create user' });
        }

        // Create session
        const sessionToken = Math.random().toString(36).substring(2) + Date.now().toString(36);
        const { data: session, error: sessionError } = await supabase
            .from('sessions')
            .insert({
                user_id: user.id,
                session_token: sessionToken,
                expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
            })
            .select()
            .single();

        if (sessionError) {
            console.error('Session creation error:', sessionError);
            return res.status(500).json({ error: 'Failed to create session' });
        }

        res.status(200).json({
            sessionId: session.session_token,
            user: user
        });

    } catch (error) {
        console.error('Auth API error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
};