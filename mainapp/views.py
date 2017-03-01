from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
import os
import json
import csv
from django.db.models import Q
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test

from .models import *


from django.core.signals import request_finished
from django.db.models.signals import post_save

from django.dispatch import receiver
import django.dispatch
from mainapp.signals import *



@login_required
def index(request):
    
    waitingPns = Participation.objects.filter(status='0').filter(user = request.user)

    try:
        nextPn = Participation.objects.get(status='next')
    except:
        nextPn = None
        
    try:    
        goingPn = Participation.objects.get(status='1')
        wtPn = waitingPns.filter(linkedToPn = goingPn)
        if wtPn.count() > 0:
            goingPn.wtPnType = True
        else:
            goingPn.wtPnType = False        
    except:
        goingPn = None  

    try:    
        newPn = Participation.objects.get(user = request.user, status ='0', linkedToPn=None)
    except:
        newPn = None     
        
    oldPns = Participation.objects.filter(status='2').order_by('-endTime')   

    allWaitingCount = Participation.objects.filter(status='0').count()
    
    for pn in oldPns:
        
        ##Calcul du temps écoulé
        pn.timeDiff = pn.endTime - pn.startTime        
        seconds = pn.timeDiff.total_seconds() 
        minutes = (seconds) // 60
        seconds = seconds - minutes * 60
        pn.seconds = seconds    
        pn.minutes = minutes    
            
        ##Marquage s'il y a des waitingPn reliées
        wtPn = waitingPns.filter(linkedToPn = pn)
        if wtPn.count() > 0:
            pn.wtPnType = True
        else:
            pn.wtPnType = False

    users = User.objects.all()
    
    
    return render(request,'mainapp/index.html',{
                            'newPn':newPn,
                            'allWaitingCount':allWaitingCount,
                            'users':users,
                            'nextPn':nextPn,
                            'goingPn':goingPn,
                            'oldPns':oldPns,
                            'waitingPns':waitingPns})

def statistics(request):
    
    oldPns = Participation.objects.filter(status='2').order_by('-endTime') 
    users = User.objects.all()       
    totalTime = datetime.now() - datetime.now()       
    for user in users:
        oldies = oldPns.filter(user = user)
        time = datetime.now() - datetime.now()
        for oldie in oldies:
            time = time + oldie.endTime - oldie.startTime
        user.time = time
        totalTime = totalTime + time
    
    
    seconds = totalTime.total_seconds() 
    minutes = (seconds) // 60
    seconds = seconds - minutes * 60

    
    theoricTimePC = 1 / users.count()       

    for user in users:
        user.timePC = user.time / totalTime
    
    
    return render(request,'mainapp/statistics.html',{
                            'users':users,
                            'totalTime':totalTime,
                            'seconds':seconds,
                            'minutes':minutes,
                            'theoricTimePC':theoricTimePC,
                            'oldPns':oldPns})      
 
def test(request):
    return render(request,'mainapp/test.html',{})
    
def butHandler(request):
    if request.method == "POST":
        
        pn = Participation.objects.get(pk = request.POST['id'])

        obj, created = Participation.objects.get_or_create(
            debate = pn.debate,
            user = request.user,           
            status = 0, 
            linkedToPn = pn,     
            defaults = {
                'creationTime' : datetime.now(),
                'linkType' : request.POST['type']
            }
            
        )
        
        if not created:
            if obj.linkType == request.POST['type']:
                obj.delete()
            else:
                obj.linkType = request.POST['type']
                obj.save()
                
        nextUpdate()
                   
        return HttpResponse('Ok')
        
    return redirect('/')    
  
def newHandler(request):
    if request.method == "POST":
    
        try:    
            newPn = Participation.objects.get(user = request.user, status ='0', linkedToPn=None)
            newPn.delete()
        except:
            newPn = Participation(           
                debate = Debate.objects.all()[0],
                user = request.user,
                creationTime = datetime.now(),
                status = 0 
            )   
            newPn.save()

        nextUpdate()    
            
        return HttpResponse('Ok')

            
    return redirect('/')

