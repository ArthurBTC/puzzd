from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Debate(models.Model):
    #admin = models.ForeignKey(User)
    theme = models.CharField(max_length = 300,default = 'default' ,blank=True, null=True)
    place = models.CharField(max_length = 300, default = 'default' ,blank=True, null=True)
    participants = models.ManyToManyField(User, blank=True)
    creationTime = models.DateTimeField()

class Participation(models.Model):

    STATUS_CHOICE = (
        ('0','Created'),
        ('1','Started'),
        ('2','Finished'),
        ('next','Next'),
        ('-1','Cancelled'),
    )

    LINK_TYPE = (
        ('0','Answer'),
        ('1','Question'),
    )     
    
    debate = models.ForeignKey(Debate)
    user = models.ForeignKey(User)
    creationTime = models.DateTimeField()
    startTime = models.DateTimeField(blank=True, null=True)
    endTime = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length = 30, choices = STATUS_CHOICE, default = '0') 
    
    
    from datetime import date
    def upload_path(instance, filename):
        import os
        from datetime import date
        d = date.today()
        parts = os.path.splitext(filename)
        return 'soundFiles/%s/%s/%s/%s.%s' % (
            d.year, d.month, d.day, parts[0], 'wav')
       
    # soundFile = models.FileField(upload_to='soundFiles/', blank=True, null=True)
    soundFile = models.FileField(upload_to=upload_path, blank=True, null=True)
    # duration = models.DurationField(default = 0, blank=True, null=True)
    text = models.CharField(max_length = 3000, default = '', blank=True, null=True)
    
    linkedToPn = models.ForeignKey('self', blank=True, null=True)
    linkType = models.CharField(max_length = 30, choices = LINK_TYPE, blank=True, null=True)
    
    totalPoints = models.IntegerField(default = 0, blank=True, null=True)
    userPoints = models.IntegerField(default = 0, blank=True, null=True)
    delayPoints = models.IntegerField(default = 0, blank=True, null=True)
    bonusPoints = models.IntegerField(default = 0, blank=True, null=True)
    
    def __str__(self):
        return str(self.id)
    
    
class Link(models.Model):
    debate = models.ForeignKey(Debate)
    user = models.ForeignKey(User)
    leftParticipation = models.ForeignKey(Participation, related_name='%(class)s_left_participation')
    rightParticipation = models.ForeignKey(Participation, related_name='%(class)s_right_participation')
    creationTime = models.DateTimeField()
    
class Request(models.Model):

    TYPE_CHOICE = (
        ('precision','Precision'),
        ('definition','Definition'),
    ) 
    
    STATUS_CHOICE = (
        ('0','Created'),
        ('1','Answered'),
        ('-1','Cancelled'),
    )    

    debate = models.ForeignKey(Debate)
    participation = models.ForeignKey(Participation)
    user = models.ForeignKey(User)
    type = models.CharField(max_length = 30, choices = TYPE_CHOICE, default = 'precision')     
    status = models.CharField(max_length = 30, choices = STATUS_CHOICE, default = '0') 
    
    creationTime = models.DateTimeField()
    endTime = models.DateTimeField(blank=True, null=True)
    
class Appreciation(models.Model):
    TYPE_CHOICE = (
        ('like','Like'),
        ('dislike','Dislike'),
    ) 
    
    debate = models.ForeignKey(Debate)
    participation = models.ForeignKey(Participation)
    user = models.ForeignKey(User)
    type = models.CharField(max_length = 30, choices = TYPE_CHOICE, default = 'like')     
    
    creationTime = models.DateTimeField() 
    