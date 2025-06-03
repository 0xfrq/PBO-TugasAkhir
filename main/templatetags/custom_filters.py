from django import template

register = template.Library()

@register.filter
def rupiah(value):
    try:
        value = float(value)
        return f"Rp{value:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp0"
