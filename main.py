import os
from google import genai
from google.genai import types

# --- CONFIGURATION ---
# PASTE YOUR API KEY HERE
API_KEY = "" 

client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.0-flash" # Fast and capable

# --- AGENT CLASSES ---

class Agent:
    """Base class for a simple agent."""
    def __init__(self, name, role_instruction):
        self.name = name
        self.role_instruction = role_instruction

    def log(self, message):
        print(f"\n🤖 [{self.name}]: {message}")

class SkepticAgent(Agent):
    """Agent 1: Extracts the core claim from the user's input."""
    def process(self, user_text):
        self.log("Analyzing the rumor...")
        prompt = f"""
        You are an expert at identifying the core factual claim in a text.
        Extract the main claim from the following text that needs verifying.
        Return ONLY the claim as a single sentence. 
        
        Text: "{user_text}"
        """
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )
        return response.text.strip()

class ResearcherAgent(Agent):
    """Agent 2: Verifies the claim using Google Search (Grounding)."""
    def process(self, claim):
        self.log(f"Searching Google for: '{claim}'...")
        
        # Define the Google Search Tool
        google_search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        
        prompt = f"Verify this claim with current facts: {claim}"
        
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"]
            )
        )
        
        # Extract the text and grounding metadata (sources)
        # Note: In a full app, we would parse response.candidates[0].grounding_metadata for links.
        return response.text

class EmpathAgent(Agent):
    """Agent 3: Synthesizes findings into a kind, shareable message."""
    def process(self, original_text, facts):
        self.log("Drafting a compassionate response...")
        prompt = f"""
        You are a compassionate fact-checker. 
        Context: A user received this potentially false message: "{original_text}"
        The Facts found by the researcher: "{facts}"
        
        Task: Write a reply to the user. 
        1. Be kind and non-judgmental. 
        2. State clearly if the message is True, False, or Misleading.
        3. Cite the facts provided.
        4. Keep it under 100 words.
        """
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )
        return response.text

# --- SESSION MANAGER ---

class VeritasSession:
    def __init__(self):
        self.skeptic = SkepticAgent("Skeptic", "Extract Claims")
        self.researcher = ResearcherAgent("Researcher", "Verify Facts")
        self.empath = EmpathAgent("Empath", " compassionate synthesis")
        self.history = [] # Memory of past verifications

    def run(self):
        print("🛡️  VERITAS SYSTEM ONLINE")
        print("Paste a rumor, news headline, or WhatsApp forward below (or type 'exit'):")
        
        while True:
            user_input = input("\n> User: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Shutting down.")
                break
            
            # Step 1: Extract Claim
            claim = self.skeptic.process(user_input)
            print(f"   (Identified Claim: {claim})")
            
            # Step 2: Research (Uses Google Search Tool)
            evidence = self.researcher.process(claim)
            
            # Step 3: Final Verdict
            response = self.empath.process(user_input, evidence)
            
            print(f"\n✨ Veritas Output:\n{response}")
            print("-" * 50)
            
            # Save to memory (Session requirement)
            self.history.append({"input": user_input, "verdict": response})

# --- ENTRY POINT ---
if __name__ == "__main__":
    session = VeritasSession()
    session.run()