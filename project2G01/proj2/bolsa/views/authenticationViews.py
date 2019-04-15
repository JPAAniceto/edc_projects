from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, HttpResponse, redirect
from bolsa.forms import RegisterForm
from bolsa.utils import queryDB


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            name = form.cleaned_data.get('name')
            user = authenticate(username=username, password=raw_password)
            # Add user to DB
            query = """
            PREFIX pred: <http://wikicompany.pt/pred/>
            PREFIX user: <http://wikicompany.pt/user/>
            INSERT DATA {{
                user:{id} a "user".
                user:{id} pred:idUser "{id}".
                user:{id} pred:name "{name}".
            }}
            """.format(id=user.id, name=name)
            queryDB(query, update=True, simplify=False)
            login(request, user)
            return redirect('/profile')
    else:
        form = RegisterForm()
    context = {
        'form': form
    }
    return render(request, 'registration/register.html', context)


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        return render(request, 'registration/logout.html')
    else:
        return redirect('/accounts/login')

