from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    
    url(r'^$', views.debatesList, name='debatesList'),
    
    url(r'^debat/(?P<iddebate>[0-9]+)', views.index, name='index'),  
    url(r'^statistics/(?P<iddebate>[0-9]+)', views.statistics, name='statistics'),
    url(r'^reports/(?P<iddebate>[0-9]+)', views.reports, name='reports'),
    
    url(r'^butHandler/', views.butHandler, name='butHandler'),
    url(r'^newHandler/', views.newHandler, name='newHandler'),
    url(r'^nextHandler/', views.nextHandler, name='nextHandler'),  
    url(r'^sounder/', views.sounder, name='sounder'),  
    url(r'^soundFileHandler/', views.soundFileHandler, name='soundFileHandler'),
    
    url(r'^test/', views.test, name='test'),
     
    url(r'^login/$', auth_views.login,
       {'template_name': 'admin/login.html'}),
    url(r'^logout/$', auth_views.logout),   
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)