import pandas as pd
from django.shortcuts import render
from django.utils.dateparse import parse_date
from sheetsapp.utils_google import get_sheet_df

# Nomes das colunas conforme sua planilha
COL_DATA         = "data_venda"
COL_LOJA         = "loja"
COL_GESTOR       = "gestor"
COL_COORDENACAO  = "coordenacao"      # <- NOVO filtro: Coordenação
COL_VENDEDOR     = "vendedor"
COL_PRODUTO      = "produto"
COL_STATUS       = "status_ativacao"
COL_RECEITA      = "receita"
COL_QTD          = "quantidade"

def _ensure_numeric(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.replace("R$", "", regex=False).str.strip()
    s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce").fillna(0)

def resultados_dados(request):
    try:
        # --- base completa ---
        df_full = get_sheet_df()
        df_full.columns = [str(c).strip() for c in df_full.columns]

        # conversões
        if COL_DATA in df_full.columns:
            df_full[COL_DATA] = pd.to_datetime(df_full[COL_DATA], dayfirst=True, errors="coerce").dt.date

        for c in [COL_LOJA, COL_GESTOR, COL_COORDENACAO, COL_VENDEDOR, COL_PRODUTO, COL_STATUS]:
            if c in df_full.columns:
                df_full[c] = df_full[c].astype(str).str.strip()

        if COL_RECEITA in df_full.columns:
            df_full[COL_RECEITA] = _ensure_numeric(df_full[COL_RECEITA])
        else:
            df_full[COL_RECEITA] = 0.0

        if COL_QTD in df_full.columns:
            df_full[COL_QTD] = _ensure_numeric(df_full[COL_QTD])
        else:
            df_full[COL_QTD] = 0.0

        # ------------------ FILTROS (lidos) ------------------
        data_inicio    = parse_date(request.GET.get("data_inicio") or "")
        data_fim       = parse_date(request.GET.get("data_fim") or "")
        f_loja         = (request.GET.get("loja") or "").strip()
        f_gestor       = (request.GET.get("gestor") or "").strip()
        f_coord        = (request.GET.get("coordenacao") or "").strip()   # <- NOVO
        f_vendedor     = (request.GET.get("vendedor") or "").strip()
        f_produto      = (request.GET.get("produto") or "").strip()
        f_status       = (request.GET.get("status_ativacao") or "").strip()

        # ------------------ DF para opções de SELECT ------------------
        # Só recorte por DATA -> assim escolher um filtro NÃO some as demais opções
        df_opts = df_full.copy()
        if COL_DATA in df_opts.columns:
            if data_inicio:
                df_opts = df_opts[df_opts[COL_DATA] >= data_inicio]
            if data_fim:
                df_opts = df_opts[df_opts[COL_DATA] <= data_fim]

        def opts(col):
            if col not in df_opts.columns: return []
            v = (df_opts[col].dropna().astype(str).str.strip()
                        .replace({"": None}).dropna().unique())
            return sorted(v, key=lambda x: x.lower())

        loja_opts   = opts(COL_LOJA)
        gestor_opts = opts(COL_GESTOR)
        coord_opts  = opts(COL_COORDENACAO)   # <- NOVO
        vend_opts   = opts(COL_VENDEDOR)
        prod_opts   = opts(COL_PRODUTO)
        status_opts = opts(COL_STATUS)

        # ------------------ DF para resultados ------------------
        # Aqui aplicamos TODOS os filtros selecionados
        df = df_opts.copy()
        if f_loja and COL_LOJA in df.columns:
            df = df[df[COL_LOJA].str.lower() == f_loja.lower()]
        if f_gestor and COL_GESTOR in df.columns:
            df = df[df[COL_GESTOR].str.lower() == f_gestor.lower()]
        if f_coord and COL_COORDENACAO in df.columns:
            df = df[df[COL_COORDENACAO].str.lower() == f_coord.lower()]
        if f_vendedor and COL_VENDEDOR in df.columns:
            df = df[df[COL_VENDEDOR].str.lower() == f_vendedor.lower()]
        if f_produto and COL_PRODUTO in df.columns:
            df = df[df[COL_PRODUTO].str.lower() == f_produto.lower()]
        if f_status and COL_STATUS in df.columns:
            df = df[df[COL_STATUS].str.lower() == f_status.lower()]

        # lista de produtos
        produtos = prod_opts[:] if prod_opts else []

        # Agrupar por loja
        lojas = []
        if COL_LOJA in df.columns:
            lojas_unicas = df[COL_LOJA].dropna().astype(str).str.strip().unique()
        else:
            df["_loja"] = "Geral"
            lojas_unicas = ["Geral"]

        for loja in sorted(lojas_unicas, key=lambda x: x.lower()):
            df_loja = df[df[COL_LOJA] == loja] if COL_LOJA in df.columns else df.copy()

            # Totais da loja por produto
            totais = {}
            for p in produtos:
                d = df_loja[df_loja[COL_PRODUTO] == p]
                tot_rec = float(d[COL_RECEITA].sum()) if not d.empty else 0.0
                tot_qtd = float(d[COL_QTD].sum()) if not d.empty else 0.0
                totais[p] = {"receita": tot_rec, "qtd": tot_qtd}

            # vendedor x produto
            if all(c in df_loja.columns for c in [COL_VENDEDOR, COL_PRODUTO]):
                g = (df_loja.groupby([COL_VENDEDOR, COL_PRODUTO])[[COL_RECEITA, COL_QTD]]
                           .sum().reset_index())
            else:
                g = pd.DataFrame(columns=[COL_VENDEDOR, COL_PRODUTO, COL_RECEITA, COL_QTD])

            vendedores_dict = {}
            for _, row in g.iterrows():
                vend = str(row[COL_VENDEDOR])
                prod = str(row[COL_PRODUTO])
                r = float(row[COL_RECEITA]); q = float(row[COL_QTD])
                vendedores_dict.setdefault(vend, {})
                vendedores_dict[vend].setdefault(prod, {"receita": 0.0, "qtd": 0.0})
                vendedores_dict[vend][prod]["receita"] += r
                vendedores_dict[vend][prod]["qtd"] += q

            # médias por produto (média entre vendedores)
            medias = {}
            for p in produtos:
                vals_r = []; vals_q = []
                for vend, met in vendedores_dict.items():
                    if p in met:
                        vals_r.append(met[p]["receita"])
                        vals_q.append(met[p]["qtd"])
                medias[p] = {
                    "receita": float(pd.Series(vals_r).mean()) if vals_r else 0.0,
                    "qtd": float(pd.Series(vals_q).mean()) if vals_q else 0.0,
                }

            # lista vendedores + flags
            vendedores_lista = []
            for vend in sorted(vendedores_dict.keys(), key=lambda x: x.lower()):
                row = {"vendedor": vend, "metrics": {}, "alerts": {}}
                for p in produtos:
                    met = vendedores_dict[vend].get(p, {"receita": 0.0, "qtd": 0.0})
                    rec = met["receita"]; qt = met["qtd"]
                    row["metrics"][p] = {"receita": rec, "qtd": qt}
                    row["alerts"][p] = {
                        "receita": rec < medias[p]["receita"],
                        "qtd": qt < medias[p]["qtd"],
                    }
                vendedores_lista.append(row)

            lojas.append({
                "loja": loja,
                "totais": totais,
                "medias": medias,
                "vendedores": vendedores_lista,
            })

        ctx = {
            "erro": None,
            "has_date": COL_DATA in df_full.columns,
            "data_inicio": request.GET.get("data_inicio", ""),
            "data_fim": request.GET.get("data_fim", ""),

            "loja_opts": loja_opts,
            "gestor_opts": gestor_opts,
            "coord_opts":  coord_opts,    # <- NOVO
            "vend_opts":   vend_opts,
            "prod_opts":   prod_opts,
            "status_opts": status_opts,

            "f_loja": f_loja,
            "f_gestor": f_gestor,
            "f_coordenacao": f_coord,     # <- NOVO
            "f_vendedor": f_vendedor,
            "f_produto": f_produto,
            "f_status": f_status,

            "produtos": produtos,
            "lojas": lojas,
        }
    except Exception as e:
        ctx = {
            "erro": str(e),
            "has_date": False,
            "data_inicio": "", "data_fim": "",
            "loja_opts": [], "gestor_opts": [], "coord_opts": [], "vend_opts": [], "prod_opts": [], "status_opts": [],
            "f_loja": "", "f_gestor": "", "f_coordenacao": "", "f_vendedor": "", "f_produto": "", "f_status": "",
            "produtos": [], "lojas": [],
        }

    return render(request, "resultados/dados.html", ctx)
