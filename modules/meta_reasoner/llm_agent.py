import os
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


from dotenv import load_dotenv

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")


class LLMAgent:

    def __init__(
        self,
        temperature: float,
        max_tokens: int,
    ) -> None:

        self.temperature = temperature
        self.max_tokens = max_tokens


        #For the prompt
        self.system_prompt= ("You are a robot assistant taking part in a multi-party conversation. The participants of the conversations are {participants}."
                             "Based on the conversation_history and the current sentence decide who is the addressee of the current sentence."
                             "Converstaion_history: {parser}"
                             "Current sentence: {input}")
        self.participants = [] #decide where to update the number of participants
        self.parser = []

        self.setup_llm()
        self.setup_prompt_template()


    def setup_llm(self) -> None:
        """
        setup the llm agent parameters
        """
        self.llm = AzureChatOpenAI(
            openai_api_version="2024-10-21",
            deployment_name="contact-MultipartyConversation_gpt4omini",
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )


    def setup_prompt_template(self):
        """
        setup the llm agent parameters
        """
        prompt_template_addresee = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            #("placeholder", "{chat_history}"),
            ("human", "{input}") #input is the last line of the parser
        ]).partial(participants=self.participants, parser=self.parser)


        return prompt_template_addresee

    def decide_addressee(self, user_input):

        #function to extrapolate parser
        #function to extrapolate user_input

        main_prompt = self.setup_prompt_template()
        chat_chain = main_prompt | self.llm

        answer = chat_chain.invoke({"input": user_input})
        print(answer)

