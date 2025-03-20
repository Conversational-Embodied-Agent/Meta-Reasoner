import os
import sys
import ast
import yarp
import pandas as pd

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, BaseMessage

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")


class MetaReasoner(yarp.RFModule):

    def __init__(self):
        """ This module is a llm-powered reasoner to assess addressee identity and conversation dynamics."""
        super(MetaReasoner, self).__init__()
        self.log_folder = "/usr/local/src/robot/Codes/Meta-Reasoner/conversations_log"
        self.llm_chain = None
        self.utterance_end = False
        self.record_history = []
        self.interaction_end = False
        self.history_dataframe = pd.DataFrame(columns=["Timestamp", "Speaker", "Utterance", "Addressee"])
        self.participants = ['Giulia', 'Luca', "Eizaburo", 'Robot']

        # handle port for the RFModule
        self.handle_port = yarp.Port()
        self.attach(self.handle_port)

        self.rpc_spatial_memory = yarp.RpcClient()
        self.rpc_spatial_memory.setRpcMode(True)
        
        self.faceID_input_port = yarp.BufferedPortBottle()
        self.speech_recognition_input_port = yarp.BufferedPortBottle()
        self.speech_output_port = yarp.Port()  
        self.fixation_coord_output = yarp.Port()

        self.llm = AzureChatOpenAI(
            openai_api_version="2024-10-21",
            deployment_name="contact-MultipartyConversation_gpt4omini",
            temperature=0.5,
            max_tokens=128,
        )

    def configure(self, rf):

        self.module_name = rf.check("name",
                                    yarp.Value("metaReasoner"),
                                    "module name (string)").asString()

        # Open ports
        self.handle_port.open("/" + self.module_name)
        self.rpc_spatial_memory.open("/" + self.module_name + "/rpc_memory")
        #self.debug_chat_port.open("/" + self.module_name + "/debug_chat:i")
        self.speech_recognition_input_port.open("/" + self.module_name + "/speech_recognition:i")
        self.speech_output_port.open('/' + self.module_name + '/speech_output:o')
        self.fixation_coord_output.open('/' + self.module_name + '/fixation_coord:o')
        
     

        # connect ports (for debug only)
        yarp.Network.connect('/metaReasoner/rpc_memory:o', '/metaReasoner/record:i')
        yarp.Network.connect('/speech2text/text:o', '/metaReasoner/speech_recognition:i')
        yarp.Network.connect('/metaReasoner/speech_output:o', '/text2speech/text:i')
        #yarp.Network.connect("/metaReasoner/rpc_spatial_memory", "/spatialmemory/rpc")
        yarp.Network.connect("/metaReasoner/fixation_coord:o", "/iKinGazeCtrl/xd:i")

        # Initialize prompt
        self.setup_prompt_template()

        print("Configuration Done")
        return True

    def setup_prompt_template(self):
        """
        setup the llm agent prompt template to be used for reasoning in determining the addressee of the current sentence.
        """
        self.prompt_template_addressee = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=(
                        f"The participants of the conversation are: {self.participants}. "
                        f"Based on the current speaker, sentence and the conversation history, decide who is the addressee of the current sentence."
                        f"The addressee must be always a name in the participants list, try to infer the name from the list of participats. Answer by saying only the name of the addressee.\n\n"
                        f"Conversation history: {self.record_history}. "
                    )
                ),
                ("human", "{question}"),
            ])
        
        self.prompt_template_answer = ChatPromptTemplate.from_messages([
                SystemMessage(
                    content=(
                        f"You are a robot assistant taking part in the conversation."
                        f"Provide a proper answer according to the current sentence and the conversation history : {self.record_history}."
                        f"Make explicit who is the addressee of your sentence among the participants. The addressee must be always a name in the participants list: {self.participants}"
                        f"Use the format: MY ANSWER: []. MY ADDRESSEE: []"
                        )
                ),
                ("human", "{question}"),
            ])
        
        self.llm_chain_addressee = self.prompt_template_addressee | self.llm
        self.llm_chain_answer = self.prompt_template_answer | self.llm
        return True
    

    def send_to_speech2text(self, msg):
        """
        Send a sentence to the speech2text module
        """
        speak_bottle = yarp.Bottle()
        speak_bottle.clear()
        speak_bottle.addString(msg)
        self.speech_output_port.write(speak_bottle)
        print(f"\033[94m[DEBUG] Sending cmd to Speech2Text: {speak_bottle.toString()}\033[00m")
        return True
    
    def get_conversation_participants(self):
        """ 
        read from the face_id module to get the participants of the conversation.
        """
        yarp.Network.connect("/metaReasoner/rpc_memory", "/spatialmemory/rpc")
        cmd_bottle = yarp.Bottle()
        response = yarp.Bottle()
        cmd_bottle.clear()
        response.clear()
        cmd_bottle.addString("get")
        cmd_bottle.addString("type")
        cmd_bottle.addString("person")
        self.rpc_spatial_memory.write(cmd_bottle, response)
        if response != "nack":
            print(f"\033[94m[DEBUG] Sending cmd to spatial memory: {cmd_bottle.toString()}. Received response: {response.toString()}\033[00m")
            self.participants = [response.get(i).asString() for i in range(response.size())]
            print(f"\033[93mParticipants are: {self.participants}\nWaiting for Speaker!\033[0m")
        else:
            print(f"\033[94m[DEBUG]No one in sight!\033[00m")
        return
        

    def get_utterance_and_speaker_id(self):
        """ read from the speech recognition module to get the utterance and speaker ID."""
        speaker_id = None
        utterance = None
        #TODO: think about doing check for a flag to trigger reasoning
        if self.speech_recognition_input_port.getInputCount():
            bottle = self.speech_recognition_input_port.read(shouldWait=True)
            if bottle:
                utterance = bottle.get(0).asList().get(0).asString()
                speaker_id = bottle.get(0).asList().get(1).asString()
                print(f"\033[93mReceived from Speech Recognition:\n Speaker: {speaker_id}\n Utterance:{utterance}\033[0m")
            else:
                print("No utterance and speaker received")
            return utterance, speaker_id


    def get_vision_addreessee(self):
        """ read from the vision module to get the addressee of the conversation."""
        #TODO: add here the read function
        pass
            
                
    def look_at(self, person):

        # Ask person position to spatial memory
        cmd_bottle = yarp.Bottle()
        response = yarp.Bottle()
        cmd_bottle.clear()
        response.clear()
        cmd_bottle.addString("get")
        cmd_bottle.addString("pos")
        cmd_bottle.addString(person)
        self.rpc_spatial_memory.write(cmd_bottle, response)
        print(f"\033[94m[DEBUG] Sending cmd to spatial memory: {cmd_bottle.toString()}. Received response: {response.toString()}\033[00m")
        
        #command to iKinGaze to look at pos
        x = response.get(0).asFloat64()
        y = response.get(1).asFloat64()
        z = response.get(2).asFloat64()
        print(f"\033[94m[DEBUG] Coordinates are: {x, y, z}\033[00m")
        
        if self.fixation_coord_output.getOutputCount():
            coord_bottle = yarp.Bottle()
            coord_bottle.clear()
            coord_bottle.addFloat64(x)
            coord_bottle.addFloat64(y)
            coord_bottle.addFloat64(z)
            self.fixation_coord_output.write(coord_bottle)
        return


    def parse_info(self, utterance, speaker_id):
        """ Parse the information about conversation to make LLM reasoning about the addressee."""
        record =  f"{speaker_id} said: \"{utterance}\""
        self.record_history.append(record)
        return record
    
    def fill_dataframe(self, speaker_id, utterance, addressee):
         #save in pandas dataframe
        new_row = pd.DataFrame({
                "Timestamp": [pd.Timestamp.now()],
                "Speaker": [speaker_id],
                "Utterance": [utterance],
                "Addressee": [addressee]
            })
        # Append the new row to the existing DataFrame
        self.history_dataframe = pd.concat([self.history_dataframe, new_row], ignore_index=True)
        return
        
    
    def save_conversation_log(self):
        """Save the history dataframe as a CSV file in the conversations_log folder. """
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder, exist_ok=True)
        
        log_file = os.path.join(self.log_folder, f"conversation_history_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv")
        self.history_dataframe.to_csv(log_file, index=False)
        print(f"\033[92mConversation history saved to {log_file}\033[0m")


    def interruptModule(self):
        self.handle_port.interrupt()
        self.rpc_spatial_memory.interrupt()
        self.speech_recognition_input_port.interrupt()
        self.speech_output_port.interrupt()
        self.faceID_input_port.close()
        return True


    def close(self):
        self.handle_port.close()
        self.rpc_spatial_memory.close()
        self.speech_recognition_input_port.close()
        self.speech_output_port.close()
        self.faceID_input_port.close()
        return True


    def respond(self, command, reply):
        reply.clear()

        if command.toString() == "start":
            self.process = True
            print("\n\033[92mREASONING 🚀\033[0m")
            reply.addString(f"received command {command.toString()}")
    
        elif command.toString() == "stop":
            self.save_conversation_log()
            self.process = False
            print("\n\033[92mREASONING STOPPED 🛑\033[0m")   
            reply.addString(f"received command {command.toString()}")   
        
        return True


    def getPeriod(self):
        return 1.0


    def updateModule(self):
        
        # 1: read number of participants, speaker ID and utterance
        self.get_conversation_participants()  
        utterance, speaker_id = self.get_utterance_and_speaker_id()

        # 2: parse the conversation information to give to the LLM
        record = self.parse_info(utterance, speaker_id)
        
        if speaker_id in self.participants:
            print("\033[94m[DEBUG] Looking at the SPEAKER\033[0m")
            self.look_at(speaker_id)

        # 3: invoke the LLM meta-reasoner to ask for text-based addressee 
        reply = self.llm_chain_addressee.invoke({
            "question": record,
            "participants": self.participants,
            "conversation_history": self.record_history
        })

        print(f"\033[91m[META REASONER] The addresse is: {reply.content}\033[0m")
        llm_addressee = reply.content

        # If addressee is the robot, give an answer
        if llm_addressee == 'Robot':
            # Invoke ANSWER LLM
            reply = self.llm_chain_answer.invoke({
                "question": record,
                "conversation_history": self.record_history
            })
            string = reply.content
            print(string)

            # Extract robot_answer and robot_addressee
            robot_answer = string.split("MY ANSWER: [")[1].split("] MY ADDRESSEE")[0]
            robot_addressee = string.split("MY ANSWER: [")[1].split("] MY ADDRESSEE: ")[1]
            print(f"\033[96m[META REASONER] Robot answer is: {robot_answer}, Robot addressee is: {robot_addressee}\033[0m")
            
            #update record history and dataframe for log with robot answer
            updated_entry = f"Robot said {robot_answer} to {robot_addressee}"
            self.record_history[-1] = updated_entry
            self.fill_dataframe(speaker_id="Robot", utterance=robot_answer, addressee=robot_addressee)
            self.send_to_speech2text(robot_answer)
        else:
            if llm_addressee in self.participants:
                print("\033[94m[DEBUG] Looking at the ADDRESSEE\033[0m")
                self.look_at(llm_addressee)

            #update record history and dataframe for log with llm addressee output
            updated_entry = f"{self.record_history[-1]} to {llm_addressee}"
            self.record_history[-1] = updated_entry
            self.fill_dataframe(speaker_id, utterance, llm_addressee)

        print(f"\033[94m[DEBUG] RECORD HISTORY IS: {self.record_history}\033[0m")

        return True
    

if __name__ == "__main__":
    yarp.Network.init()
    module = MetaReasoner()
    rf = yarp.ResourceFinder()
    rf.setVerbose(True)
    rf.configure(["--from", "config.ini"])
    module.runModule(rf)
    yarp.Network.fini()

