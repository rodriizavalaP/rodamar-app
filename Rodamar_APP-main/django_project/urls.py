from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Panel técnico de Django
    path('admin/', admin.site.urls),
    
    # Rutas públicas de inicio
    path('', include('pages.urls')),
    
    # Rutas del sistema portuario y logística
    path('logistica/', include('logistica.urls')),

    # Registro de usuarios (rol USUARIO)
    path('usuarios/', include('usuarios.urls')),
    
    # Autenticación (Login y Logout)
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- API REST (Unidad 3) ---
    # CRUD REST + JSON de buques, clientes, camiones, vehículos e historial
    path('api/', include('logistica.api_urls')),
    # Autenticación por JWT: obtener y refrescar el token de acceso
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]