// Edge Function : renvoie UNIQUEMENT la date d'expiration de l'abonnement d'un utilisateur.
// Elle remplace la lecture directe de la table profiles par l'application, ce qui permet de
// supprimer la regle publique "Lecture public profiles" (etape 2 de la securisation).
//
// Deploiement (la verification JWT reste ACTIVEE, c'est le reglage par defaut : l'app envoie
// la cle publique "anon" dans l'en-tete Authorization) :
//     supabase functions deploy get-subscription
//   ou tableau de bord : Edge Functions > Deploy a new function > nom exact : get-subscription
//
// Test depuis PowerShell (remplacer CLE_ANON et UUID_UTILISATEUR) :
//   $h = @{ "Authorization"="Bearer CLE_ANON"; "apikey"="CLE_ANON"; "Content-Type"="application/json" }
//   Invoke-RestMethod -Method Post -Headers $h -Body '{"user_id":"UUID_UTILISATEUR"}' `
//     -Uri "https://ofmigkoamxqvfmthxcpa.supabase.co/functions/v1/get-subscription"
//   Reponse attendue : { "expires_at": "2026-10-08T12:00:00+00:00" }

import { createClient } from "npm:@supabase/supabase-js@2";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);

  let userId = "";
  try {
    const body = await req.json();
    userId = String(body?.user_id ?? "").trim();
  } catch {
    return json({ error: "JSON invalide" }, 400);
  }
  if (!UUID_RE.test(userId)) return json({ error: "user_id invalide" }, 400);

  const admin = createClient(
    Deno.env.get("SUPABASE_URL") ?? "",
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
  );

  const { data, error } = await admin
    .from("profiles")
    .select("subscription_expires_at, expiration_date")
    .eq("id", userId)
    .maybeSingle();

  if (error) {
    console.error("Erreur lecture profiles", error);
    return json({ error: "Erreur interne" }, 500);
  }

  // Meme regle que l'ancien verificateur : subscription_expires_at en priorite, sinon expiration_date
  const expiresAt = data?.subscription_expires_at || data?.expiration_date || null;
  return json({ expires_at: expiresAt });
});
