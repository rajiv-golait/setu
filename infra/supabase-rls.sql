-- Optional: lock down PHI tables from direct PostgREST/anon access.
-- The SETU API is the only writer; run after supabase-schema.sql.

ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE current_truth ENABLE ROW LEVEL SECURITY;
ALTER TABLE briefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;

-- Deny all for anon + authenticated roles (API uses postgres/service connection).
DO $$
DECLARE
  t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'patients','documents','extractions','claims','current_truth',
    'briefs','summaries','shares','referrals','consents','reminders'
  ] LOOP
    EXECUTE format('CREATE POLICY deny_all_anon ON %I FOR ALL TO anon USING (false)', t);
    EXECUTE format('CREATE POLICY deny_all_authenticated ON %I FOR ALL TO authenticated USING (false)', t);
  END LOOP;
END $$;
