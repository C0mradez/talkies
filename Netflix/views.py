from pickle import NONE
from queue import Empty
from types import NoneType
from unicodedata import category, name
from urllib import request
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from Core.settings import TMDB_API_KEY
import requests
import tmdbsimple as tmdb
from Netflix.models import *
from django.conf import settings
import stripe
from django.http import HttpResponse,JsonResponse
stripe.api_key = settings.STRIPE_SKEY

# Create your views here.
def Home(request):
    return render(request, 'Index.html')

def Register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1=="" or email=="" or username=="" or password2=="":
            messages.error(request,'⚠️ please fill all fields')

        elif password1 != password2:
            messages.error(request, '⚠️ Passwords Do Not Match! Try Again')
           # return redirect('Register')

        elif User.objects.filter(username=username).exists():
            messages.error(request, '⚠️ Username Already Exists!')
            #return redirect('Register')

        elif User.objects.filter(email=email).exists():
            messages.error(request, '⚠️ Email Address Already Exists!')
           # return redirect('Register')
        else:

           user = User.objects.create_user(username=username, email=email)
           user.set_password(password1)
           user.save()
        
           messages.success(request, '✅ Regristration Successful!')
           customer = Customer(user=user)
           customer.save()
           return redirect('Register')

    return render(request, 'Register.html')    
# def Register(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         email = request.POST['email']
#         password1 = request.POST['password1']
#         password2 = request.POST['password2']

#         if password1 != password2:
#             messages.error(request, '⚠️ Passwords Do Not Match! Try Again')
#             return redirect('Register')

#         if User.objects.filter(username=username).exists():
#             messages.error(request, '⚠️ Username Already Exists!')
#             return redirect('Register')

#         if User.objects.filter(email=email).exists():
#             messages.error(request, '⚠️ Email Address Already Exists!')
#             return redirect('Register')

#         if User.objects.filter(email=None).exists():
#             messages.error(request, '⚠️ fill all credentials!')
#             return redirect('Register')

#         if User.objects.filter(username=NoneType).exists():
#             messages.error(request, '⚠️ fill all credentials!')
#             return redirect('Register')

#         if User.objects.filter(password1=NoneType).exists():
#             messages.error(request, '⚠️ fill all credentials!')
#             return redirect('Register')
        
#         if User.objects.filter(password2=NoneType).exists():
#             messages.error(request, '⚠️ fill all credentials!')
#             return redirect('Register')
        
            

    

#         user = User.objects.create_user(username=username, email=email)
#         user.set_password(password1)
#         user.save()
        
#         messages.success(request, '✅ Regristration Successful!')
#         customer = Customer(user=user)
#         customer.save()
#         return redirect('Register')

#     return render(request, 'Register.html')

def Login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if not User.objects.filter(username=username).exists():
            messages.error(request, '⚠️ Username Does Not Exist!')
            return redirect('Login')

        if user is None:
            messages.error(request, '⚠️ Username or Password Is Incorrect!!')
            return redirect('Login')

        if user is not None:
            login(request, user)
            return redirect(reverse('Recommendations'))
        
    return render(request, 'Login.html')

@login_required(login_url='Login')
def Logout(request):
    logout(request)
    messages.success(request, '✅ Successfully Logged Out!')
    return redirect(reverse('Login'))

@login_required(login_url='Login')
def Recommendations(request):
    upcoming_request = requests.get("https://api.themoviedb.org/3/movie/upcoming?api_key=" + TMDB_API_KEY)
    upcoming_results = upcoming_request.json()
    upcoming = upcoming_results['results']
    now_playing_movies = Movies.objects.filter(category='TRENDING NOW')
    top_rated = Movies.objects.filter(category='TOP PICKS') 
    popular_tv =  Movies.objects.filter(category='TV SHOWS')
    must_watch = Movies.objects.filter(category='MUST WATCH') 
    w_again = Movies.objects.filter(category='AGAIN') 
    # print(w_again)
    
    # print(now_playing_movies[0].title)


    return render(request, 'Recommendations.html', {'now_playing_movies':now_playing_movies, 'top_rated':top_rated, 'must_watch':must_watch, 'popular_tv':popular_tv,'again':w_again})

@login_required(login_url='Login')
def MovieDetails(request, movie_id):
    user = request.user
    customer = Customer.objects.get(user=user)
    movie = Movies.objects.get(id=movie_id)
    order = Orders.objects.filter(user=customer,movie=movie)
    playmov = False
    if order and order[0].watch_cnt <2:
        playmov = True
    # print(movie.trailer)
    video_url = movie.trailer
    video_url = video_url[32:]
    print(video_url)
    return render(request, 'Movie Details.html', {'movie':movie,'vid_url': video_url,'order':playmov})




