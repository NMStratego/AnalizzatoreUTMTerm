# Variabili d'ambiente per Vercel

Per configurare correttamente l'applicazione su Vercel, è necessario impostare le seguenti variabili d'ambiente nel dashboard di Vercel:

## Variabili richieste:

1. **AIRTABLE_API_KEY**
   - Valore: `patD0oILpVSAgGlXH.340137025a6213e618f73e85886219cadc77c33e93168022f89fad7224d25bd8`

2. **AIRTABLE_BASE_ID**
   - Valore: `app7QNXXGNwobUi0N`

3. **SECRET_KEY**
   - Valore: `your-secret-key-for-sessions`

4. **APP_NAME**
   - Valore: `Estrattore UTM Term`

5. **APP_VERSION**
   - Valore: `1.0.0`

## Come configurare su Vercel:

1. Vai al dashboard di Vercel
2. Seleziona il tuo progetto
3. Vai su Settings > Environment Variables
4. Aggiungi ogni variabile con il suo valore
5. Rideploya l'applicazione

## Note:
- Le variabili d'ambiente sono necessarie per l'autenticazione Airtable
- SECRET_KEY è importante per la gestione delle sessioni
- Senza queste variabili, l'app non riconoscerà gli utenti registrati