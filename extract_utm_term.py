import pandas as pd
import re
from urllib.parse import urlparse, parse_qs
from collections import Counter

def extract_utm_term_from_url(url):
    """Estrae il valore utm_term da un URL"""
    if pd.isna(url) or not isinstance(url, str):
        return None
    
    try:
        # Parse dell'URL
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # Estrai utm_term
        utm_term = query_params.get('utm_term', [None])[0]
        return utm_term
    except:
        return None

def extract_campaign_name_from_url(url):
    """Estrae il nome della campagna dall'URL"""
    if pd.isna(url) or not isinstance(url, str):
        return None
    
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # Estrai utm_campaign
        utm_campaign = query_params.get('utm_campaign', [None])[0]
        return utm_campaign
    except:
        return None

def extract_content_name_from_url(url):
    """Estrae il contenuto dell'inserzione dall'URL"""
    if pd.isna(url) or not isinstance(url, str):
        return None
    
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # Estrai utm_content
        utm_content = query_params.get('utm_content', [None])[0]
        return utm_content
    except:
        return None

def main():
    # Leggi il file CSV
    print("Caricamento del file CSV...")
    df = pd.read_csv('KPI - Legge3 - Lead.csv')
    
    print(f"Totale righe nel file: {len(df)}")
    
    # Filtra solo le righe che hanno una SORGENTE (URL)
    df_with_url = df[df['SORGENTE'].notna() & df['SORGENTE'].str.contains('utm_term', na=False)]
    
    print(f"Righe con utm_term: {len(df_with_url)}")
    
    # Estrai i parametri UTM
    df_with_url = df_with_url.copy()
    df_with_url['utm_term_extracted'] = df_with_url['SORGENTE'].apply(extract_utm_term_from_url)
    df_with_url['utm_campaign_extracted'] = df_with_url['SORGENTE'].apply(extract_campaign_name_from_url)
    df_with_url['utm_content_extracted'] = df_with_url['SORGENTE'].apply(extract_content_name_from_url)
    
    # Rimuovi righe senza utm_term
    df_with_utm_term = df_with_url[df_with_url['utm_term_extracted'].notna()]
    
    print(f"Righe con utm_term valido: {len(df_with_utm_term)}")
    
    # Analizza i valori utm_term più frequenti
    utm_term_counts = Counter(df_with_utm_term['utm_term_extracted'])
    
    print("\n=== TOP 20 UTM_TERM PIÙ FREQUENTI ===")
    for utm_term, count in utm_term_counts.most_common(20):
        print(f"{utm_term}: {count} occorrenze")
    
    # Crea un mapping utm_term -> nome inserzione basato su utm_content
    print("\n=== MAPPING UTM_TERM -> NOME INSERZIONE ===")
    
    # Raggruppa per utm_term e prendi il utm_content più frequente per ogni utm_term
    utm_term_to_content = {}
    
    for utm_term in utm_term_counts.keys():
        if utm_term:
            subset = df_with_utm_term[df_with_utm_term['utm_term_extracted'] == utm_term]
            content_counts = Counter(subset['utm_content_extracted'].dropna())
            if content_counts:
                most_common_content = content_counts.most_common(1)[0][0]
                utm_term_to_content[utm_term] = most_common_content
    
    # Salva i risultati in un file CSV
    results = []
    for utm_term, content in utm_term_to_content.items():
        count = utm_term_counts[utm_term]
        results.append({
            'utm_term': utm_term,
            'nome_inserzione': content,
            'numero_lead': count
        })
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('numero_lead', ascending=False)
    
    # Salva in CSV
    results_df.to_csv('utm_term_inserzioni.csv', index=False, encoding='utf-8-sig')
    
    print(f"\nRisultati salvati in 'utm_term_inserzioni.csv'")
    print(f"Totale inserzioni uniche identificate: {len(results_df)}")
    
    # Mostra i primi 10 risultati
    print("\n=== PRIME 10 INSERZIONI PER NUMERO DI LEAD ===")
    for _, row in results_df.head(10).iterrows():
        print(f"UTM_TERM: {row['utm_term']}")
        print(f"Nome inserzione: {row['nome_inserzione']}")
        print(f"Lead generati: {row['numero_lead']}")
        print("-" * 50)
    
    # Salva anche un file dettagliato con tutti i lead
    detailed_results = df_with_utm_term[['Data', 'Ora', 'Email', 'utm_term_extracted', 'utm_campaign_extracted', 'utm_content_extracted']].copy()
    detailed_results.columns = ['Data', 'Ora', 'Email', 'UTM_Term', 'Campagna', 'Nome_Inserzione']
    detailed_results.to_csv('lead_dettagliati_con_inserzioni.csv', index=False, encoding='utf-8-sig')
    
    print(f"\nFile dettagliato salvato in 'lead_dettagliati_con_inserzioni.csv'")

if __name__ == "__main__":
    main()