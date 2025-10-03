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
        const { sessionId, answers, score, resultType, resultTitle, resultDescription } = req.body;

        if (!sessionId) {
            return res.status(400).json({ error: 'Session ID is required' });
        }

        // Verify session and get user ID
        const { data: session, error: sessionError } = await supabase
            .from('sessions')
            .select('id, user_id')
            .eq('session_token', sessionId)
            .single();

        if (sessionError || !session) {
            return res.status(401).json({ error: 'Invalid session' });
        }

        // Save test result
        const testResult = {
            user_id: session.user_id,
            session_id: session.id,
            answers: answers,
            score: score,
            result_type: resultType,
            result_title: resultTitle,
            result_description: resultDescription
        };

        const { data: result, error: resultError } = await supabase
            .from('test_results')
            .insert(testResult)
            .select()
            .single();

        if (resultError) {
            console.error('Test result save error:', resultError);
            return res.status(500).json({ error: 'Failed to save test result' });
        }

        res.status(200).json({
            success: true,
            resultId: result.id,
            message: 'Test result saved successfully'
        });

    } catch (error) {
        console.error('Test result API error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
};