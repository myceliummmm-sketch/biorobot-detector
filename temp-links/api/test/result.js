import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { score, result_type, answers } = req.body;
    const sessionId = req.headers['x-session-id'];

    if (!sessionId) {
      return res.status(401).json({ error: 'Session ID required' });
    }

    // Находим пользователя по сессии
    const { data: session, error: sessionError } = await supabase
      .from('sessions')
      .select('user_id')
      .eq('session_id', sessionId)
      .single();

    if (sessionError || !session) {
      return res.status(401).json({ error: 'Invalid session' });
    }

    // Сохраняем результат теста
    const { data: result, error: insertError } = await supabase
      .from('test_results')
      .insert([{
        user_id: session.user_id,
        score: score,
        result_type: result_type,
        answers: JSON.stringify(answers),
        completed_at: new Date().toISOString()
      }])
      .select()
      .single();

    if (insertError) throw insertError;

    res.status(200).json({
      success: true,
      result_id: result.id
    });

  } catch (error) {
    console.error('Save result error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to save result'
    });
  }
}