@login_required(login_url='Login')
def PlayMovie(request,m_id):
    user = request.user
    cust = Customer.objects.get(user = user)
    movie = Movies.objects.get(id=m_id)
    ord = Orders.objects.filter(user=cust,movie=movie)   
    # try:
    #     endpoint = stripe.WebhookEndpoint.create(url='https://hungry-jobs-rhyme-103-160-194-136.loca.lt/webhook', enabled_events=['charge.failed','charge.succeeded', ],)
    #     print(endpoint)

    # except Exception as e:
    #     print(e)
    if ord and ord[0].watch_cnt <2:
        ord[0].watch_cnt += 1
        ord[0].save()
        movie = Movies.objects.get(id=m_id)
        print(movie.video_file)
        return render(request,'moviePlay.html',{'vid': movie.video_file})
    else:
        return render(request,'noorder.html',{'movie':movie})

@login_required(login_url='Login')
def checkout(request,m_id):
    if request.method == 'POST':
        movie = Movies.objects.get(id=m_id)
        user = request.user.id
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                    'price': f'{movie.stripe_id}',
                    'quantity': 1,

                    },
                ],
                mode='payment',
                success_url=f'http://127.0.0.1:8000/play/{m_id}',
                cancel_url=f'http://127.0.0.1:8000/play/{m_id}',
                client_reference_id = str(user)
 

            )
                
        except Exception as e:
            # return str(e)
            print(e)        
        return redirect(checkout_session.url, code=303)
        # return JsonResponse({'sessionId': checkout_session['id']})

from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def stripe_webhook(request):
  stripe.api_key = settings.STRIPE_SKEY
  endpoint_secret = 'whsec_ba59f2c438bcff1c01a5ba2a998d811bb53154e5816402fec135d128a84bb478'
  payload = request.body
  sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
  event = None

  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, endpoint_secret
    )
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)
  except stripe.error.SignatureVerificationError as e:
    # Invalid signature
    return HttpResponse(status=400)

  # Handle the checkout.session.completed event
  if event["type"] == "checkout.session.completed":
    # print(event)
    # print(event.data.object.client_reference_id)
    user = User.objects.get(id=int(event.data.object.client_reference_id))
    user= Customer.objects.get(user=user)
    # movie = event.data.object.
    print(event.data.object.success_url[27:])
    print(user)
    m_id = int(event.data.object.success_url[27:])
    movie = Movies.objects.get(id=m_id)
    order = Orders.objects.filter(user=user,movie=movie)
    if order:
        order = order[0]
        order.watch_cnt = 0
        order.save()
        return HttpResponse(status=200)

    order = Orders(user=user,movie=movie,watch_cnt=0)
    print(order)
    order.save()
    print("order saved")
    

  return HttpResponse(status=200)# #from unicodedata import category, name
# from urllib import request
# from django.shortcuts import redirect, render
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.models import User
# from django.contrib import messages
# from django.contrib.auth import authenticate, login, logout
# from django.urls import reverse
# from Core.settings import TMDB_API_KEY
# import requests
# import tmdbsimple as tmdb
# from Netflix.models import *
# from django.conf import settings
# import stripe
# from django.http import HttpResponse,JsonResponse
# stripe.api_key = settings.STRIPE_SKEY

# # Create your views here.
# def Home(request):
#     return render(request, 'Index.html')
    
# def Register(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         email = request.POST['email']
#         password1 = request.POST['password1']
#         password2 = request.POST['password2']

#         if password1 != password2:
#             messages.error(request, '⚠️ Passwords Do Not Match! Try Again')
#             return redirect('Register')

#         if User.objects.filter(username=username).exists():
#             messages.error(request, '⚠️ Username Already Exists!')
#             return redirect('Register')

#         if User.objects.filter(email=email).exists():
#             messages.error(request, '⚠️ Email Address Already Exists!')
#             return redirect('Register')

#         user = User.objects.create_user(username=username, email=email)
#         user.set_password(password1)
#         user.save()
        
#         messages.success(request, '✅ Regristration Successful!')
#         customer = Customer(user=user)
#         customer.save()
#         return redirect('Register')

#     return render(request, 'Register.html')

# def Login(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']

#         user = authenticate(username=username, password=password)

#         if not User.objects.filter(username=username).exists():
#             messages.error(request, '⚠️ Username Does Not Exist!')
#             return redirect('Login')

#         if user is None:
#             messages.error(request, '⚠️ Username or Password Is Incorrect!!')
#             return redirect('Login')

#         if user is not None:
#             login(request, user)
#             return redirect(reverse('Recommendations'))
        
#     return render(request, 'Login.html')

# @login_required(login_url='Login')
# def Logout(request):
#     logout(request)
#     messages.success(request, '✅ Successfully Logged Out!')
#     return redirect(reverse('Login'))

