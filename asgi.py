# import os
# import django
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# from django.core.asgi import get_asgi_application
# import club.routing

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "college_portal.settings")
# django.setup()

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             club.routing.websocket_urlpatterns
#         )
#     ),
# })
