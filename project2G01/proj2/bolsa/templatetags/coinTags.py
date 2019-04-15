from django import template
from bolsa.utils import queryDB, coinSymbol, coins

register = template.Library()

@register.simple_tag()
def getCoins():
    return coins()

@register.simple_tag()
def getCoinSymbol(code):
    return coinSymbol(code)