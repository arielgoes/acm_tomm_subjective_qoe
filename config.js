// Supabase configuration for online response collection.
//
// Leave BOTH empty to run in LOCAL mode (responses are kept in the browser's
// localStorage and can be exported with the "Download CSV" button on the
// thank-you screen). This is what you want for local testing.
//
// To collect responses online, paste your Supabase project URL and the
// *public* anon key below. The anon key is designed to be exposed in the
// browser; with the insert-only RLS policy from supabase_schema.sql,
// participants can only append rows, never read or modify them.
window.SUPABASE_URL = "";
window.SUPABASE_ANON_KEY = "";
