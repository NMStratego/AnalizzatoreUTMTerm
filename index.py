from app import app

# Vercel richiede che l'applicazione Flask sia esportata come 'app'
if __name__ == '__main__':
    app.run()