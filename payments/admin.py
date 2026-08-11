from django.contrib import admin
from .models import StudentWallet, Subscription, WalletTransaction, Plan

admin.site.register(StudentWallet)
admin.site.register(Subscription)
admin.site.register(WalletTransaction)
admin.site.register(Plan)