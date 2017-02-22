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

@login_required
def index(request):
    try:
        nextPn = Participation.objects.get(status='next')
    except:
        nextPn = None
    goingPn = Participation.objects.get(status='1')  
    oldPns = Participation.objects.filter(status='2').order_by('-endTime')   
    waitingPns = Participation.objects.filter(status='0').filter(user = request.user)

    for pn in oldPns:
        pn.timeDiff = pn.endTime - pn.startTime

        wtPn = waitingPns.filter(linkedToPn = pn)
        if wtPn.count() > 0:
            pn.wtPnType = wtPn[0].get_linkType_display()
    
    
    
    users = User.objects.all()
    
    totalTime = datetime.now() - datetime.now()
    
    for user in users:
        oldies = oldPns.filter(user = user)
        time = datetime.now() - datetime.now()
        for oldie in oldies:
            time = time + oldie.endTime - oldie.startTime
        user.time = time
        
        totalTime = totalTime + time

    for user in users:
        user.timepc = user.time / totalTime * 100

    
    return render(request,'mainapp/index.html',{
                            'users':users,
                            'totalTime':totalTime,
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
    
    theoricTimePC = 1 / users.count()       

    for user in users:
        user.timePC = user.time / totalTime
    
    
    return render(request,'mainapp/statistics.html',{
                            'users':users,
                            'totalTime':totalTime,
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
                   
        return HttpResponse('Ok')
        
    return redirect('/')    
    
def nextHandler(request):
    
    nextPn = Participation.objects.get(status='next')
    goingPn = Participation.objects.get(status='1')
    
    ##Next devient current
    nextPn.status = 1
    nextPn.startTime = datetime.now()
    nextPn.save()
    
    ##Current devient old      
    goingPn.status = 2
    goingPn.endTime = datetime.now()
    goingPn.save()
    
    oldPns = Participation.objects.filter(status='2')   
    
    ##Déterminons la nouvelle Next
    waitingPns = Participation.objects.filter(status='0')
    if waitingPns.count() > 0:
        
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
    
    
        ##Calculons le nombre de point pour chaque PN:
        
        maxPoints = 0
        maxWtpn = waitingPns[0]
        for wtpn in waitingPns:
            wtpn.points = userPoints[wtpn.user.pk]
            
            if(wtpn.points > maxPoints):    
                maxPoints = wtpn.points
                maxWtpn = wtpn
            
        maxWtpn.status = 'next'
        maxWtpn.save()
    
    
    return redirect('/')