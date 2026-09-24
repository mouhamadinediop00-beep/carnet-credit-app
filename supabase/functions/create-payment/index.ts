const PAYTECH_API_KEY = Deno.env.get("PAYTECH_API_KEY")!;
const PAYTECH_API_SECRET = Deno.env.get("PAYTECH_API_SECRET")!;
const PAYTECH_ENV = Deno.env.get("PAYTECH_ENV") ?? "prod";
const IPN_URL =
  Deno.env.get("PAYTECH_IPN_URL") ??
  "https://ofmigkoamxqvfmthxcpa.supabase.co/functions/v1/paytech-webhook";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);

  let userId: unknown;
  try {
    ({ user_id: userId } = await req.json());
  } catch {
    return json({ error: "JSON invalide" }, 400);
  }
  if (typeof userId !== "string" || userId.length < 8 || userId.length > 100) {
    return json({ error: "user_id invalide" }, 400);
  }

  const payload = {
    item_name: "Abonnement Carnet de Crédit (1 Mois)",
    item_price: "2000",
    currency: "XOF",
    ref_command: `SUB_${userId.slice(0, 8)}_${Date.now()}`,
    command_name: "Renouvellement Abonnement",
    ipn_url: IPN_URL,
    success_url: "https://paytech.sn",
    cancel_url: "https://paytech.sn",
    custom_field: userId,
    env: PAYTECH_ENV,
  };

  try {
    const res = await fetch("https://paytech.sn/api/payment/request-payment", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        api_key: PAYTECH_API_KEY,
        api_secret: PAYTECH_API_SECRET,
      },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.success === 1 && data.redirect_url) {
      return json({ redirect_url: data.redirect_url });
    }
    console.error("Erreur PayTech", data);
    return json({ error: "PayTech a refusé la demande" }, 502);
  } catch (e) {
    console.error("Erreur réseau PayTech", e);
    return json({ error: "Erreur réseau" }, 502);
  }
});