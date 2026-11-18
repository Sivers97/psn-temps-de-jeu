"""
PSN – Temps de jeu
Petite appli web Flask qui récupère tes temps de jeu PlayStation avec psnawp 3.1.0.

Lancement :
    pip install -r requirements.txt
    python app.py            # puis ouvre http://127.0.0.1:5000

Optionnel : export PSN_NPSSO="ton_token" pour ne pas avoir à le coller à chaque fois.
"""
from __future__ import annotations

import base64
import os
from datetime import datetime, timedelta

from flask import Flask, Response, render_template_string, request
from psnawp_api import PSNAWP
from psnawp_api.core import PSNAWPAuthenticationError, PSNAWPError

app = Flask(__name__)

# Mot de passe optionnel (indispensable si l'appli est en ligne) : export APP_PASSWORD="..."
APP_PASSWORD = os.environ.get("APP_PASSWORD")


@app.before_request
def proteger():
    if not APP_PASSWORD:
        return None
    auth = request.authorization
    if auth and auth.password == APP_PASSWORD:
        return None
    return Response("Mot de passe requis", 401, {"WWW-Authenticate": 'Basic realm="PSN"'})

PLATEFORMES = {"ps5_native_game": "PS5", "ps4_game": "PS4", "unknown": "?"}


def format_duree(d: timedelta | None) -> str:
    if not d:
        return "0 min"
    minutes = int(d.total_seconds() // 60)
    h, m = divmod(minutes, 60)
    return f"{h} h {m:02d}" if h else f"{m} min"


def format_date(dt: datetime | None) -> str:
    return dt.astimezone().strftime("%d/%m/%Y") if dt else "—"


def recuperer_stats(npsso: str) -> tuple[str, list[dict]]:
    psnawp = PSNAWP(npsso)
    moi = psnawp.me()
    jeux = []
    for t in moi.title_stats():  # pagination gérée par psnawp
        secondes = int(t.play_duration.total_seconds()) if t.play_duration else 0
        jeux.append(
            {
                "nom": t.name or t.title_id or "Inconnu",
                "image": t.image_url or "",
                "plateforme": PLATEFORMES.get(t.category.value if t.category else "unknown", "?"),
                "secondes": secondes,
                "duree": format_duree(t.play_duration),
                "sessions": t.play_count or 0,
                "premiere": format_date(t.first_played_date_time),
                "premiere_iso": t.first_played_date_time.isoformat() if t.first_played_date_time else "",
                "derniere": format_date(t.last_played_date_time),
                "derniere_iso": t.last_played_date_time.isoformat() if t.last_played_date_time else "",
            }
        )
    jeux.sort(key=lambda j: j["secondes"], reverse=True)
    return moi.online_id, jeux


@app.route("/", methods=["GET", "POST"])
def index():
    npsso = (request.form.get("npsso") or os.environ.get("PSN_NPSSO") or "").strip()
    erreur, pseudo, jeux = None, None, []

    if npsso and (request.method == "POST" or os.environ.get("PSN_NPSSO")):
        try:
            pseudo, jeux = recuperer_stats(npsso)
        except PSNAWPAuthenticationError:
            erreur = "Token NPSSO invalide ou expiré. Récupère-en un nouveau (voir l'aide ci-dessous)."
        except PSNAWPError as e:
            erreur = f"Erreur PSN : {e}"
        except Exception as e:  # noqa: BLE001
            erreur = f"Erreur inattendue : {e}"

    total = sum(j["secondes"] for j in jeux)
    return render_template_string(
        PAGE,
        erreur=erreur,
        pseudo=pseudo,
        jeux=jeux,
        total=format_duree(timedelta(seconds=total)),
        total_h=round(total / 3600),
        nb_jeux=len(jeux),
        sessions=sum(j["sessions"] for j in jeux),
        env_token=bool(os.environ.get("PSN_NPSSO")),
    )


PAGE = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mes temps de jeu PlayStation</title>
<meta name="theme-color" content="#0b0e14">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Temps PSN">
<link rel="apple-touch-icon" href="/icon.png">
<link rel="icon" href="/icon.png">
<style>
  :root { --bg:#0b0e14; --card:#141925; --line:#232a3a; --txt:#e8ecf4; --mut:#8a93a6; --acc:#2f7bff; --ps5:#e8ecf4; --ps4:#2f7bff; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; background:var(--bg); color:var(--txt); }
  .wrap { max-width:1100px; margin:0 auto; padding:24px 16px 60px; }
  h1 { font-size:1.6rem; margin:0 0 4px; } .mut { color:var(--mut); }
  form.token { display:flex; gap:8px; margin:20px 0; flex-wrap:wrap; }
  input, select { background:var(--card); color:var(--txt); border:1px solid var(--line); border-radius:10px; padding:10px 12px; font-size:.95rem; }
  input[name=npsso] { flex:1; min-width:240px; }
  button { background:var(--acc); color:#fff; border:0; border-radius:10px; padding:10px 18px; font-weight:600; cursor:pointer; }
  button.sec { background:var(--card); border:1px solid var(--line); }
  .err { background:#3a1620; border:1px solid #6b2333; padding:12px 14px; border-radius:10px; margin:16px 0; }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin:20px 0; }
  .stat { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; }
  .stat b { display:block; font-size:1.6rem; margin-top:4px; }
  .tools { display:flex; gap:8px; flex-wrap:wrap; margin:12px 0; } .tools input { flex:1; min-width:200px; }
  table { width:100%; border-collapse:collapse; background:var(--card); border-radius:14px; overflow:hidden; }
  th, td { padding:10px 12px; text-align:left; border-bottom:1px solid var(--line); font-size:.92rem; }
  th { color:var(--mut); font-weight:600; cursor:pointer; user-select:none; white-space:nowrap; }
  th:hover { color:var(--txt); } th.on::after { content:attr(data-dir); margin-left:4px; }
  td.jeu { display:flex; align-items:center; gap:10px; min-width:220px; }
  td.jeu img { width:44px; height:44px; border-radius:8px; object-fit:cover; background:#000; flex:none; }
  .bar { height:6px; background:var(--line); border-radius:3px; margin-top:6px; min-width:80px; }
  .bar i { display:block; height:100%; background:var(--acc); border-radius:3px; }
  .tag { font-size:.75rem; padding:2px 8px; border-radius:6px; border:1px solid var(--line); }
  .num { text-align:right; white-space:nowrap; }
  details { margin-top:28px; background:var(--card); border:1px solid var(--line); border-radius:14px; padding:14px 16px; }
  summary { cursor:pointer; font-weight:600; } code { background:#0b0e14; padding:2px 6px; border-radius:6px; }
  @media (max-width:700px) {
    .hide-sm { display:none; }
    .wrap { padding:calc(16px + env(safe-area-inset-top)) 12px 40px; }
    .stats { grid-template-columns:1fr 1fr; gap:8px; } .stat { padding:12px; } .stat b { font-size:1.25rem; }
    th, td { padding:9px 8px; } td.jeu { min-width:0; } td.jeu img { width:36px; height:36px; }
    input, select, button { font-size:16px; } /* évite le zoom auto sur iPhone */
  }
</style>
</head>
<body><div class="wrap">
  <h1>🎮 Mes temps de jeu PlayStation</h1>
  <div class="mut">{% if pseudo %}Compte : <b>{{ pseudo }}</b>{% else %}Colle ton token NPSSO pour charger tes stats (PS4 et PS5).{% endif %}</div>

  {% if not env_token %}
  <form class="token" method="post">
    <input name="npsso" type="password" placeholder="Token NPSSO (64 caractères)" autocomplete="off" required>
    <button type="submit">Récupérer mes temps de jeu</button>
  </form>
  {% endif %}

  {% if erreur %}<div class="err">{{ erreur }}</div>{% endif %}

  {% if jeux %}
  <div class="stats">
    <div class="stat"><span class="mut">Temps total</span><b>{{ total }}</b></div>
    <div class="stat"><span class="mut">Jeux lancés</span><b>{{ nb_jeux }}</b></div>
    <div class="stat"><span class="mut">Sessions</span><b>{{ sessions }}</b></div>
    <div class="stat"><span class="mut">Jeu n°1</span><b style="font-size:1.05rem">{{ jeux[0].nom }}</b><span class="mut">{{ jeux[0].duree }}</span></div>
  </div>

  <div class="tools">
    <input id="q" placeholder="Rechercher un jeu…">
    <select id="plat"><option value="">Toutes plateformes</option><option>PS5</option><option>PS4</option></select>
    <button class="sec" id="csv" type="button">Exporter en CSV</button>
  </div>

  <table id="t">
    <thead><tr>
      <th data-k="nom">Jeu</th>
      <th data-k="plat" class="hide-sm">Plateforme</th>
      <th data-k="sec" class="on num" data-dir="▼">Temps</th>
      <th data-k="ses" class="num hide-sm">Sessions</th>
      <th data-k="first" class="hide-sm">1ʳᵉ partie</th>
      <th data-k="last">Dernière partie</th>
    </tr></thead>
    <tbody>
    {% set max = jeux[0].secondes or 1 %}
    {% for j in jeux %}
      <tr data-nom="{{ j.nom|lower }}" data-plat="{{ j.plateforme }}" data-sec="{{ j.secondes }}" data-ses="{{ j.sessions }}"
          data-first="{{ j.premiere_iso }}" data-last="{{ j.derniere_iso }}">
        <td class="jeu">{% if j.image %}<img src="{{ j.image }}" alt="" loading="lazy">{% endif %}<span>{{ j.nom }}</span></td>
        <td class="hide-sm"><span class="tag">{{ j.plateforme }}</span></td>
        <td class="num">{{ j.duree }}<div class="bar"><i style="width:{{ (100 * j.secondes / max)|round(1) }}%"></i></div></td>
        <td class="num hide-sm">{{ j.sessions }}</td>
        <td class="hide-sm">{{ j.premiere }}</td>
        <td>{{ j.derniere }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% endif %}

  <details {% if not jeux %}open{% endif %}>
    <summary>Comment obtenir mon token NPSSO ?</summary>
    <ol>
      <li>Connecte-toi sur <a href="https://www.playstation.com" target="_blank" rel="noopener">playstation.com</a> dans ton navigateur.</li>
      <li>Dans le même navigateur, ouvre <a href="https://ca.account.sony.com/api/v1/ssocookie" target="_blank" rel="noopener">ca.account.sony.com/api/v1/ssocookie</a>.</li>
      <li>Copie la valeur de <code>"npsso"</code> (64 caractères) et colle-la ci-dessus.</li>
    </ol>
    <p class="mut">⚠️ Ce token donne accès à ton compte PSN : ne le partage jamais. Il reste uniquement sur ta machine (l'appli tourne en local) et expire au bout d'environ 2 mois.
    Seuls les jeux PS4/PS5 sont suivis par Sony (pas les jeux PS3/Vita).</p>
  </details>
</div>

<script>
(() => {
  const tb = document.querySelector('#t tbody'); if (!tb) return;
  const rows = [...tb.rows], q = document.getElementById('q'), plat = document.getElementById('plat');
  const filtre = () => { const s = q.value.toLowerCase(), p = plat.value;
    rows.forEach(r => r.hidden = !(r.dataset.nom.includes(s) && (!p || r.dataset.plat === p))); };
  q.oninput = plat.onchange = filtre;

  document.querySelectorAll('#t th').forEach(th => th.onclick = () => {
    const k = th.dataset.k, num = k === 'sec' || k === 'ses';
    const asc = th.classList.contains('on') ? th.dataset.dir === '▼' : !num;
    document.querySelectorAll('#t th').forEach(x => x.classList.remove('on'));
    th.classList.add('on'); th.dataset.dir = asc ? '▲' : '▼';
    rows.sort((a, b) => { let x = a.dataset[k], y = b.dataset[k];
      if (num) { x = +x; y = +y; } const c = x < y ? -1 : x > y ? 1 : 0; return asc ? c : -c; })
      .forEach(r => tb.appendChild(r));
  });

  document.getElementById('csv').onclick = () => {
    const esc = v => '"' + String(v).replace(/"/g, '""') + '"';
    const lignes = [['Jeu','Plateforme','Heures','Sessions','Première partie','Dernière partie'].join(';')];
    rows.filter(r => !r.hidden).forEach(r => { const d = r.dataset;
      lignes.push([esc(r.cells[0].innerText), d.plat, (d.sec / 3600).toFixed(2).replace('.', ','), d.ses,
                   d.first.slice(0, 10), d.last.slice(0, 10)].join(';')); });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['﻿' + lignes.join('\n')], { type: 'text/csv' }));
    a.download = 'temps-de-jeu-psn.csv'; a.click();
  };
})();
</script>
</body></html>"""


@app.route("/icon.png")
def icon():
    # Icône d'écran d'accueil (chrono blanc sur fond bleu PlayStation)
    return Response(base64.b64decode(ICONE_PNG), mimetype="image/png")


ICONE_PNG = "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"


if __name__ == "__main__":
    # HOST=0.0.0.0 pour y accéder depuis ton téléphone sur le même Wi-Fi
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)), debug=False)
