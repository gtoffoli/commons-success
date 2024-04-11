from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required

def home(request):
    return HttpResponseRedirect('/project/success-erasmus/')

@login_required
def raise_exception(request):
    raise
