from django.urls import path
from .views import LeadersAPIView, MyPlaceAPIView

urlpatterns = [
    path('leaders', LeadersAPIView.as_view()),
    path('my-place', MyPlaceAPIView.as_view()),
]