import os
import sys
import yarp
import plotly
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import cv2


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
        self.setup_gaze_controller()

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
            print("Failed to connect to iKinGaze")
            exit()

        self.GazeControl = self.clientGaze.viewIGazeControl()
        return True

    def interruptModule(self):
        self.input_port.interrupt()
        self.output_port.interrupt()
        self.rpc_output_port.interrupt()
        return True


    def close(self):
        self.input_port.close()
        self.output_port.close()
        self.rpc_output_port.close()
        return True


    def respond(self, command, reply):
        return True

    def getPeriod(self):
        return 1.0


    def updateModule(self):
        #self.write_spatial_memory()
        if self.input_port.getInputCount():
            faces = self.input_port.read(shouldWait=True)
            if faces is not None:
                faces = faces.get(0)
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

            self.radarplot(angles[0], area)
        return True

        
    def radarplot(self, angle, area):

        angle = [angle]
        r = [area]

        # Coordinate polari
        theta = angle 
        #r = np.random.rand(1)

        # Emoji delle faccine
        emojis = ["😀", "😃", "😄", "😁", "😆", "😊"]

        self.fig = go.Figure()

        # Creazione del plot polare
        if self.var is None:
            # put the emoji of a robot in the center
            self.fig.add_trace(go.Scatterpolar(
            r=[0],
            theta=[0],
            mode='text',
            text=["🤖"],
            textfont_size=80,
            name="🤖"
            ))
            self.var = 1
        

        # disable the radial grid
        self.fig.update_polars(radialaxis_showgrid=False)
        # set the 0 to be on top and flip the direction
        self.fig.update_layout(polar_angularaxis_direction="clockwise", polar_angularaxis_rotation=90)

        # disable the labels on the radial axis
        self.fig.update_layout(
        polar=dict(
            radialaxis=dict(
            showticklabels=False,
            ticks=''
            )
        )
        )

        # Aggiunta delle emoji al posto dei punti
        for i in range(len(r)):
            self.fig.add_trace(go.Scatterpolar(
            r=[r[i]],
            theta=[theta[i]],
            mode='text',
            text=[emojis[i]],
            textfont_size=60,
            name=emojis[i]
            ))

        # Aggiorna il grafico senza aprire una nuova finestra
        self.fig.update_traces()

        # convert image to opencv format
        img = cv2.cvtColor(np.array(self.fig), cv2.COLOR_RGB2BGR)
        cv2.imshow("Radar Plot", img)
        cv2.waitKey(0)


if __name__ == "__main__":
    yarp.Network.init()
    module = SpatialMemory()
    rf = yarp.ResourceFinder()
    rf.setVerbose(True)
    rf.configure(["--from", "config.ini"])
    module.runModule(rf)
    yarp.Network.fini()


    






