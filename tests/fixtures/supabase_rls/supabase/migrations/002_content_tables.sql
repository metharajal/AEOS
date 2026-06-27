-- Test fixture: content tables with various RLS patterns

-- notifications: INSERT too permissive (no WITH CHECK on user_id)
CREATE TABLE IF NOT EXISTS public.notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  title text,
  message text,
  read boolean DEFAULT false
);

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "notifications_select_own"
  ON public.notifications
  FOR SELECT
  USING (auth.uid() = user_id);

-- Intentionally missing WITH CHECK — risk detector should flag this
CREATE POLICY "notifications_insert_auth"
  ON public.notifications
  FOR INSERT
  WITH CHECK (auth.uid() IS NOT NULL);

-- personnel: sensitive table with over-permissive SELECT
CREATE TABLE IF NOT EXISTS public.personnel (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  commune_id uuid,
  full_name text,
  phone text,
  email text
);

ALTER TABLE public.personnel ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.personnel FORCE ROW LEVEL SECURITY;

-- This exposes sensitive fields (phone, email) to all auth users
CREATE POLICY "personnel_select_all_auth"
  ON public.personnel
  FOR SELECT
  USING (auth.uid() IS NOT NULL);

CREATE POLICY "personnel_manage_agents"
  ON public.personnel
  FOR ALL
  USING (public.has_role(auth.uid(), 'agent'::app_role));

-- forum_posts: no DELETE policy (moderatable table)
CREATE TABLE IF NOT EXISTS public.forum_posts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  forum_id uuid,
  user_id uuid NOT NULL,
  content text,
  commune_id uuid
);

ALTER TABLE public.forum_posts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "forum_posts_select_all"
  ON public.forum_posts
  FOR SELECT
  USING (true);

-- Commune-scoped insert — makes _schema_has_tenant_columns = True
CREATE POLICY "forum_posts_insert_own"
  ON public.forum_posts
  FOR INSERT
  WITH CHECK (auth.uid() = user_id AND commune_id IS NOT NULL);

-- No DELETE policy — inspector should flag this

-- budget_projets: UPDATE without commune scope (multi-tenant schema detected)
CREATE TABLE IF NOT EXISTS public.budget_projets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  commune_id uuid,
  title text,
  status text
);

ALTER TABLE public.budget_projets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "budget_projets_select_all"
  ON public.budget_projets
  FOR SELECT
  USING (true);

CREATE POLICY "budget_projets_insert_own"
  ON public.budget_projets
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- UPDATE without commune_id scope — should be flagged MISSING_TENANT_SCOPE
CREATE POLICY "budget_projets_update_agents"
  ON public.budget_projets
  FOR UPDATE
  USING (
    public.has_role(auth.uid(), 'agent'::app_role)
    OR public.has_role(auth.uid(), 'maire'::app_role)
    OR public.has_role(auth.uid(), 'admin'::app_role)
  );
