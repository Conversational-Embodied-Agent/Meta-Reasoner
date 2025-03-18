import os
import sys
import yarp
import plotly
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import cv2
from radar import RadarPlotApp

def print_error(msg):
    print("\033[91m[ERROR]:", msg, "\033[0m")

def print_warning(msg):
    print("\033[93m[[WARNING]", msg, "\033[0m")


class SpatialMemory(yarp.RFModule):

    def __init__(self):
        """ This module is a llm-powered reasoner to assess addressee identity and conversation dynamics."""
        super(SpatialMemory, self).__init__()
        self.var = None

        self.input_port = yarp.BufferedPortBottle()
        self.output_port = yarp.Port()
        self.rpc_output_port = yarp.RpcClient()


    def configure(self, rf):

        module_name = "spatialmemory"

        # Open ports
        self.input_port.open(f"/{module_name}/input:i")
        self.output_port.open(f"/{module_name}/gaze:o")
        self.rpc_output_port.open(f"/{module_name}/rpc")

        # connect ports
        yarp.Network.connect("/faceID/annotations:o","/spatialmemory/input:i")
        #yarp.Network.connect("/spatialmemory/input:i","/faceID/annotations:o")

        # Initialize prompt
        #self.setup_gaze_controller()

        # initialize the radar plot visualization
        self.radarplot = RadarPlotApp()
            # Avvia il server in background
        self.radarplot.start_server(open_browser=True)

        print("Configuration Done")
        # test the radar plot
        for i in range(1000):
            yarp.delay(0.1)

            # face_ang, neck_ang, area_ang
            self.radarplot.update_data(90, 0, 0.5)

        print("Configuration Done")
        return True

    def setup_gaze_controller(self):
        """ open iKinGazeCtrl device and get the IGazeControl interface """
        optGaze = yarp.Property()
        optGaze.put("device", "gazecontrollerclient")
        optGaze.put("remote", "/iKinGazeCtrl")
        optGaze.put("local", "/spatialmemory/gaze:o")

        self.clientGaze = yarp.PolyDriver()
        self.clientGaze.open(optGaze)
        if not self.clientGaze.isValid():
            print_error("Gaze controller client device is not available. Check if the gazecontrollerclient is running.")
            exit()

        self.GazeControl = self.clientGaze.viewIGazeControl()
        return True

    def interruptModule(self):
        self.input_port.interrupt()
        self.output_port.interrupt()
        self.rpc_output_port.interrupt()
        return True


    def close(self):
        try:
            self.input_port.close()
            self.output_port.close()
            self.rpc_output_port.close()
        finally:
            # Assicurati di fermare il server quando hai finito
            self.radarplot.stop_server()
        return True


    def respond(self, command, reply):
        return True

    def getPeriod(self):
        return 0.2


    def updateModule(self):

        if self.input_port.getInputCount():
            faces = self.input_port.read(shouldWait=True)
            if faces is not None:
                for person in range(faces.size()):
                    faces = faces.get(person)
                    box = faces.find("box")
                    box = box.asList()
                    # get centroid of the face
                    top_x, top_y, bot_x, bot_y = box.get(0).asInt16(), box.get(1).asInt16(), box.get(2).asInt16(), box.get(3).asInt16()
                    x = (top_x + bot_x) / 2
                    y = (top_y + bot_y) / 2
                    
                    print(f"x: {x}, y: {y}")
                    area = (bot_x - top_x) * (bot_y - top_y)
                    print(f"area: {area}")

                    #area percentage
                    area_percentage = area / (320 * 240)
                    print(f"area percentage: {area_percentage}")

                    self.write_spatial_memory(x,y, area)

                print(faces.toString())
                
            
        return True
    
    def write_spatial_memory(self, x, y, area):
        # create a yarp::sig::Vector const &
        frame_pos = yarp.Vector(3)

        # x = 320/2  # Pixel coordinates of the object in the image
        # y = 240/2  # Pixel coordinates of the object in the image
        z = 0.7  # Distance from the camera to the object in meters

        angles = yarp.Vector(3)

        px = yarp.Vector(2)  # Create a vector of size 2
        px[0] = x
        px[1] = y

        if self.GazeControl.get3DPoint(0, px, 0.7, frame_pos):
            self.GazeControl.getAnglesFrom3DPoint(frame_pos, angles)
            #print(f"Angles: {angles.toString()}")
            #print in green the first angle
            print("\033[92m", angles[0], "\033[0m")

            #print("3D point in the camera frame: ", frame_pos.toString())

            #self.radarplot(angles[0], area)
        return True


if __name__ == "__main__":
    yarp.Network.init()
    module = SpatialMemory()
    rf = yarp.ResourceFinder()
    rf.setVerbose(True)
    rf.configure(["--from", "config.ini"])
    module.runModule(rf)
    yarp.Network.fini()


    






