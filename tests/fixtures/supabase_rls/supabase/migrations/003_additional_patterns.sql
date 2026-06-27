-- Test fixture: additional RLS patterns for edge case coverage

-- table_no_rls: no RLS enabled at all
CREATE TABLE IF NOT EXISTS public.table_no_rls (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  data text
);

-- table_rls_no_policies: RLS enabled but no policies
CREATE TABLE IF NOT EXISTS public.table_rls_no_policies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  data text
);

ALTER TABLE public.table_rls_no_policies ENABLE ROW LEVEL SECURITY;

-- audit_log: uses auth.role() = 'authenticated' (overly broad)
CREATE TABLE IF NOT EXISTS public.audit_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid,
  action text,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "audit_log_insert_authenticated"
  ON public.audit_log
  FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

-- comments: another moderatable table without DELETE policy
CREATE TABLE IF NOT EXISTS public.comments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  content text
);

ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "comments_select"
  ON public.comments
  FOR SELECT
  USING (true);

CREATE POLICY "comments_insert"
  ON public.comments
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- DROP and recreate a policy (tests DROP POLICY handling)
DROP POLICY IF EXISTS "notifications_insert_auth" ON public.notifications;

CREATE POLICY "notifications_insert_self"
  ON public.notifications
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);
