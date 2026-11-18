# Temps de jeu PlayStation

Petite appli web (Flask + [psnawp](https://github.com/isFakeAccount/psnawp) 3.1.0) qui affiche tes temps de jeu PS4/PS5 : total, classement, recherche, filtre plateforme, export CSV. Pensée pour le téléphone (ajout à l'écran d'accueil).

## Déployer sur Render (gratuit)
1. render.com → **New → Blueprint** → choisir ce dépôt.
2. Renseigner :
   - `APP_PASSWORD` : mot de passe pour protéger la page (obligatoire si en ligne)
   - `PSN_NPSSO` : ton token, récupéré sur https://ca.account.sony.com/api/v1/ssocookie après connexion à playstation.com
3. Ouvrir l'URL sur le téléphone → Safari → Partager → « Sur l'écran d'accueil ».

Le token expire tous les ~2 mois : il suffit de le remplacer dans Render (Environment).

## En local
```bash
pip install -r requirements.txt
HOST=0.0.0.0 python app.py   # http://IP-de-l-ordi:5000 depuis le tel (même Wi-Fi)
```
