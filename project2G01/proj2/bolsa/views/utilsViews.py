from django.shortcuts import render, HttpResponse, redirect

def selectCoin(request, code):
    referer = request.GET['last']
    request.session['selected_coin'] = code
    return redirect(referer)

