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


#Vue utilisateur pendant le débat
@login_required
def index(request, iddebate):
    
    debate = Debate.objects.get(pk = iddebate)
    waitingPns = Participation.objects.filter(status='0').filter(user = request.user).filter(debate = debate)

    try:
        nextPn = Participation.objects.get(status='next', debate=debate)
    except:
        nextPn = None
        
    try:    
        goingPn = Participation.objects.get(status='1', debate=debate)
        wtPn = waitingPns.filter(linkedToPn = goingPn)
        ##Test si la prochaine n'est pas une réponse
        try:
            if nextPn.linkedToPn == goingPn and nextPn.user == request.user:
                aaa = 1
            else:
                aaa = 0
        except:
            aaa = 0
            
        if wtPn.count() + aaa > 0:
            goingPn.wtPnType = True
        else:
            goingPn.wtPnType = False 

        apcs= Appreciation.objects.filter(participation = goingPn).filter(user = request.user)
        if apcs.count() > 0:
            goingPn.apcMark = True
        else:
            goingPn.apcMark = False         
            
    except:
        goingPn = None  

    try:    
        newPn = Participation.objects.get(user = request.user, status ='0', linkedToPn=None, debate=debate)
    except:
        newPn = None     
        
    oldPns = Participation.objects.filter(status='2').filter(debate=debate).order_by('-endTime')

    allWaitingCount = Participation.objects.filter(status='0').filter(debate=debate).count()
    
    for pn in oldPns:
        
        ##Calcul du temps écoulé
        pn.timeDiff = pn.endTime - pn.startTime        
        seconds = pn.timeDiff.total_seconds() 
        minutes = (seconds) // 60
        seconds = seconds - minutes * 60
        pn.seconds = seconds    
        pn.minutes = minutes    
            
        ##Marquage s'il y a des waitingPn reliées
        
        try:
            if nextPn.linkedToPn == pn and nextPn.user == request.user:
                aaa = 1
            else:
                aaa = 0
        except:
            aaa = 0        
        
        wtPn = waitingPns.filter(linkedToPn = pn)
        if wtPn.count() + aaa > 0:
            pn.wtPnType = True
        else:
            pn.wtPnType = False

        ##Marquage s'il y a du love
        apcs= Appreciation.objects.filter(participation = pn).filter(user = request.user)
        if apcs.count() > 0:
            pn.apcMark = True
        else:
            pn.apcMark = False        
            
    users = User.objects.all()
    
    
    return render(request,'mainapp/index.html',{
                            'iddebate':iddebate,
                            'newPn':newPn,
                            'allWaitingCount':allWaitingCount,
                            'users':users,
                            'nextPn':nextPn,
                            'goingPn':goingPn,
                            'oldPns':oldPns,
                            'waitingPns':waitingPns})
  
#Vue utilisateurs après le débat  
def reports(request, iddebate):
    
    debate = Debate.objects.get(pk = iddebate)
    pns = Participation.objects.filter(debate = debate).order_by('startTime')

    for pn in pns:        
        ##Calcul du temps écoulé
        pn.timeDiff = pn.endTime - pn.startTime        
        seconds = pn.timeDiff.total_seconds() 
        minutes = (seconds) // 60
        seconds = seconds - minutes * 60
        pn.seconds = seconds    
        pn.minutes = minutes

        ##Calcul du nombre de like
        apcs = Appreciation.objects.filter(participation = pn)
        pn.likes = apcs.count()
    
    users = debate.participants.all()
    
    users, totalTime = usersTimeCalculator(users, pns)
    seconds = totalTime.total_seconds() 
    minutes = (seconds) // 60
    seconds = seconds - minutes * 60

    theoricTimePC = 1 / users.count() 
    
    return render(request,'mainapp/reports.html',{
                            'iddebate':iddebate,
                            'debate':debate,
                            'users':users,
                            'totalTime':totalTime,
                            'seconds':seconds,
                            'minutes':minutes,
                            'theoricTimePC':theoricTimePC,                            
                            'pns':pns})   
     
#Pendant le débat, pour voir les stats     
@login_required                            
def statistics(request, iddebate):
    
    debate = Debate.objects.get(pk = iddebate)
    oldPns = Participation.objects.filter(status='2').filter(debate = debate).order_by('-endTime')      
    users = debate.participants.all()
    
    users, totalTime = usersTimeCalculator(users, oldPns)
    
    seconds = totalTime.total_seconds() 
    minutes = (seconds) // 60
    seconds = seconds - minutes * 60

    theoricTimePC = 1 / users.count()       

      
    return render(request,'mainapp/statistics.html',{
                            'iddebate':iddebate,
                            'users':users,
                            'totalTime':totalTime,
                            'seconds':seconds,
                            'minutes':minutes,
                            'theoricTimePC':theoricTimePC,
                            'oldPns':oldPns})      

#Pendant le débat, pour l'admin    
@user_passes_test(lambda u: u.is_superuser)                         
def admindebate(request, iddebate):
    return render(request,'mainapp/admindebate.html',{
                            'iddebate':iddebate
                            })          
    
                            
#Calculer le temps pour un ensemble d'utilisateurs sur un ensemble de participations                            
def usersTimeCalculator(users, pns):
    totalTime = datetime.now() - datetime.now()
    for user in users:
        pnsUser = pns.filter(user = user)
        time = datetime.now() - datetime.now()
        for pnUser in pnsUser:
            time = time + pnUser.endTime - pnUser.startTime
        user.time = time
        totalTime = totalTime + time
        
    for user in users:
        user.timePC = user.time / totalTime        
        
    return users, totalTime    
                            
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
                
        nextUpdate(pn.debate)
                   
        return HttpResponse('Ok')
        
    return redirect('/')    
  
