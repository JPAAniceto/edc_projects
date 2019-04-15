from django.shortcuts import render, HttpResponse, redirect
from bolsa.utils import queryDB

def favoriteCompany(request, code):
    if request.user.is_authenticated:
        referer = '/profile'
        if 'last' in request.GET:
            referer = request.GET['last']
        query = """
        PREFIX pred: <http://wikicompany.pt/pred/>
        PREFIX user: <http://wikicompany.pt/user/>
        INSERT {{
            ?user pred:favCompany ?company.
        }}
        WHERE {{
            ?user pred:idUser "{id}".
            ?company a "company".
            ?company pred:symbol "{symbol}".
        }}
        """.format(id=request.user.id, symbol=code.upper())
        queryDB(query, simplify=False, update=True)
        return redirect(referer)
    else:
        return redirect('/accounts/login')


def unfavoriteCompany(request, code):
    if request.user.is_authenticated:
        referer = '/profile'
        if 'last' in request.GET:
            referer = request.GET['last']
        query = """
        PREFIX pred: <http://wikicompany.pt/pred/>
        PREFIX user: <http://wikicompany.pt/user/>
        DELETE {{
            ?user pred:favCompany ?company.
        }}
        WHERE {{
            ?user pred:idUser "{id}".
            ?company a "company".
            ?company pred:symbol "{symbol}".
        }}
        """.format(id=request.user.id, symbol=code.upper())
        queryDB(query, simplify=False, update=True)
        return redirect(referer)
    else:
        return redirect('/accounts/login')


def favoriteCeo(request, name):
    if request.user.is_authenticated:
        referer = '/profile'
        if 'last' in request.GET:
            referer = request.GET['last']
        query = """
        PREFIX pred: <http://wikicompany.pt/pred/>
        PREFIX user: <http://wikicompany.pt/user/>
        INSERT {{
            ?user pred:favCeo ?ceo.
        }}
        WHERE {{
            ?user pred:idUser "{id}".
            ?ceo a "ceo".
            ?ceo pred:name "{name}".
        }}
        """.format(id=request.user.id, name=name)
        queryDB(query, simplify=False, update=True)
        return redirect(referer)
    else:
        return redirect('/accounts/login')


def unfavoriteCeo(request, name):
    if request.user.is_authenticated:
        referer = '/profile'
        if 'last' in request.GET:
            referer = request.GET['last']
        query = """
        PREFIX pred: <http://wikicompany.pt/pred/>
        PREFIX user: <http://wikicompany.pt/user/>
        DELETE {{
            ?user pred:favCeo ?ceo.
        }}
        WHERE {{
            ?user pred:idUser "{id}".
            ?ceo a "ceo".
            ?ceo pred:name "{name}".
        }}
        """.format(id=request.user.id, name=name)
        queryDB(query, simplify=False, update=True)
        return redirect(referer)
    else:
        return redirect('/accounts/login')