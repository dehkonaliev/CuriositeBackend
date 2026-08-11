from django.urls import path
from .views import ReplenishWalletAPIView, SubscribeAPIView, PlansAPIView, BuyCourseAPIView, MyWalletAPIView, MySubscriptionsAPIView

urlpatterns = [
    path('replenish-wallet', ReplenishWalletAPIView.as_view()),
    path('plans', PlansAPIView.as_view()),
    path('subscribe', SubscribeAPIView.as_view()),
    path('buy-course', BuyCourseAPIView.as_view()),
    path('my-wallet', MyWalletAPIView.as_view()),
    path('my-subscriptions', MySubscriptionsAPIView.as_view()),
]