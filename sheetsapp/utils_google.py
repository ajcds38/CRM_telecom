import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Escopo necessário apenas para leitura
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_sheet_df():
    """Lê os dados do Google Sheets e retorna como DataFrame."""
    json_path = os.getenv("GOOGLE_SA_JSON")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    worksheet_name = os.getenv("GOOGLE_WORKSHEET", "Página1")

    if not json_path or not sheet_id:
        raise RuntimeError("Configuração ausente: GOOGLE_SA_JSON e/ou GOOGLE_SHEET_ID")

    creds = Credentials.from_service_account_file(json_path, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(worksheet_name)

    data = ws.get_all_records()  # primeira linha como cabeçalho
    df = pd.DataFrame(data)

    # Remove espaços extras nos nomes das colunas
    df.columns = [col.strip() for col in df.columns]
    return df
