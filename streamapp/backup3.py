from imutils.video import VideoStream
import imutils
import cv2
import os
import urllib.request
import numpy as np
from django.conf import settings
from .models import Iklan, DataCam
from django.db import connection
import time
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from django.contrib.sessions.backends.db import SessionStore
from collections import OrderedDict
from scipy.spatial import distance as dist
from pyimagesearch.centroidtracker import CentroidTracker
from pyimagesearch.trackableobject import TrackableObject
from imutils.video import FPS
import numpy as np
import argparse
import dlib


CLASSES = [
    "background",
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
]

path_proto_mobilenet = "mobilenet_ssd/MobileNetSSD_deploy.prototxt"
path_model_mobilenet = "mobilenet_ssd/MobileNetSSD_deploy.caffemodel"
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe(path_proto_mobilenet, path_model_mobilenet)

writer = None
W = None
H = None

ct2 = CentroidTracker(maxDisappeared=50, maxDistance=60)
trackers = []
trackableObjects = {}
totalFrames = 0
totalleft = 0
totalright = 0

fps = FPS().start()
objek_tracking = OrderedDict()
buffer_objek = []


faceProto = "opencv_face_detector.pbtxt"
faceModel = "opencv_face_detector_uint8.pb"
ageProto = "age_deploy.prototxt"
ageModel = "age_net.caffemodel"
genderProto = "gender_deploy.prototxt"
genderModel = "gender_net.caffemodel"
pathvideo = "videoiklan\%s"

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
ageList = [
    "(0-2)",
    "(4-6)",
    "(8-12)",
    "(15-20)",
    "(25-32)",
    "(38-43)",
    "(48-53)",
    "(60-100)",
]
genderList = ["Male", "Female"]

faceNet = cv2.dnn.readNet(faceModel, faceProto)
ageNet = cv2.dnn.readNet(ageModel, ageProto)
genderNet = cv2.dnn.readNet(genderModel, genderProto)

padding = 20
direktori = os.getcwd()
fullpathvideo = os.path.join(direktori, pathvideo)


s = SessionStore()
b = SessionStore()
data_idloop = s.get("id_loop")
# print(data_idloop)
# frame1 = []
fram2 = []


class CentroidTracker1:
    global s, data_idloop

    def __init__(self, maxDisappeared=50):
        self.nextObjectID = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.stateiklan = OrderedDict()
        self.objek_atribute = OrderedDict()
        self.maxDisappeared = maxDisappeared

    def register(self, centroid, age, gender):
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.stateiklan[self.nextObjectID] = 0
        self.objek_atribute[self.nextObjectID] = [age, gender]
        if self.stateiklan[self.nextObjectID] == 0:
            data_idloop = s.get("id_loop")
            string_tmp = str(self.objek_atribute[self.nextObjectID])
            data_hitung = ambil_datahitung(data_idloop)
            buffer_datahitung = data_hitung + 1
            temp_filter = string_tmp[1:-1]
            data_fix = temp_filter.split(", ")
            # print(data_fix[0])

            kirimdata(data_fix[0], data_fix[1], buffer_datahitung, data_idloop)
            self.stateiklan[self.nextObjectID] = 1
            b = DataCam(
                id_iklan=data_idloop, kode_umur=data_fix[0], kode_gender=data_fix[1]
            )
            b.save()
        self.nextObjectID += 1

    def deregister(self, objectID):
        del self.objects[objectID]
        del self.disappeared[objectID]
        del self.objek_atribute[objectID]

    def update(self, rects, age, gender):

        if len(rects) == 0:
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                # print(self.disappeared[objectID])
                if self.disappeared[objectID] > self.maxDisappeared:
                    print("reset")
                    self.deregister(objectID)
            return self.objects
        # print(self.objects)
        inputCentroids = np.zeros((len(rects), 2), dtype="int")
        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            inputCentroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(0, len(inputCentroids)):
                self.register(inputCentroids[i], age[i], gender[i])

        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            D = dist.cdist(np.array(objectCentroids), inputCentroids)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            usedRows = set()
            usedCols = set()

            for (row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols:
                    continue
                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]

                self.disappeared[objectID] = 0
                usedRows.add(row)
                usedCols.add(col)

            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            if D.shape[0] >= D.shape[1]:
                for row in unusedRows:
                    objectID = objectIDs[row]
                    self.disappeared[objectID] += 1
                    if self.disappeared[objectID] > self.maxDisappeared:
                        self.deregister(objectID)
            else:
                for col in unusedCols:
                    self.register(inputCentroids[col], age[col], gender[col])
        return self.objects

    def ambildataobjek(self):
        return self.objects

    def kirimdata(self, rects):
        self.objects

    def deregisterall(self):
        for objectID in list(self.disappeared.keys()):
            self.deregister(objectID)
        self.nextObjectID = 0