def newHandler(request):
    if request.method == "POST":
    
        debate = Debate.objects.get(pk = request.POST['iddebate'])
    
        try:    
            newPn = Participation.objects.get(user = request.user, debate = debate, status ='0', linkedToPn=None)
            newPn.delete()
        except:
            newPn = Participation(           
                debate = debate,
                user = request.user,
                creationTime = datetime.now(),
                status = 0 
            )   
            newPn.save()

        nextUpdate(debate)    
            
        return HttpResponse('Ok')

            
    return redirect('/')

def nextCalculation(debate):

    oldPns = Participation.objects.filter(status='2').filter(debate=debate)   
    waitingPns = Participation.objects.filter(status='0').filter(debate=debate)  
    
    if waitingPns.count() == 0:
        return None
    elif waitingPns.count() == 1:
        return waitingPns[0]
    elif waitingPns.count() > 0:
        
        ##Calculons pour chaque utilisateur le temps utilisé (plus l'utilisateur a parlé, moins il aura de points)
        users = debate.participants.all()       
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
        
def nextUpdate(debate):
        
    goingPn = Participation.objects.filter(status='1').filter(debate=debate)   
    currentNextPn = Participation.objects.filter(status='next').filter(debate=debate)     
    
    ##S'il y a ni going, ni next
    if goingPn.count() == 0 and currentNextPn.count() == 0:
        newNextPn = nextCalculation(debate)
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
        newNextPn = nextCalculation(debate)
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
        nextUpdate(debate)
              
    ##S'il n'y a un going et un next, on ne fait rien...
                                 
def nextHandler(request):

    debate = Debate.objects.get(pk = request.POST['iddebate'])
    goingPn = Participation.objects.get(status='1', debate=debate)
    if request.user == goingPn.user or request.user.username == 'arthur44' or request.user.username == 'arthur':       
        ##Current devient old    
        goingPn.status = 2
        goingPn.endTime = datetime.now()
        goingPn.save()    
        ##Et on stop l'enregistrement
        stopSignal.send(None)
        
        ##Maintenant, on lance l'update
        nextUpdate(debate)
        
    return redirect('/')
   

##Gérer les demandes de love ou de hate
@login_required
def loveHandler(request):

    # TYPE_CHOICE = (
        # ('like','Like'),
        # ('dislike','Dislike'),
    # ) 
    
    # participation = models.ForeignKey(Participation)
    # user = models.ForeignKey(User)
    # type = models.CharField(max_length = 30, choices = TYPE_CHOICE, default = 'like')     
    
    # creationTime = models.DateTimeField()  


 
    if request.method == "POST":
        pn = Participation.objects.get(pk = request.POST['id'])

        obj, created = Appreciation.objects.get_or_create(
            user = request.user,           
            participation = pn,     
            defaults = {
                'type' : 'like',
                'creationTime' : datetime.now()
            }
            
        )
        
        if not created:
            obj.delete()
                   
        return HttpResponse('Ok')        
    
    return redirect('/')
    
   
def soundFileHandler(request):
    pn = Participation.objects.order_by('-endTime')[0]
    pn.soundFile = request.FILES['file']
    pn.save()
    
    return HttpResponse("yeaaaaaah")
    
def sounder(request):

    return render(request,'mainapp/sounder.html',{})
    
def generateCueFile(iddebate):

    debate = Debate.objects.get(pk = iddebate)
    pns = Participation.objects.filter(debate = debate).order_by('startTime')
    
    file = open("CueFile_"+str(iddebate)+".txt","w") 
    file.write('FILE "debatmachine.MP3" MP3\n')
    
    i=1
    for pn in pns:  

        timedelta = pn.startTime - debate.creationTime
        seconds = timedelta.total_seconds()
        # hours = seconds // 3600
        # minutes = (seconds % 3600) // 60
        minutes = seconds  // 60
        seconds = seconds % 60
    
        file.write("  TRACK "+'%02d' % i+" AUDIO\n")
        file.write('    TITLE "Default"\n')
        file.write('    PERFORMER "'+pn.user.username+'"\n')
        # file.write('    INDEX 01 '+'%02d' % minutes+':'+'%02d' % seconds+':00\n')
        file.write('    INDEX 01 '+str(int(minutes))+':'+'%02d' % seconds+':00\n')
        i=i+1
    file.close()
    
@login_required    
def debatesList(request):
    debates = Debate.objects.filter(participants__id=request.user.id)
    # debates = Debate.objects.all()
    return render(request,'mainapp/debatesList.html',{'debates':debates})

def audioPaths(iddebate):
    debate = Debate.objects.get(pk = iddebate)
    pns = Participation.objects.filter(debate = debate).order_by('startTime')
    i = 1
    for pn in pns:
        pn.soundFile = "debateSounds/"+str(iddebate)+"/"+'%02d' % i+".mp3"
        pn.save()
        i=i+1
        
#Pour démarrer le débat (supprime tout, définit le creationTime)        
def startdebate(request, iddebate):
    debate = Debate.objects.get(pk = iddebate)
    Participation.objects.filter(debate=debate).delete()
    debate.creationTime = datetime.now()
    debate.save()
    my_signal.send(None)
    return HttpResponse('GOGOGO')
    
    
    