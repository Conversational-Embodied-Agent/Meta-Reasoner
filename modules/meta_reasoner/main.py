# some imports
import yarp
import sys

from llm_agent import LLMAgent


def log_message(prefix, msg):
    """Generic logging function used for different types of messages."""
    colors = {
        "ICUB": "\033[91m",
        "YARP-INFO": "\033[92m",
        "DEBUG": "\033[96m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m"
    }
    reset_color = "\033[00m"
    color = colors.get(prefix.upper(), "")
    print(f"{color}{prefix.upper()}:{msg}{reset_color}")



class MetaReasoner(yarp.RFModule):
    """
    Description:

    """

    def __init__(self):
        yarp.RFModule.__init__(self)

        self.temperature = 0.7
        self.max_tokens = 128

    def configure(self, rf):
        # Configure module parameters #
        module_name = rf.check("name",
                               yarp.Value("metaReasoner"),
                               "module name (string)").asString()

        language = rf.check("language",
                            yarp.Value("english"),
                            "language of the prompts (english/italian)").asString()

        # This looks for the prompts.ini in the context of the module
        prompts_path = rf.check('prompts_path',
                                yarp.Value(rf.findFileByName("prompts.ini")),
                                'path containing the ini file with the prompts.').asString()
        log_message("YARP-INFO", f"Reading prompts from context: {prompts_path}")

        # This looks for the configuration file
        conf_path = rf.check('conf_path',
                             yarp.Value(rf.findFileByName("metaReasoner.ini")),
                             'path containing the ini file with the configurations.').asString()
        log_message("YARP-INFO", f"Reading conf from context: {conf_path}")


        ########## LLM MODEL ##########
        self.llm_agent = LLMAgent(
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        log_message("YARP-INFO", "Initialization complete. Yeah!\n")
        return True


    def respond(self, command, reply):
        return


    def getPeriod(self):
        """
           Module refresh rate.
           Returns : The period of the module in seconds.
        """
        return 0.05

    def updateModule(self):
        print("HELLO! WORK IN PROGRESS HERE")

        #call function to read parser
        #call function to update participants

        #call llm to reason about addressee

        #call llm to reason about the answer if robot is the addressee


    def interruptModule(self):
        log_message("YARP-INFO", "stopping the module")
        return True

    def close(self):
        log_message("YARP-INFO", "Closing ports")
        return True



if __name__ == '__main__':

    # Initialise YARP
    if not yarp.Network.checkNetwork():
        print("Unable to find a yarp server, exiting...")
        sys.exit(1)

    yarp.Network.init()
    metaReasonerModule = MetaReasoner()

    rf = yarp.ResourceFinder()
    rf.setVerbose(True)
    rf.setDefaultContext('metaReasoner')
    rf.setDefaultConfigFile('metaReasoner.ini')

    if rf.configure(sys.argv):
        metaReasonerModule.runModule(rf)

    sys.exit()










