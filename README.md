# Analizzatore UTM Term

Applicazione Flask per l'estrazione e analisi dei parametri UTM dai file CSV di lead generation.

## Funzionalità

- ✅ Upload di file CSV con colonna "SORGENTE"
- ✅ Estrazione automatica di utm_term, utm_campaign, utm_content
- ✅ Analisi e raggruppamento dei lead per inserzione
- ✅ Export di risultati in formato CSV
- ✅ Interfaccia web moderna e responsive

## Deployment su Vercel

### Prerequisiti
1. Account Vercel
2. Repository Git (GitHub, GitLab, Bitbucket)

### Passi per il deployment

1. **Carica il codice su un repository Git**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Connetti il repository a Vercel**
   - Vai su [vercel.com](https://vercel.com)
   - Clicca "New Project"
   - Importa il tuo repository
   - Vercel rileverà automaticamente che è un'app Python

3. **Configurazione automatica**
   - Vercel userà automaticamente `vercel.json` per la configurazione
   - Le dipendenze saranno installate da `requirements.txt`

4. **Deploy**
   - Clicca "Deploy"
   - L'app sarà disponibile all'URL fornito da Vercel

### File di configurazione inclusi

- `vercel.json` - Configurazione Vercel
- `requirements.txt` - Dipendenze Python
- `.gitignore` - File da escludere dal repository

## Sviluppo locale

```bash
# Installa le dipendenze
pip install -r requirements.txt

# Avvia l'applicazione
python app.py
```

L'app sarà disponibile su `http://localhost:5000`

## Struttura del progetto

```
├── app.py                 # Applicazione Flask principale
├── requirements.txt       # Dipendenze Python
├── vercel.json           # Configurazione Vercel
├── templates/            # Template HTML
│   ├── index.html
│   └── results.html
├── static/               # File statici
│   └── img/
│       └── Stratego logo official.svg
└── uploads/              # Directory per file caricati
```

---

**© 2025 Stratego Swat - Sviluppata da Nicolas Micolani**