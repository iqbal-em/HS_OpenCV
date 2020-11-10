from django.urls import path, include
from streamapp import views


urlpatterns = [
    path("", views.index, name="index"),
    path("video_feed", views.video_feed, name="video_feed"),
    path("iklan_feed", views.iklan_feed, name="iklan_feed"),
    path("iklanapihandler", views.iklan_api, name= "iklan_apifeed"),
    path("datacamapihandler", views.datacam_api,name= "datacam_apifeed" ),
    path("peoplecountapihandler", views.peoplecount_api, name= "peoplecount_apifeed"),
]
