# 🏃‍♂️ Guide de Configuration - Coach Sport & Santé n8n

## 📋 Vue d'ensemble

Ce workflow n8n crée un coach sport et santé personnalisé pour homme de 50 ans, utilisant l'IA pour fournir des conseils adaptés, un suivi personnalisé et une motivation quotidienne.

## 🎯 Fonctionnalités Principales

### 🤖 Agent IA Coach
- Conseils personnalisés selon l'âge et condition physique
- Programmes d'entraînement adaptés aux 50 ans
- Conseils nutritionnels équilibrés
- Prévention des blessures
- Motivation quotidienne

### ⏰ Automatisations
- **Motivation matinale** (8h00) : Rappels et encouragements
- **Bilan du soir** (20h00) : Suivi des progrès
- **Interactions temps réel** : Réponses via Telegram/Webhook

### 📊 Suivi & Données
- Enregistrement automatique des conversations
- Suivi des progrès dans Google Sheets
- Mémoire des conversations précédentes
- Analyse des tendances

## 🛠️ Configuration Étape par Étape

### 1. Prérequis API

#### OpenAI API
```bash
# Obtenez votre clé API sur https://platform.openai.com/
OPENAI_API_KEY=sk-...
```

#### Telegram Bot
```bash
# Créez un bot via @BotFather sur Telegram
TELEGRAM_BOT_TOKEN=123456789:ABC...
TELEGRAM_CHAT_ID=123456789
```

#### Google Sheets API
```bash
# Activez l'API Google Sheets dans Google Cloud Console
# Créez des credentials OAuth2
```

### 2. Configuration Google Sheets

Créez un Google Sheet avec les onglets suivants :

#### Onglet "Profil_Utilisateur"
| Colonne A | Colonne B | Colonne C | Colonne D |
|-----------|-----------|-----------|-----------|
| user_id | nom | age | niveau_forme |
| 123456789 | Jean | 50 | débutant |

#### Onglet "Programmes_Entrainement"
| Colonne A | Colonne B | Colonne C | Colonne D |
|-----------|-----------|-----------|-----------|
| niveau | type | exercices | duree |
| débutant | cardio | marche rapide, vélo | 30min |
| débutant | renforcement | pompes murales, squats | 20min |

#### Onglet "Conseils_Nutrition"
| Colonne A | Colonne B | Colonne C |
|-----------|-----------|-----------|
| categorie | conseil | details |
| hydratation | Boire 2L d'eau/jour | Répartir sur la journée |
| protéines | 1.2g/kg poids corps | Privilégier sources variées |

#### Onglet "Suivi_Coaching"
| Colonne A | Colonne B | Colonne C | Colonne D | Colonne E | Colonne F |
|-----------|-----------|-----------|-----------|-----------|-----------|
| date | user_id | message_user | response_coach | sentiment | category |

### 3. Configuration n8n

#### Credentials à créer :

1. **OpenAI API**
   - Nom : `openai-credentials`
   - Type : OpenAI
   - API Key : Votre clé OpenAI

2. **Telegram Bot**
   - Nom : `telegram-bot-credentials`
   - Type : Telegram
   - Access Token : Token de votre bot

3. **Google Sheets**
   - Nom : `google-sheets-credentials`
   - Type : Google Sheets OAuth2
   - Suivre le processus OAuth2

#### Variables à remplacer :

Dans le fichier JSON du workflow, remplacez :
- `VOTRE_GOOGLE_SHEET_ID` par l'ID de votre Google Sheet
- `VOTRE_TELEGRAM_CHAT_ID` par votre ID de chat Telegram

### 4. Import du Workflow

1. Copiez le contenu de `coach_sport_sante_workflow.json`
2. Dans n8n, allez dans **Workflows** > **Import from JSON**
3. Collez le JSON et importez
4. Configurez les credentials dans chaque node

## 🚀 Utilisation

### Démarrage
1. Activez le workflow dans n8n
2. Le bot enverra automatiquement :
   - Motivation matinale à 8h00
   - Bilan du soir à 20h00

### Interaction
- Envoyez un message à votre bot Telegram
- Utilisez le webhook pour intégrations externes
- Consultez Google Sheets pour le suivi

### Exemples de Questions
```
"Comment commencer un programme de sport à 50 ans ?"
"Quels exercices pour renforcer le dos ?"
"Conseils nutrition pour perdre du poids sainement ?"
"J'ai mal au genou après ma course, que faire ?"
```

## 🎨 Personnalisation

### Modifier les Horaires
Dans le node "Condition Horaire", changez :
```json
"leftValue": "08",  // Heure matinale
"leftValue": "20"   // Heure du soir
```

### Adapter les Messages
Modifiez les textes dans :
- "Motivation Matinale"
- "Bilan du Soir"
- "Message d'Accueil Telegram"

### Ajouter des Outils
Connectez d'autres nodes au port `ai_tool` de l'Agent IA :
- API météo pour adapter les conseils
- Calendrier pour planifier les séances
- Tracker de fitness pour données réelles

## 📊 Monitoring

### Métriques à Suivre
- Nombre d'interactions quotidiennes
- Types de questions les plus fréquentes
- Évolution du sentiment utilisateur
- Taux d'engagement aux rappels

### Logs
Consultez l'onglet "Suivi_Coaching" pour :
- Historique des conversations
- Analyse des tendances
- Amélioration continue

## 🔧 Dépannage

### Problèmes Courants

1. **Bot Telegram ne répond pas**
   - Vérifiez le token du bot
   - Confirmez que le workflow est activé

2. **Erreurs Google Sheets**
   - Vérifiez les permissions du sheet
   - Confirmez l'ID du document

3. **Réponses IA incohérentes**
   - Ajustez la température du modèle
   - Enrichissez les données d'entraînement

## 🎯 Évolutions Possibles

### Court Terme
- Intégration avec applications fitness (Strava, MyFitnessPal)
- Rappels personnalisés selon les préférences
- Génération de rapports hebdomadaires

### Long Terme
- Analyse vidéo des mouvements
- Intégration avec objets connectés (balance, montre)
- Coaching vocal via assistant

## 📞 Support

Pour toute question ou personnalisation :
- Consultez la documentation n8n
- Rejoignez la communauté n8n
- Adaptez selon vos besoins spécifiques

---

**🎉 Félicitations ! Votre coach sport et santé IA est prêt à vous accompagner dans votre parcours de remise en forme !**
