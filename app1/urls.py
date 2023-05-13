from  django.urls  import  path
from . import views 

urlpatterns = [
path('', views.homepage, name='homepage'),
path('create_event_page/', views.create_event_page, name='create_event_page'),
path('create_event/', views.create_event, name='create_event'),
]