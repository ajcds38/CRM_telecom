from django.shortcuts import render
from .utils_google import get_sheet_df

def dados_view(request):
    try:
        df = get_sheet_df()
        colunas = list(df.columns)
        registros = df.to_dict(orient="records")
        ctx = {"colunas": colunas, "registros": registros, "erro": None}
    except Exception as e:
        ctx = {"colunas": [], "registros": [], "erro": str(e)}
    return render(request, "dados.html", ctx)
