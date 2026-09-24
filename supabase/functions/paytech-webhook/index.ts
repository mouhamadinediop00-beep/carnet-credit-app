import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

serve(async (req) => {
  try {
    let userId = ""

    // PayTech peut transmettre les données en JSON ou en Form-Data
    const contentType = req.headers.get("content-type") || ""

    if (contentType.includes("application/json")) {
      const body = await req.json()
      userId = body.custom_field || body.client_reference
    } else {
      const formData = await req.formData()
      userId = formData.get("custom_field")?.toString() || ""
    }

    if (!userId) {
      return new Response(JSON.stringify({ error: "ID client manquant" }), { status: 400 })
    }

    // Connexion admin Supabase
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Récupération de la date d'expiration actuelle du profil
    const { data: profile } = await supabaseAdmin
      .from('profiles')
      .select('subscription_expires_at')
      .eq('id', userId)
      .single()

    let nouvelleDate = new Date()

    // Si l'abonnement est encore en cours, on ajoute 30 jours à la date de fin
    if (profile?.subscription_expires_at) {
      const dateExpiration = new Date(profile.subscription_expires_at)
      if (dateExpiration > nouvelleDate) {
        nouvelleDate = dateExpiration
      }
    }

    // Ajout de 30 jours
    nouvelleDate.setDate(nouvelleDate.getDate() + 30)

    // Mise à jour automatique du profil client
    const { error } = await supabaseAdmin
      .from('profiles')
      .update({ subscription_expires_at: nouvelleDate.toISOString() })
      .eq('id', userId)

    if (error) throw error

    return new Response(JSON.stringify({ success: true, message: "Abonnement prolonge de 30 jours" }), {
      headers: { "Content-Type": "application/json" },
      status: 200,
    })

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), { status: 500 })
  }
})