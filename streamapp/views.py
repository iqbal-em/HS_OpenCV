from django.shortcuts import render
from django.http.response import StreamingHttpResponse
from streamapp.camera import VideoCamera, handling_iklan
from .models import Iklan, PeopleCount, DataCam
from django.db import connection
import time
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from streamapp.response import Response
from . import transformer

# Create your views here.


def index(request):
    return render(request, "streamapp/home.html")

def iklan_api(request):
    iklan = Iklan.objects.all()
    iklan = transformer.transform(iklan)
    return Response.ok(values=iklan)
    #return render(request, "streamapp/api.html")

def datacam_api(request):
    datacam = DataCam.objects.all()
    datacam = transformer.transform(datacam)
    return Response.ok(values=datacam)

def peoplecount_api(request):
    peoplecounting = PeopleCount.objects.all()
    peoplecounting = transformer.transform(peoplecounting)
    return Response.ok(values=peoplecounting)

    

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n")
        # time.sleep(0.025)


def gen1(iklan):
    while True:
        frame1 = iklan.get_frame()
        # yield (
        #   b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame1 + b"\r\n\r\n"
        # )
        yield (0)


"""
def gen2(camera1):
    while True:
        frame2 = camera1.get_frame()
        yield (
            b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame2 + b"\r\n\r\n"
        )
"""


def video_feed(request):
    return StreamingHttpResponse(
        gen(VideoCamera()), content_type="multipart/x-mixed-replace; boundary=frame"
    )


def iklan_feed(request):
    return StreamingHttpResponse(
        gen1(handling_iklan()), content_type="multipart/x-mixed-replace; boundary=frame"
    )


"""
def peoplecounting_feed(request):
    return StreamingHttpResponse(
        gen2(people_counting()),
        content_type="multipart/x-mixed-replace; boundary=frame",
    )
"""

"""
def webcam_feed(request):
    return StreamingHttpResponse(gen(IPWebCam()),
                                 content_type='multipart/x-mixed-replace; boundary=frame')


def mask_feed(request):
    return StreamingHttpResponse(gen(MaskDetect()),
                                 content_type='multipart/x-mixed-replace; boundary=frame')


def livecam_feed(request):
    return StreamingHttpResponse(gen(LiveWebCam()),
                                 content_type='multipart/x-mixed-replace; boundary=frame')
"""
