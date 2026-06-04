"""
CareerBridge — Root URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("jobs/", include("apps.jobs.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("scraper/", include("apps.scraper.urls")),
    # API endpoints
    path("api/jobs/", include("apps.jobs.api_urls")),
    path("api/analytics/", include("apps.analytics.api_urls")),
    path("api/scraper/", include("apps.scraper.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin site customization
admin.site.site_header = "CareerBridge Admin"
admin.site.site_title = "CareerBridge"
admin.site.index_title = "Dashboard"
