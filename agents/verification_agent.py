from langchain_openrouter import ChatOpenRouter
from typing import Dict, List
from langchain_core.documents import Document
from config.settings import settings
from .models import VerificationReport


class VerificationAgent:
    def __init__(self):
        """
        Initialize the verification agent with OpenRouter chat model.
        """
        print("Initializing VerificationAgent with OpenRouter...")
        self.model = ChatOpenRouter(
            model=settings.CHAT_MODEL,
            temperature=0.0,
            max_tokens=200,
        )
        # Bind structured output to the model
        self.structured_model = self.model.with_structured_output(VerificationReport)
        print("Model initialized successfully.")

    def generate_prompt(self, answer: str, context: str) -> str:
        """
        Generate a structured prompt for the LLM to verify the answer against the context.
        """
        prompt = f"""
        You are an AI assistant designed to verify the accuracy and relevance of answers based on provided context.

        **Instructions:**
        - Verify the following answer against the provided context.
        - Check for:
        1. Direct/indirect factual support (supported: YES/NO)
        2. Unsupported claims (list any if present)
        3. Contradictions (list any if present)
        4. Relevance to the question (relevant: YES/NO)
        - Provide additional details or explanations where relevant.

        **Answer:** {answer}
        **Context:**
        {context}
        """
        return prompt

    def check(self, answer: str, documents: List[Document]) -> Dict:
        """
        Verify the answer against the provided documents.
        """
        print(f"VerificationAgent.check called with answer='{answer}' and {len(documents)} documents.")

        # Combine all document contents into one string
        context = "\n\n".join([doc.page_content for doc in documents])
        print(f"Combined context length: {len(context)} characters.")

        # Create a prompt for the LLM to verify the answer
        prompt = self.generate_prompt(answer, context)
        print("Prompt created for the LLM.")

        # Call the LLM with structured output
        try:
            print("Sending prompt to the model...")
            verification = self.structured_model.invoke(prompt)
            print("LLM response received.")
        except Exception as e:
            print(f"Error during model inference: {e}")
            # Fallback to default report on error
            verification = VerificationReport(
                supported="NO",
                unsupported_claims=[],
                contradictions=[],
                relevant="NO",
                additional_details="Failed to verify due to model error."
            )

        # Format the verification report
        verification_report = verification.to_report()
        print(f"Verification report:\n{verification_report}")
        print(f"Context used: {context}")

        return {
            "verification_report": verification_report,
            "context_used": context
        }
