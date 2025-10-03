import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const userData = req.body;

    // Проверяем и сохраняем пользователя
    const { data: existingUser, error: selectError } = await supabase
      .from('users')
      .select('*')
      .eq('telegram_id', userData.id)
      .single();

    let user;
    if (selectError && selectError.code === 'PGRST116') {
      // Пользователь не найден, создаем нового
      const { data: newUser, error: insertError } = await supabase
        .from('users')
        .insert([{
          telegram_id: userData.id,
          first_name: userData.first_name,
          last_name: userData.last_name,
          username: userData.username,
          created_at: new Date().toISOString()
        }])
        .select()
        .single();

      if (insertError) throw insertError;
      user = newUser;
    } else if (selectError) {
      throw selectError;
    } else {
      user = existingUser;
    }

    // Создаем сессию
    const sessionId = `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const { error: sessionError } = await supabase
      .from('sessions')
      .insert([{
        session_id: sessionId,
        user_id: user.id,
        created_at: new Date().toISOString()
      }]);

    if (sessionError) throw sessionError;

    res.status(200).json({
      success: true,
      sessionId,
      user: {
        id: user.id,
        telegram_id: user.telegram_id,
        first_name: user.first_name,
        last_name: user.last_name,
        username: user.username
      }
    });

  } catch (error) {
    console.error('Auth error:', error);
    res.status(500).json({
      success: false,
      error: 'Authentication failed'
    });
  }
}