# @login_required(login_url='Login')
# def Recommendations(request):
#     upcoming_request = requests.get("https://api.themoviedb.org/3/movie/upcoming?api_key=" + TMDB_API_KEY)
#     upcoming_results = upcoming_request.json()
#     upcoming = upcoming_results['results']
#     now_playing_movies = Movies.objects.filter(category='TRENDING NOW')
#     top_rated = Movies.objects.filter(category='TOP PICKS') 
#     popular_tv =  Movies.objects.filter(category='TV SHOWS')
#     must_watch = Movies.objects.filter(category='MUST WATCH') 
#     w_again = Movies.objects.filter(category='AGAIN') 
#     # print(w_again)
    
#     # print(now_playing_movies[0].title)


#     return render(request, 'Recommendations.html', {'now_playing_movies':now_playing_movies, 'top_rated':top_rated, 'must_watch':must_watch, 'popular_tv':popular_tv,'again':w_again})

# @login_required(login_url='Login')
# def MovieDetails(request, movie_id):
#     user = request.user
#     customer = Customer.objects.get(user=user)
#     movie = Movies.objects.get(id=movie_id)
#     order = Orders.objects.filter(user=customer,movie=movie)
#     playmov = False
#     if order and order[0].watch_cnt <2:
#         playmov = True
#     # print(movie.trailer)
#     video_url = movie.trailer
#     video_url = video_url[32:]
#     print(video_url)
#     return render(request, 'Movie Details.html', {'movie':movie,'vid_url': video_url,'order':playmov})




# @login_required(login_url='Login')
# def PlayMovie(request,m_id):
#     user = request.user
#     cust = Customer.objects.get(user = user)
#     movie = Movies.objects.get(id=m_id)
#     ord = Orders.objects.filter(user=cust,movie=movie)   
#     # try:
#     #     endpoint = stripe.WebhookEndpoint.create(url='https://hungry-jobs-rhyme-103-160-194-136.loca.lt/webhook', enabled_events=['charge.failed','charge.succeeded', ],)
#     #     print(endpoint)

#     # except Exception as e:
#     #     print(e)
#     if ord and ord[0].watch_cnt <2:
#         ord[0].watch_cnt += 1
#         ord[0].save()
#         movie = Movies.objects.get(id=m_id)
#         print(movie.video_file)
#         return render(request,'moviePlay.html',{'vid': movie.video_file})
#     else:
#         return render(request,'noorder.html',{'movie':movie})

# @login_required(login_url='Login')
# def checkout(request,m_id):
#     if request.method == 'POST':
#         movie = Movies.objects.get(id=m_id)
#         user = request.user.id
#         try:
#             checkout_session = stripe.checkout.Session.create(
#                 line_items=[
#                     {
#                     'price': f'{movie.stripe_id}',
#                     'quantity': 1,

#                     },
#                 ],
#                 mode='payment',
#                 success_url=f'http://127.0.0.1:8000/play/{m_id}',
#                 cancel_url=f'http://127.0.0.1:8000/play/{m_id}',
#                 client_reference_id = str(user)
 

#             )
                
#         except Exception as e:
#             # return str(e)
#             print(e)        
#         return redirect(checkout_session.url, code=303)
#         # return JsonResponse({'sessionId': checkout_session['id']})

# from django.views.decorators.csrf import csrf_exempt


# @csrf_exempt
# def stripe_webhook(request):
#   stripe.api_key = settings.STRIPE_SKEY
#   endpoint_secret = 'whsec_bf47feb59a5a43341ce102ce9af5bdd6c2c72f02045713bdc170e686644a0c22'
#   payload = request.body
#   sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
#   event = None

#   try:
#     event = stripe.Webhook.construct_event(
#       payload, sig_header, endpoint_secret
#     )
#   except ValueError as e:
#     # Invalid payload
#     return HttpResponse(status=400)
#   except stripe.error.SignatureVerificationError as e:
#     # Invalid signature
#     return HttpResponse(status=400)

#   # Handle the checkout.session.completed event
#   if event["type"] == "checkout.session.completed":
#     # print(event)
#     # print(event.data.object.client_reference_id)
#     user = User.objects.get(id=int(event.data.object.client_reference_id))
#     user= Customer.objects.get(user=user)
#     # movie = event.data.object.
#     print(event.data.object.success_url[27:])
#     print(user)
#     m_id = int(event.data.object.success_url[27:])
#     movie = Movies.objects.get(id=m_id)
#     order = Orders.objects.filter(user=user,movie=movie)
#     if order:
#         order = order[0]
#         order.watch_cnt = 0
#         order.save()
#         return HttpResponse(status=200)

#     order = Orders(user=user,movie=movie,watch_cnt=0)
#     print(order)
#     order.save()
#     print("order saved")
    

#   return HttpResponse(status=200)