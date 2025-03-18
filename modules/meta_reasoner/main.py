import os
import sys
import ast
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import yarp
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
        self.llm_chain = None
        self.participants = None
        self.record_history = []
        self.masked_record = ''

        self.record_input_port = yarp.BufferedPortBottle()
        self.debug_chat_port = yarp.BufferedPortBottle()
        self.output_port = yarp.Port()
        self.rpc_output_port = yarp.RpcClient()

        self.llm = AzureChatOpenAI(
            openai_api_version="2024-10-21",
            deployment_name="contact-MultipartyConversation_gpt4omini",
            temperature=0.5,
            max_tokens=128,
        )

    def configure(self, rf):

        # Open ports
        self.record_input_port.open("/metaReasoner/record:i")
        self.debug_chat_port.open("/metaReasoner/debug_chat:i")
        self.output_port.open("/metaReasoner/output:o")
        self.rpc_output_port.open("/metaReasoner/rpc")

        # connect ports
        yarp.Network.connect('/conversationParser/record:o', '/metaReasoner/record:i')

        # Initialize prompt
        self.setup_prompt_template()

        print("Configuration Done")
        return True

    def setup_prompt_template(self):
        """
        setup the llm agent prompt template to be used for reasoning in determining the addressee of the current sentence.
        """
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=(
                        f"You are a robot assistant taking part in a multi-party conversation. "
                        f"The participants of the conversation are: {self.participants}. "
                        f"Based on the conversation history and the current sentence, decide who is the addressee of the current sentence."
                        f"The addressee must be always a name in the participants list, try to infer the name from the list of participats.\n\n"
                        "Conversation history: {conversation_history}. Answer by saying only the name of the addressee."
                    )
                ),
                ("human", "{question}"),
            ])


        self.llm_chain = self.prompt_template | self.llm
        return True
    
    def get_conversation_participants(self):
        """ read from the face_id module to get the participants of the conversation."""
        #TODO: add here the read function
        #TODO: in the future read from the spacial memory
        self.participant = ['Alice', 'Bob', 'Mary', 'John', 'Robot']


    def interruptModule(self):
        self.record_input_port.interrupt()
        self.output_port.interrupt()
        self.rpc_output_port.interrupt()
        return True


    def close(self):
        self.record_input_port.close()
        self.output_port.close()
        self.rpc_output_port.close()
        return True


    def respond(self, command, reply):
        if command.toString() == "reasoning":
            print("\n\033[92mREASONING 🚀\033[0m")
        return True

    def getPeriod(self):
        return 1.0


    def updateModule(self):
        #function to extrapolate parserù
        if self.record_input_port.getInputCount():
            masked_record = self.read_record()

            if masked_record is not None:

                print("\033[91mINVOKING LLM META-REASONER\033[0m")

                conversation_history = [] #"\n".join(self.updated_record_history) if self.updated_record_history else "No previous messages."

                # Invoke LLM
                reply = self.llm_chain.invoke({
                    "question": masked_record,
                    "participants": self.get_conversation_participants(),
                    "conversation_history": conversation_history
                })

                print(f"\033[96m[META REASONER] The addresse is: {reply.content}\033[0m")
                llm_addressee = reply.content

                # update record history with llm addressee output
                updated_entry = f"{self.record_history[-1]} to {llm_addressee}"
                self.record_history[-1] = updated_entry

        return True


    def read_record(self):
        
        record = self.record_input_port.read(shouldWait=True)
        if record:
            # given this string, we can parse it to a dictionary
            # e.g.
            # Alice, Hi Bob!
            # to Alice said: 'Hi Bob!'
            r = record.toString()
            # split the message ino a list of strings, use the comma as separator
            parsed_message = r.split(",")

            print(parsed_message)
            masked_record = f"{parsed_message[0]} said: '{parsed_message[1]}'"
            self.record_history.append(masked_record)
            print(f"\033[93mReceived from Parser: {masked_record}\033[0m")
            return masked_record
        else:
            print("No record received")
            return None

if __name__ == "__main__":
    yarp.Network.init()
    module = MetaReasoner()
    rf = yarp.ResourceFinder()
    rf.setVerbose(True)
    rf.configure(["--from", "config.ini"])
    module.runModule(rf)
    yarp.Network.fini()

