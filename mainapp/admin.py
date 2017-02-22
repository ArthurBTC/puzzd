from django.contrib import admin
from .models import Debate, Participation, Link, Request, Appreciation

class DebateAdmin(admin.ModelAdmin):
    list_display = ('theme','place','creationTime')
    
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('debate','user','creationTime','endTime','status','soundFile','text')    

class LinkAdmin(admin.ModelAdmin):
    list_display = ('debate','user','leftParticipation','rightParticipation','creationTime')
    
class RequestAdmin(admin.ModelAdmin):
    list_display = ('debate','participation','user','type','status','creationTime','endTime')

class AppreciationAdmin(admin.ModelAdmin):
    list_display = ('debate','participation','user','type','creationTime') 
    
# Register your models here.
admin.site.register(Debate, DebateAdmin)
admin.site.register(Participation, ParticipationAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(Request, RequestAdmin)
admin.site.register(Appreciation, AppreciationAdmin)

    