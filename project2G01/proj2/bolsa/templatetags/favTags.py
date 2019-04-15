from django import template
from bolsa.utils import queryDB, checkAskQuery

register = template.Library()

@register.simple_tag()
def isFavouriteCompany(userID, code):
    query="""
    PREFIX pred: <http://wikicompany.pt/pred/>
    PREFIX user: <http://wikicompany.pt/user/>
    ASK {{
        ?user pred:favCompany ?company.
        ?company a "company".
        ?user pred:idUser "{}".
        ?company pred:symbol "{}".
    }}
    """.format(userID, code.upper())
    res = queryDB(query, simplify=False)
    return checkAskQuery(res)

@register.simple_tag()
def isFavouriteCEO(userID, name):
    query="""
    PREFIX pred: <http://wikicompany.pt/pred/>
    PREFIX user: <http://wikicompany.pt/user/>
    ASK {{
        ?user pred:favCeo ?ceo.
        ?ceo a "ceo".
        ?user pred:idUser "{}".
        ?ceo pred:name "{}".
    }}
    """.format(userID, name)
    res = queryDB(query, simplify=False)
    return checkAskQuery(res)

