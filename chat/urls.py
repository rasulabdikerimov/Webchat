from chat.views import chat_page
from django.urls import path
urlpatterns = [
    path("chat/", chat_page),
]