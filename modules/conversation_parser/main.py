import yarp
import os
import pandas as pd
import json
from datetime import datetime
import logging


class ConversationParser(yarp.RFModule):
    def __init__(self):
        super(ConversationParser, self).__init__()
        self.data_records = []
        self.interaction_end = False #todo: understand who should send/trigger this
        self.json_path = 'fake_dictionnaries.JSON'#todo: this is only for debugger purpose
        self.log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../parse_log')

        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

        self.spatial_memory_input_port = yarp.BufferedPortBottle()
        self.speech_recognition_input_port = yarp.BufferedPortBottle()
        self.output_port = yarp.Port()
        self.handle_port = yarp.Port()
        self.attach(self.handle_port)

        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def configure(self, rf):
        # connect yarp ports
        self.handle_port.open('/conversationParser')
        self.spatial_memory_input_port.open("/conversationParser/dict:i")
        self.speech_recognition_input_port.open("/conversationParser/utterance:i")
        self.output_port.open('/conversationParser/record:o')


        #todo: add to xml file
        yarp.Network.connect('/spatial_memory/dict:o', '/conversationParser/dict:i')
        yarp.Network.connect('/SpeechToText/speech_recognition:o', '/conversationParser/utterance:i')

        print("Configuration Done")
        return True


    def interruptModule(self):
        self.spatial_memory_input_port.interrupt()
        self.speech_recognition_input_port.interrupt()
        self.handle_port.interrupt()
        return True

    def close(self):
        self.spatial_memory_input_port.close()
        self.speech_recognition_input_port.close()
        self.handle_port.close()
        return True

    def respond(self, command, reply):
        reply.clear()
        if command.toString() == "conversation_end":
            self.interaction_end = True
            reply.addString(f"received command {command.toString()}")
        return True

    def getPeriod(self):
        return 1.0

    def updateModule(self):
        spatial_memory_dict = self.read_spatial_memory()
        if spatial_memory_dict is not None:
            #print to check if it is reading correctly
            logging.info(f"Spatial Memory: {spatial_memory_dict}")
            # create a structured record of the conversation dynamic and send to meta reasoner
            self.parse_info(spatial_memory_dict)

        if self.interaction_end:
            self.save_log_file()
            self.interaction_end = False
            logging.info("Conversation Interaction Ended. Saving Logs")
        return True

    #TODO: understand if the spatial memory dictionary should be read from a yarp port or in a different way
    def read_spatial_memory(self):
        """
        Read spatial memory dictionnary (for simulation we use a JSON file)

        :return: json data
        """
        try:
            with open(self.json_path, 'r') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print(f"The file at {self.json_path} was not found.")
        except json.JSONDecodeError:
            print(f"The file at {self.json_path} is not a valid JSON file.")
        except Exception as e:
            print(f"An error occurred: {e}")


    #todo: check utterance readings is in sync with spatial memory
    def read_utterance(self):
        """
        Read utterance from speech2Text

        :return:
        """
        if self.speech_recognition_input_port.getInputCount():
            utterance = self.speech_recognition_input_port.read(shouldWait=True)
            if utterance:
                speaker_input = utterance.toString()
                logging.info(f"Utterance: {speaker_input}")
                return speaker_input
        return None


    def parse_info(self, input_data):
        """
        Create instances of the conversation log for each conversation turn.
        :param input_data from spatial memory
        :return: populate self.data_records
        """
        # Simulate the current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Extract speaker and utterance once
        speaker = None
        utterance = None
        addressee = None

        # Loop once to find speaker, addressee, and utterance
        for id_key, attributes in input_data.items():
            if attributes['role'] == 'Speaker':
                speaker = attributes['name']
                utterance = attributes['utterance']
                #utterance = self.read_utterance() or "No utterance received"

            elif attributes['role'] == 'Addressee':
                addressee = attributes['name']

        # Only create a record if a speaker is found
        if speaker and addressee:
            record = {
                "Timestamp": timestamp,
                "Speaker": speaker,
                "Utterance": utterance,
                "Addressee": addressee or "Unknown"
            }
            self.data_records.append(record)
            self.send_record_to_metareasoner(record)

        return

    def send_record_to_metareasoner(self, record):
        record_bottle = yarp.Bottle()
        record_bottle.clear()
        record_bottle.addString(str(record))
        self.output_port.write(record_bottle)

        return True


    def save_log_file(self):
        """
        Saves the conversation records to a CSV file in the specified folder.

        :param log_path: The path to the folder where the CSV file will be saved
        :return: None
        """
        df = pd.DataFrame(self.data_records)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_log_{timestamp}.csv"
        file_path = os.path.join(self.log_path, filename)

        try:
            df.to_csv(file_path, index=False)
            logging.info(f"Data saved to {file_path}")
        except Exception as e:
            logging.error(f"An error occurred while saving the log file: {e}")

        return



if __name__ == "__main__":
    yarp.Network.init()
    module = ConversationParser()
    rf = yarp.ResourceFinder()
    rf.setVerbose(True)
    rf.configure(["--from", "config.ini"])
    module.runModule(rf)
    yarp.Network.fini()