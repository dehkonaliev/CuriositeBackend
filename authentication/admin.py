from django.contrib import admin
from .models import CustomUser, CodeVerify, UserPreference, MyToken


admin.site.register(CustomUser)
admin.site.register(CodeVerify)
admin.site.register(UserPreference)
admin.site.register(MyToken)
