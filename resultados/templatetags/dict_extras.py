from django import template

register = template.Library()

@register.filter
def get_item(d, k):
    """
    Uso: {{ meu_dict|get_item:chave }}
    Retorna d[k] se existir; senão, "".
    """
    try:
        return d.get(k, "")
    except Exception:
        return ""

@register.filter
def default0(v):
    """
    Converte None/"" para 0 (útil antes de floatformat).
    """
    try:
        if v in (None, ""):
            return 0
        return v
    except Exception:
        return 0