ct = CentroidTracker1()


def highlightFace(net, frame, conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    blob = cv2.dnn.blobFromImage(
        frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False
    )
    net.setInput(blob)
    detections = net.forward()
    faceBoxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            faceBoxes.append([x1, y1, x2, y2])
            cv2.rectangle(
                frameOpencvDnn,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                int(round(frameHeight / 150)),
                8,
            )
            cX = int((x1 + x2) / 2.0)
            cY = int((y1 + y2) / 2.0)
            cv2.circle(frameOpencvDnn, (cX, cY), 5, (255, 255, 255), -1)
    # print(faceBoxes)

    return frameOpencvDnn, faceBoxes


class VideoCamera(object):
    global data_idloop, frame1

    def __init__(self):
        global s, ct, frame2
        self.video = cv2.VideoCapture(1)
        self.loop_facebox = 1

    def __del__(self):
        self.video.release()

    def get_frame(self):
        global frame2
        hasFrame, frame1 = self.video.read()
        frame2 = frame1.copy()
        id_loop = s.get("id_loop")
        print(id_loop)
        # print(data_idloop)
        # print(s.get("id_loop"))
        data_hitung = ambil_datahitung(id_loop)
        if not hasFrame:
            cv2.waitKey()
        resultImg, faceBoxes = highlightFace(faceNet, frame1)
        faceBoxes_copy = faceBoxes.copy()

        if not faceBoxes:
            # loop = 0
            # loop = loop + 1
            print("no face")
        hitung_objek = 0
        jumlahobjek = len(faceBoxes)
        umur = []
        jenis_kelamin = []
        for faceBox in faceBoxes:
            face = frame1[
                max(0, faceBox[1] - padding) : min(
                    faceBox[3] + padding, frame1.shape[0] - 1
                ),
                max(0, faceBox[0] - padding) : min(
                    faceBox[2] + padding, frame1.shape[1] - 1
                ),
            ]

            blob = cv2.dnn.blobFromImage(
                face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False
            )
            genderNet.setInput(blob)
            genderPreds = genderNet.forward()
            gender = genderList[genderPreds[0].argmax()]

            ageNet.setInput(blob)
            agePreds = ageNet.forward()
            age = ageList[agePreds[0].argmax()]
            umur.append(age[1:-1])
            jenis_kelamin.append(gender)
            # print(umur,age)

            cv2.putText(
                resultImg,
                f"{gender}, {age}",
                (faceBox[0], faceBox[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )
        gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        fm = variance_of_laplacian(gray)
        if fm > 100:
            iniasi_objektracker(faceBoxes_copy, resultImg, umur, jenis_kelamin)
        # print(faceBoxes_copy)
        ret, jpeg = cv2.imencode(".jpg", resultImg)
        return jpeg.tobytes()


class handling_iklan(object):
    def __init__(self):
        global s, fullpathvideo, ct, b
        self.i = 0
        self.data = ambil_data()
        # print(self.data)
        self.data1 = self.data[self.i]
        self.url = self.data1[3]
        self.id_loop = self.data1[0]
        self.data_hitung = self.data1[2]
        self.video = cv2.VideoCapture(fullpathvideo % (self.url))
        # self.s = SessionStore()
        s["id_loop"] = self.id_loop
        b["id_loop"] = self.id_loop
        s["data_hitung"] = self.data_hitung
        s.save()
        b.save()

    def __del__(self):
        cv2.destroyAllWindows()

    def get_frame(self):
        success, image = self.video.read()
        if success == True:
            ret, jpeg = cv2.imencode(".jpg", image)
            # return jpeg.tobytes()

            s["id_loop"] = self.id_loop
            b["id_loop"] = self.id_loop
            s["data_hitung"] = self.data_hitung
            s.save()
            b.save()
            # print(s['id_loop'])
        else:
            if self.i == 2:
                self.i = -1
            ct.deregisterall()
            self.i += 1
            self.data1 = self.data[self.i]
            self.id_loop = self.data1[0]
            # print(self.id_loop)
            s["id_loop"] = self.id_loop
            b["id_loop"] = self.id_loop
            s["data_hitung"] = self.data_hitung
            s.save()
            b.save()
            self.video = cv2.VideoCapture(fullpathvideo % (self.url))
            success, image = self.video.read()
            ret, jpeg = cv2.imencode(".jpg", image)
            # return jpeg.tobytes()


def ambil_data():
    cursor = connection.cursor()
    query = """SELECT * FROM iklan ORDER BY RAND()"""
    cursor.execute(query)
    data = cursor.fetchall()
    # print(data)
    if data == None:
        data[0] = 0
        data[1] = ""
        data[2] = ""
        return data
    else:
        return data


def kirimdata(umur, jeniskelamin, hasil_hitung, id_iklan):
    cursor = connection.cursor()
    sql = "UPDATE iklan SET hitung = %d WHERE id= %d" % (hasil_hitung, id_iklan)
    cursor.execute(sql)


def kirimdata_peoplecount(hasil_hitung, id_iklan):
    cursor = connection.cursor()
    sql = "UPDATE iklan SET peoplecount = %d WHERE id= %d" % (hasil_hitung, id_iklan)
    cursor.execute(sql)


def ambil_dataterakhir():
    cursor = connection.cursor()
    sql = "SELECT waktu from data_cam ORDER by id DESC"
    cursor.execute(sql)
    data_waktu = cursor.fetchone()
    if data_waktu == None:
        return 0
    else:
        struct_time = time.strptime(str(data_waktu[0]), "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(struct_time))


def ambil_datahitung(data_idloop):
    global s
    cursor = connection.cursor()
    query = """SELECT hitung FROM iklan where id = %d""" % (data_idloop)
    cursor.execute(query)
    data = cursor.fetchone()
    # print(data[0])
    if data[0] == None:
        data[0] = 0
        return int(data[0])
    else:
        return int(data[0])


def ambil_peoplecount(dataloop):
    print(dataloop)
    cursor = connection.cursor()
    # print(data_idloop)
    query = """SELECT peoplecount FROM iklan where id = %d""" % (dataloop)
    cursor.execute(query)
    data = cursor.fetchone()
    # print(data)
    # print(data[0])
    if data[0] is None:
        data[0] = 0
        return int(data[0])
    else:
        return int(data[0])


def iniasi_objektracker(facebox, img, age, gender):
    # print(facebox)
    objek_raw = np.array(facebox)
    # print(objek_raw)
    objek = ct.update(objek_raw, age, gender)
    for (objectID, centroid) in objek.items():
        text = "ID {}".format(objectID)
        if centroid.all() != None:
            cv2.putText(
                img,
                text,
                (centroid[0] - 10, centroid[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )
    # kirimdata()


def variance_of_laplacian(image):
    return cv2.Laplacian(image, cv2.CV_64F).var()


class people_counting(object):
    global frame1, data_idloop, b, frame2

    def __init__(self):
        # global s
        time.sleep(7)
        global frame2

        # self.video = cv2.VideoCapture(1)
        self.loop_facebox = 1
        self.trackers = []
        self.idloop = b.get("id_loop")
        print(self.idloop)
        # print(idloop)
        self.datapeoplecount = ambil_peoplecount(self.idloop)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        # frame2 = frame1.copy()
        global frame2
        global data_idloop, s, ct2, W, H, totalFrames, totalleft, totalright, net
        self.idloop = b.get("id_loop")
        # print(idloop)
        data_peoplecount = ambil_peoplecount(self.idloop)
        """if not hasFrame:
            print("camera is not connected")
            cv2.waitKey()
        """
        frame3 = imutils.resize(frame2, width=500)
        rgb = cv2.cvtColor(frame3, cv2.COLOR_BGR2RGB)

        if W is None or H is None:
            (H, W) = frame2.shape[:2]

        status = "Waiting"
        rects = []

        if totalFrames % 40 == 0:

            status = "Detecting"
            self.trackers = []

            blob = cv2.dnn.blobFromImage(frame3, 0.007843, (W, H), 127.5)
            net.setInput(blob)
            detections = net.forward()

            for i in np.arange(0, detections.shape[2]):

                confidence = detections[0, 0, i, 2]

                if confidence > 0.7:

                    idx = int(detections[0, 0, i, 1])

                    if CLASSES[idx] != "person":
                        continue

                    box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
                    (startX, startY, endX, endY) = box.astype("int")

                    tracker = dlib.correlation_tracker()
                    rect = dlib.rectangle(startX, startY, endX, endY)
                    tracker.start_track(rgb, rect)

                    self.trackers.append(tracker)

        else:
            for tracker in self.trackers:

                status = "Tracking"

                tracker.update(rgb)
                pos = tracker.get_position()

                startX = int(pos.left())
                startY = int(pos.top())
                endX = int(pos.right())
                endY = int(pos.bottom())

                rects.append((startX, startY, endX, endY))

        # cv2.line(frame1, (W // 2, 0), (W // 2, H), (0, 255, 255), 2)

        objects = ct2.update(rects)

        for (objectID, centroid) in objects.items():  #
            to = trackableObjects.get(objectID, None)

            if to is None:
                to = TrackableObject(objectID, centroid)

            else:

                x = [c[0] for c in to.centroids]
                direction = centroid[0] - np.mean(x)
                to.centroids.append(centroid)

                if not to.counted:
                    if direction < 0 and centroid[0] < W // 2:
                        totalleft += 1
                        to.counted = True

                    elif direction > 0 and centroid[0] > W // 2:
                        totalright += 1
                        to.counted = True
                    kirimdata_peoplecount(self.datapeoplecount + 1, self.idloop)
            trackableObjects[objectID] = to
            # print(objectID)
            text = "ID {}".format(objectID)
            cv2.putText(
                frame3,
                text,
                (centroid[0] - 10, centroid[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )
            cv2.circle(frame3, (centroid[0], centroid[1]), 4, (255, 0, 0), -1)

        info = [
            ("Status", status),
        ]

        for (i, (k, v)) in enumerate(info):
            text = "{}: {}".format(k, v)
            cv2.putText(
                frame2,
                text,
                (10, H - ((i * 20) + 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )
        totalFrames += 1
        ret, jpeg = cv2.imencode(".jpg", frame3)
        return jpeg.tobytes()


'''
if not hasFrame:
                cv2.waitKey()
            resultImg, faceBoxes = highlightFace(faceNet, frame1)
            faceBoxes_copy = faceBoxes.copy()

            if not faceBoxes:
                print("no face")
            hitung_objek = 0
            jumlahobjek = len(faceBoxes)
            umur = []
            jenis_kelamin = []
            for faceBox in faceBoxes:
                face = frame1[
                max(0, faceBox[1] - padding) : min(
                faceBox[3] + padding, frame1.shape[0] - 1
                ),
                max(0, faceBox[0] - padding) : min(
                    faceBox[2] + padding, frame1.shape[1] - 1
                ),
            ]

                blob = cv2.dnn.blobFromImage(
                    face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False
            )
                genderNet.setInput(blob)
                genderPreds = genderNet.forward()
                gender = genderList[genderPreds[0].argmax()]

                ageNet.setInput(blob)
                agePreds = ageNet.forward()
                age = ageList[agePreds[0].argmax()]
                umur.append(age[1:-1])
                jenis_kelamin.append(gender)
                # print(umur,age)

                cv2.putText(
                resultImg,
                f"{gender}, {age}",
                (faceBox[0], faceBox[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )
            gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            fm = variance_of_laplacian(gray)
            if fm > 100:
                iniasi_objektracker(faceBoxes_copy, resultImg, umur, jenis_kelamin)
        ret, jpeg = cv2.imencode(".jpg", resultImg)
        return jpeg.tobytes()

        



        global s, W, H, ct2, net

        hasFrame, frame1 = self.video.read()
        if W is None or H is None:
            (H, W) = frame1.shape[:2]
        status = "Waiting"
        rects = []
        frame2 = frame1.copy()
        id_loop = s.get("id_loop")
        data_hitung = ambil_datahitung(id_loop)
        data_peoplecount = ambil_peoplecount(id_loop)
        frame3 = imutils.resize(frame2, width=500)
        rgb = cv2.cvtColor(frame3, cv2.COLOR_BGR2RGB)

        if totalFrames % 40 == 0:
            status = "Detecting"
            self.trackers = []

            blob = cv2.dnn.blobFromImage(frame2, 0.007843, (W, H), 127.5)
            net.setInput(blob)
            detections = net.forward()

            for i in np.arange(0, detections.shape[2]):

                confidence = detections[0, 0, i, 2]

                if confidence > 0.7:

                    idx = int(detections[0, 0, i, 1])

                    if CLASSES[idx] != "person":
                        continue

                    box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
                    (startX, startY, endX, endY) = box.astype("int")

                    tracker = dlib.correlation_tracker()
                    rect = dlib.rectangle(startX, startY, endX, endY)
                    tracker.start_track(rgb, rect)

                    self.trackers.append(tracker)

        else:
            for tracker in self.trackers:

                status = "Tracking"
                tracker.update(rgb)
                pos = tracker.get_position()
                startX = int(pos.left())
                startY = int(pos.top())
                endX = int(pos.right())
                endY = int(pos.bottom())
                rects.append((startX, startY, endX, endY))

        # cv2.line(frame1, (W // 2, 0), (W // 2, H), (0, 255, 255), 2)

        objects = ct2.update(rects)

        for (objectID, centroid) in objects.items():
            to = trackableObjects.get(objectID, None)

            if to is None:
                to = TrackableObject(objectID, centroid)

            else:

                x = [c[0] for c in to.centroids]
                direction = centroid[0] - np.mean(x)
                to.centroids.append(centroid)

                if not to.counted:
                    self.totalcount += 1
                    to.counted = True
                    kirimdata_peoplecount(self.datapeoplecount + 1, self.idloop)

            trackableObjects[objectID] = to
            # print(objectID)
            # text = "ID {}".format(objectID)
            cv2.putText(
                frame3,
                text,
                (centroid[0] - 10, centroid[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

            cv2.circle(frame3, (centroid[0], centroid[1]), 4, (255, 0, 0), -1)

        info = [
            ("Peoplecounting", self.totalcount),
            ("Status", status),
        ]

        for (i, (k, v)) in enumerate(info):
            text = "{}: {}".format(k, v)
            cv2.putText(
                frame3,
                text,
                (10, H - ((i * 20) + 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                2,
            )
        # totalFrames += 1
        ret, jpeg = cv2.imencode(".jpg", frame3)
        return jpeg.tobytes()

        from django.db import models


class DataCam(models.Model):
    id_iklan = models.IntegerField()
    kode_umur = models.CharField(max_length=30)
    kode_gender = models.CharField(max_length=30)
    waktu = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'data_cam'


class Iklan(models.Model):
    nama = models.TextField()
    hitung = models.IntegerField()
    url = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'iklan'
