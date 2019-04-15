import random
from django import template
import xmltodict
from BaseXClient import BaseXClient

register = template.Library()

@register.simple_tag
def randomInt(a, b):
    return random.randint(a, b)

@register.simple_tag()
def multiply(qty, unit_price, *args, **kwargs):
    # you would need to do any localization of the result here
    return int(qty) * float(unit_price)

@register.simple_tag()
def multiplyDouble(qty, unit_price, *args, **kwargs):
    # you would need to do any localization of the result here
    return round(float(qty) * float(unit_price), 2)

@register.simple_tag()
def multiplyTriple(a, b, c, *args, **kwargs):
    # you would need to do any localization of the result here
    return round(float(a) * float(b) * float(c), 2)



@register.simple_tag()
def round2(value, *args, **kwargs):
    # you would need to do any localization of the result here
    return round(float(value), 2)


@register.simple_tag()
def getCoins():
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        input = """<root>{
            let $a := db:open("Bolsa")/coins/coin
            return $a
            }</root>
        """
        query = session.query(input)
        res = query.execute()
        query.close()
    # closes database session
    finally:
        if session:
            session.close()
    dres = xmltodict.parse(res)
    lres = dres['root']['coin']
    coins = {}
    for coin in lres:
        coins[coin['code']] = coin['symbol']
    return coins

@register.simple_tag()
def getCoinValue(code):
    if code is None or code == "usd":
        return 1
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        input = """<root>{{
            for $a in db:open("Bolsa")/days/update[last()]/coin
            where $a/code = "{}"
            return $a/value/text()
            }}</root>
        """.format(code)
        query = session.query(input)
        res = query.execute()
        query.close()
    # closes database session
    finally:
        if session:
            session.close()
    dres = xmltodict.parse(res)
    lres = dres['root']
    if not lres:
        lres = 1
    return lres

@register.simple_tag()
def getCoinSymbol(code):
    if code is None or code == "usd":
        return "$"
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        input = """<root>{{
                   for $a in db:open("Bolsa")/coins/coin
                   where $a/code = "{}"
                   return $a/symbol/text()
                   }}</root>
        """.format(code)
        query = session.query(input)
        res = query.execute()
        query.close()
    # closes database session
    finally:
        if session:
            session.close()
    dres = xmltodict.parse(res)
    lres = dres['root']
    if not lres:
        lres = "$"
    return lres





