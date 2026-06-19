// Supabase configuration for online response collection.
//
// Leave the key empty to run in LOCAL mode (responses are kept in the browser's
// localStorage and can be exported with the "Download CSV" button on the
// thank-you screen). This is what you want for local testing.
//
// To collect responses online, set your project URL and the PUBLISHABLE key
// (Project Settings -> API Keys). The publishable key (sb_publishable_...) is
// designed to be exposed in the browser; with the insert-only RLS policy and
// grant from supabase_schema.sql, participants can only append rows, never read
// or modify them.
//
// NEVER put a secret key (sb_secret_...) or legacy service_role key here -- those
// bypass RLS and must stay server-side (see export_responses.py).
window.SUPABASE_URL = "https://puquysdbjsexrlkhcirr.supabase.co";
window.SUPABASE_PUBLISHABLE_KEY = "sb_publishable_0mgxr8WYR09CIcQXBSjEXw_6st7LrmO";   // sb_publishable_...

// Legacy fallback: if you only have an old anon JWT key, you may set it here
// instead and leave PUBLISHABLE empty.
window.SUPABASE_ANON_KEY = "";
