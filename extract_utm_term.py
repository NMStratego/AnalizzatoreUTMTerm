import csv
import re
from urllib.parse import urlparse, parse_qs
from collections import Counter

def extract_utm_term_from_url(url):
    """Estrae il valore utm_term da un URL"""
    if not url or not isinstance(url, str):
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
    rows = []
    with open('KPI - Legge3 - Lead.csv', 'r', encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rows.append(row)
    
    print(f"Totale righe nel file: {len(rows)}")
    
    # Filtra solo le righe che hanno una SORGENTE (URL)
    rows_with_url = []
    for row in rows:
        sorgente = row.get('SORGENTE', '')
        if sorgente and 'utm_term' in sorgente:
            rows_with_url.append(row)
    
    print(f"Righe con utm_term: {len(rows_with_url)}")
    
    # Estrai i parametri UTM
    rows_with_utm_term = []
    for row in rows_with_url:
        utm_term = extract_utm_term_from_url(row.get('SORGENTE', ''))
        utm_campaign = extract_campaign_name_from_url(row.get('SORGENTE', ''))
        utm_content = extract_content_name_from_url(row.get('SORGENTE', ''))
        
        if utm_term:
            row['utm_term_extracted'] = utm_term
            row['utm_campaign_extracted'] = utm_campaign
            row['utm_content_extracted'] = utm_content
            rows_with_utm_term.append(row)
    
    print(f"Righe con utm_term valido: {len(rows_with_utm_term)}")
    
    # Analizza i valori utm_term più frequenti
    utm_term_counts = Counter([row['utm_term_extracted'] for row in rows_with_utm_term])
    
    print("\n=== TOP 20 UTM_TERM PIÙ FREQUENTI ===")
    for utm_term, count in utm_term_counts.most_common(20):
        print(f"{utm_term}: {count} occorrenze")
    
    # Crea un mapping utm_term -> nome inserzione basato su utm_content
    print("\n=== MAPPING UTM_TERM -> NOME INSERZIONE ===")
    
    # Raggruppa per utm_term e prendi il utm_content più frequente per ogni utm_term
    utm_term_to_content = {}
    
    for utm_term in utm_term_counts.keys():
        if utm_term:
            content_list = [row['utm_content_extracted'] for row in rows_with_utm_term 
                           if row['utm_term_extracted'] == utm_term and row.get('utm_content_extracted')]
            if content_list:
                content_counts = Counter(content_list)
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
    
    # Ordina per numero di lead
    results.sort(key=lambda x: x['numero_lead'], reverse=True)
    
    # Salva in CSV
    with open('utm_term_inserzioni.csv', 'w', newline='', encoding='utf-8-sig') as csvfile:
        if results:
            fieldnames = results[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    
    print(f"\nRisultati salvati in 'utm_term_inserzioni.csv'")
    print(f"Totale inserzioni uniche identificate: {len(results)}")
    
    # Mostra i primi 10 risultati
    print("\n=== PRIME 10 INSERZIONI PER NUMERO DI LEAD ===")
    for i, row in enumerate(results[:10]):
        print(f"UTM_TERM: {row['utm_term']}")
        print(f"Nome inserzione: {row['nome_inserzione']}")
        print(f"Lead generati: {row['numero_lead']}")
        print("-" * 50)
    
    # Salva anche un file dettagliato con tutti i lead
    detailed_results = []
    for row in rows_with_utm_term:
        detailed_results.append({
            'Data': row.get('Data', ''),
            'Ora': row.get('Ora', ''),
            'Email': row.get('Email', ''),
            'UTM_Term': row.get('utm_term_extracted', ''),
            'Campagna': row.get('utm_campaign_extracted', ''),
            'Nome_Inserzione': row.get('utm_content_extracted', '')
        })
    
    with open('lead_dettagliati_con_inserzioni.csv', 'w', newline='', encoding='utf-8-sig') as csvfile:
        if detailed_results:
            fieldnames = detailed_results[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(detailed_results)
    
    print(f"\nFile dettagliato salvato in 'lead_dettagliati_con_inserzioni.csv'")

if __name__ == "__main__":
    main()