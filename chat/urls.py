from chat.views import chat_page, register, login_view, logout_view, get_messages
from django.urls import path

urlpatterns = [
    path("", register, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("chat/", chat_page, name="chat"),
    path("api/messages/<int:user_id>/", get_messages, name="get_messages"),
]