const TEMPLATE_TYPES = [
  { id: "event_announcement", label: "Annuncio evento" },
  { id: "lineup_followup",   label: "Follow-up lineup" },
  { id: "early_bird_ending", label: "Fine Early Bird" },
  { id: "late_bird_start",   label: "Inizio Late Bird" },
]

const PRODUCTION_BASE_URL   = "https://musiconnectingpeople.com"
const DEFAULT_LOGO_URL      = `${PRODUCTION_BASE_URL}/logo_white.png`
const FOOTER_LOGO_URL       = `${PRODUCTION_BASE_URL}/secondaryLogoWhite.png`
const DEFAULT_UNSUBSCRIBE   = "{{unsubscribe_link}}"
const DEFAULT_NAME          = "{{firstname}}"
const HTTP_URL_RE           = /^https?:\/\//i

function esc(v) {
  return String(v ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
}

function toLineupArray(lineup) {
  if (Array.isArray(lineup)) return lineup.filter(Boolean).map((v) => String(v).trim()).filter(Boolean)
  if (typeof lineup === "string")
    return lineup.split(/[,\n]/g).map((v) => v.trim()).filter(Boolean)
  return []
}

function normalizeImageUrl(value) {
  const raw = String(value ?? "").trim()
  return HTTP_URL_RE.test(raw) ? raw : ""
}

/** Derive the public event URL from the event object */
export function getEventPublicUrl(event) {
  const slug = event?.slug || event?.id
  if (!slug) return ""
  return `${PRODUCTION_BASE_URL}/events/${slug}`
}

function templateCopy(type, eventTitle, eventDate) {
  switch (type) {
    case "lineup_followup":
      return {
        subject: `Lineup reveal: ${eventTitle}`,
        eyebrow: "Lineup Reveal",
        heading: `La lineup di\n${eventTitle}`,
        intro: `Ciao ${DEFAULT_NAME}, la lineup ufficiale è qui. Gli artisti sono pronti — sei pronto anche tu?`,
        extra: "Scopri chi si esibirà e prendi il tuo posto prima che sia tardi.",
        cta: "Scopri la lineup completa",
      }
    case "early_bird_ending":
      return {
        subject: `⏳ Ultime ore Early Bird — ${eventTitle}`,
        eyebrow: "Early Bird in Scadenza",
        heading: `Ultime ore\nal prezzo ridotto`,
        intro: `Ciao ${DEFAULT_NAME}, hai ancora poche ore per assicurarti il biglietto Early Bird.`,
        extra: `L'evento è in programma il ${eventDate}. Dopo la scadenza il prezzo aumenta.`,
        cta: "Blocca il tuo Early Bird",
      }
    case "late_bird_start":
      return {
        subject: `Late Bird aperti — ${eventTitle}`,
        eyebrow: "Late Bird Disponibili",
        heading: `I biglietti\nsono tornati`,
        intro: `Ciao ${DEFAULT_NAME}, i Late Bird per ${eventTitle} sono ufficialmente aperti.`,
        extra: `L'evento è in programma il ${eventDate}. I posti sono limitati — non aspettare.`,
        cta: "Acquista il tuo biglietto",
      }
    case "event_announcement":
    default:
      return {
        subject: `Nuovo evento MCP — ${eventTitle}`,
        eyebrow: "Nuovo Evento",
        heading: `${eventTitle}`,
        intro: `Ciao ${DEFAULT_NAME}, abbiamo appena annunciato un nuovo evento MCP.`,
        extra: `Segnati la data: ${eventDate}. Tutti i dettagli sono alla pagina dell'evento.`,
        cta: "Scopri l'evento",
      }
  }
}

function lineupSection(lineupItems, includeFallback = false) {
  if (!lineupItems.length) {
    if (!includeFallback) return ""
    return `
      <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:28px 0 0;">
        <tr>
          <td style="padding-bottom:10px;">
            <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:10px;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;">Lineup</span>
          </td>
        </tr>
        <tr>
          <td>
            <p style="margin:0;color:#aaaaaa;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;line-height:1.6;">{{event_lineup}}</p>
          </td>
        </tr>
      </table>
    `
  }

  const pills = lineupItems.map((artist) =>
    `<span style="display:inline-block;background:#1c1c1c;border:1px solid #2e2e2e;color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:13px;font-weight:600;letter-spacing:0.01em;padding:8px 16px;border-radius:100px;margin:4px 4px 4px 0;">${esc(artist)}</span>`
  ).join("")

  return `
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:28px 0 0;">
      <tr>
        <td style="padding-bottom:12px;">
          <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:10px;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;">Lineup</span>
        </td>
      </tr>
      <tr>
        <td style="line-height:0;">${pills}</td>
      </tr>
    </table>
  `
}

export function getEventTemplateTypes() {
  return TEMPLATE_TYPES
}

export function buildEventCampaignTemplate({
  type = "event_announcement",
  event,
  ctaUrl,
  imageUrl,
  logoUrl,
  unsubscribeUrl,
  includeLineup = true,
}) {
  const eventTitle        = esc(event?.title || "Evento MCP")
  const eventDate         = esc(event?.date  || "data da confermare")
  const resolvedImage     = normalizeImageUrl(imageUrl) || normalizeImageUrl(event?.image) || normalizeImageUrl(event?.photoPath)
  const eventImage        = esc(resolvedImage)
  const finalLogoUrl      = esc(logoUrl || DEFAULT_LOGO_URL)
  const finalCtaUrl       = esc(ctaUrl  || getEventPublicUrl(event) || "{{event_url}}")
  const finalUnsub        = esc(unsubscribeUrl || DEFAULT_UNSUBSCRIBE)
  const lineupItems       = toLineupArray(event?.lineup)
  const copy              = templateCopy(type, eventTitle, eventDate)
  const lineupHtml        = includeLineup ? lineupSection(lineupItems, type === "lineup_followup") : ""
  const headingLines      = copy.heading.split("\n").map(esc).join("<br/>")

  const heroBlock = eventImage ? `
            <!-- Hero image -->
            <tr>
              <td style="padding:0;line-height:0;font-size:0;border-left:1px solid #1e1e1e;border-right:1px solid #1e1e1e;">
                <img src="${eventImage}" alt="${eventTitle}" width="598"
                  style="width:100%;max-width:598px;height:auto;display:block;" />
              </td>
            </tr>
            <!-- Gradient fade bar below image -->
            <tr>
              <td style="background:linear-gradient(to bottom,#0e0e0e,#111111);height:16px;border-left:1px solid #1e1e1e;border-right:1px solid #1e1e1e;font-size:0;line-height:0;">&nbsp;</td>
            </tr>` : ""

  const html = `<!DOCTYPE html>
<html lang="it" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="color-scheme" content="dark" />
  <meta name="supported-color-schemes" content="dark" />
  <title>${esc(copy.subject)}</title>
  <!--[if mso]>
  <noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript>
  <![endif]-->
  <style>
    * { box-sizing:border-box; }
    body { margin:0; padding:0; background-color:#050505; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }
    img { border:0; outline:none; display:block; }
    a { text-decoration:none; }
    @media screen and (max-width:600px) {
      .outer-pad  { padding:16px 8px !important; }
      .headline   { font-size:30px !important; line-height:1.15 !important; }
      .body-pad   { padding:28px 20px 32px !important; }
      .footer-pad { padding:20px !important; }
    }
  </style>
</head>
<body style="margin:0;padding:0;background-color:#050505;">

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#050505;">
  <tr>
    <td class="outer-pad" align="center" style="padding:40px 16px 48px;">

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:598px;">

        <!-- ░░ TOP ACCENT BAR ░░ -->
        <tr>
          <td style="background:linear-gradient(90deg,#f97316 0%,#fb923c 50%,#f97316 100%);height:3px;border-radius:3px 3px 0 0;font-size:0;line-height:0;">&nbsp;</td>
        </tr>

        <!-- ░░ HEADER — Logo ░░ -->
        <tr>
          <td style="background:#0e0e0e;border-left:1px solid #1e1e1e;border-right:1px solid #1e1e1e;padding:32px 40px 28px;text-align:center;">
            <img src="${finalLogoUrl}" alt="Music Connecting People" width="150"
              style="max-width:150px;height:auto;display:inline-block;" />
          </td>
        </tr>

        ${heroBlock}

        <!-- ░░ BODY ░░ -->
        <tr>
          <td class="body-pad" style="background:#111111;border-left:1px solid #1e1e1e;border-right:1px solid #1e1e1e;padding:36px 40px 40px;">

            <!-- Eyebrow -->
            <p style="margin:0 0 18px;color:#f97316;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;">${esc(copy.eyebrow)}</p>

            <!-- Headline -->
            <h1 class="headline" style="margin:0 0 20px;color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:38px;font-weight:800;line-height:1.12;letter-spacing:-0.025em;">${headingLines}</h1>

            <!-- Intro body copy -->
            <p style="margin:0 0 24px;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">${esc(copy.intro)}</p>

            <!-- Date chip -->
            <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 20px;">
              <tr>
                <td style="background:#1a1a1a;border:1px solid #272727;border-radius:8px;padding:10px 18px;">
                  <span style="color:#f97316;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;">Data&nbsp;&nbsp;</span><span style="color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">${eventDate}</span>
                </td>
              </tr>
            </table>

            <!-- Extra copy -->
            <p style="margin:0;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">${esc(copy.extra)}</p>

            ${lineupHtml}

            <!-- Divider -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:32px 0;">
              <tr><td style="border-top:1px solid #1e1e1e;">&nbsp;</td></tr>
            </table>

            <!-- CTA Button -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td align="center">
                  <!--[if mso]>
                  <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word"
                    href="${finalCtaUrl}" style="height:52px;v-text-anchor:middle;width:400px;" arcsize="15%" strokecolor="#f97316" fillcolor="#f97316">
                    <w:anchorlock/>
                    <center style="color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;">${esc(copy.cta)} →</center>
                  </v:roundrect>
                  <![endif]-->
                  <!--[if !mso]><!-->
                  <a href="${finalCtaUrl}"
                    style="display:block;width:100%;background:#f97316;color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;letter-spacing:0.02em;text-decoration:none;text-align:center;padding:17px 32px;border-radius:8px;">
                    ${esc(copy.cta)}&nbsp;&nbsp;→
                  </a>
                  <!--<![endif]-->
                </td>
              </tr>
            </table>

          </td>
        </tr>

        <!-- ░░ FOOTER ░░ -->
        <tr>
          <td class="footer-pad" style="background:#0a0a0a;border:1px solid #1e1e1e;border-top:none;border-radius:0 0 12px 12px;padding:24px 40px;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td>
                  <p style="margin:0 0 6px;color:#3a3a3a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;line-height:1.6;">
                    Ricevi questa email perché sei iscritto alle comunicazioni di Music Connecting People.
                  </p>
                  <a href="${finalUnsub}"
                    style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;text-decoration:underline;">
                    {{unsubscribe_text}}
                  </a>
                </td>
                <td align="right" style="vertical-align:middle;">
                  <img src="${FOOTER_LOGO_URL}" alt="MCP" width="60"
                    style="max-width:60px;height:auto;opacity:0.3;" />
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>

</body>
</html>`.trim()

  const titleSuffix = String(type || "event_announcement").replace(/_/g, " ")
  return {
    title:   `${event?.title || "Evento"} — ${titleSuffix}`,
    subject: copy.subject,
    html,
  }
}
