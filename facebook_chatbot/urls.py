from django.conf.urls import include, url
from .views import recommBotView
urlpatterns = [
                url(r'^bot_clinet/?$', recommBotView.as_view()) 
            ]
