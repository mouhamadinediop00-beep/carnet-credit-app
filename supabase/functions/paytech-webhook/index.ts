import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

serve(async (req) => {
  try {
    // 1. Récupération des données envoyées par PayTech
    const body = await req.json()
    const { custom_field, type_event } = body

    // Vérification de la validation du paiement
    if (type_event === "sale_complete" || body.status === "success") {
      const userId = custom_field // L'UUID ou l'identifiant transmis lors du paiement

      // 2. Initialisation du client Supabase (avec clé Service Role pour outrepasser les RLS)
      const supabaseAdmin = createClient(
        Deno.env.get("SUPABASE_URL") ?? "",
        Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
      )

      // 3. Calcul de la nouvelle date (+30 jours)
      const nouvelleDate = new Date()
      nouvelleDate.setDate(nouvelleDate.getDate() + 30)

      // 4. Mise à jour dans la table profiles
      const { error } = await supabaseAdmin
        .from("profiles")
        .update({ subscription_expires_at: nouvelleDate.toISOString() })
        .or(`id.eq.${userId},email.ilike.%${userId}%`)

      if (error) {
        console.error("Erreur lors de la mise à jour :", error)
        return new Response(JSON.stringify({ error: error.message }), { status: 500 })
      }

      return new Response(JSON.stringify({ message: "Abonnement prolongé de 30 jours avec succès" }), { status: 200 })
    }

    return new Response(JSON.stringify({ message: "Événement ignoré" }), { status: 200 })
  } catch (err) {
    console.error("Erreur Webhook :", err)
    return new Response(JSON.stringify({ error: err.message }), { status: 400 })
  }
})