def nextCalculation():
    oldPns = Participation.objects.filter(status='2')   
    waitingPns = Participation.objects.filter(status='0')
    
    if waitingPns.count() == 0:
        return None
    elif waitingPns.count() == 1:
        return waitingPns[0]
    elif waitingPns.count() > 0:
        
        ##Calculons pour chaque utilisateur le temps utilisé (plus l'utilisateur a parlé, moins il aura de points)
        users = User.objects.all()       
        totalTime = datetime.now() - datetime.now()       
        for user in users:
            oldies = oldPns.filter(user = user)
            time = datetime.now() - datetime.now()
            for oldie in oldies:
                time = time + oldie.endTime - oldie.startTime
            user.time = time
            totalTime = totalTime + time
        
        theoricTimePC = 1 / users.count()
        
        userPoints = {}
            
        for user in users:
            userTimePC = user.time/totalTime 
            userPoints[user.pk] = 200 * (theoricTimePC - userTimePC) / ( (userTimePC+0.0001) * (1.00001 - userTimePC) )        
            # print(user.username +' : '+str(userPoints[user.pk]))
    
        ##Calculons le nombre de point pour chaque PN:
        
        maxPoints = 0
        forMaxUserPoints = 0
        forMaxDelayPoints = 0
        forMaxBonusPoints = 0
        
        maxWtpn = waitingPns[0]
        for wtpn in waitingPns:
            
            ##On calcule les points issus de la vieillesse de la demande:
            delayPoints = (datetime.now() - wtpn.creationTime).total_seconds() 
        
            ##On met un bonus si c'est une réponse
            bonus = 0
            if wtpn.linkedToPn:
                bonus = 100
        
            ##On additionne le tout
            wtpn.points = userPoints[wtpn.user.pk] + delayPoints + bonus
            
            # print( str(wtpn.pk) +' : '+str(wtpn.points)+' --> '
                                    # + str(userPoints[wtpn.user.pk]) 
                                    # + ' + '
                                    # +str(delayPoints) 
                                    # + ' + '
                                    # +str(bonus) 
                 # )
            
            ##Si le score dépasse le score maximal précédent, on marque le nouveau champion
            if(wtpn.points > maxPoints):    
                
                maxPoints = wtpn.points
                forMaxUserPoints = userPoints[wtpn.user.pk]
                forMaxDelayPoints = delayPoints
                forMaxBonusPoints = bonus               
                
                maxWtpn = wtpn
        
        
        ##On enregistre le score du champion, pour voir quels points jouent le plus
        maxWtpn.totalPoints = maxPoints
        maxWtpn.userPoints = forMaxUserPoints
        maxWtpn.delayPoints = forMaxDelayPoints
        maxWtpn.bonusPoints = forMaxBonusPoints
        maxWtpn.save()
             
        return maxWtpn    

        
def nextUpdate():
        
    goingPn = Participation.objects.filter(status='1')   
    currentNextPn = Participation.objects.filter(status='next')   
    
    ##S'il y a ni going, ni next
    if goingPn.count() == 0 and currentNextPn.count() == 0:
        newNextPn = nextCalculation()
        if newNextPn:
            ##S'il y a une participation de dispo, on la met en going
            newNextPn.status = '1'
            newNextPn.startTime = datetime.now()
            newNextPn.save()
            ##... on reload les screens, et on lance l'enregistrement
            beginSignal.send(None)
            my_signal.send(None)
            

    
    ##S'il y a un going mais pas de next   
    elif goingPn.count()>0 and currentNextPn.count() == 0:
        newNextPn = nextCalculation()
        if newNextPn:
            ##S'il y a une participation de dispo, on la met en next
            newNextPn.status = 'next'
            newNextPn.save()
            ##...et on ne va pas envoyer de signal 
            

            
    ##S'il n'y a pas de going mais il y a un next
    elif goingPn.count()==0 and currentNextPn.count() > 0:
        ##On va lancer la next
        pn = currentNextPn[0]
        pn.status = '1'
        pn.startTime = datetime.now()
        pn.save()
        ##On envoie les signaux..
        beginSignal.send(None)
        my_signal.send(None)
        
        ##Et on relance nextUpdate()
        nextUpdate()
        

        
    ##S'il n'y a un going et un next, on ne fait rien...
                                 
def nextHandler(request):

    goingPn = Participation.objects.get(status='1')
    if request.user == goingPn.user:       
        ##Current devient old    
        goingPn.status = 2
        goingPn.endTime = datetime.now()
        goingPn.save()    
        ##Et on stop l'enregistrement
        stopSignal.send(None)
        
        ##Maintenant, on lance l'update
        nextUpdate()
        
    return redirect('/')
    
def soundFileHandler(request):
    pn = Participation.objects.order_by('-endTime')[0]
    pn.soundFile = request.FILES['file']
    pn.save()
    
    return HttpResponse("yeaaaaaah")
    
def sounder(request):

    

    return render(request,'mainapp/sounder.html',{})