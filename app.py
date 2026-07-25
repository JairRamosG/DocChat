import gradio as gr
import hashlib
from typing import List, Dict
import os
from dotenv import load_dotenv

# Load environment variables before importing settings
load_dotenv()

from document_processor.file_handler import DocumentProcessor
from retriever.builder import RetrieverBuilder
from agents.workflow import AgentWorkflow
from config import constants, settings
from utils.logging import logger

# 1) Define some example data 
#    (i.e. question + paths to documents relevant to that question).
EXAMPLES = {
    "Certificado CENLEX": {
        "question": "What is the expiration date of the certificate issued by CENLEX?",
        "file_paths": ["examples/certificado.pdf"]  
    }
}

def main():
    processor = DocumentProcessor()
    retriever_builder = RetrieverBuilder()
    workflow = AgentWorkflow()

    # Define custom CSS for styling
    css = """
    .title {
        font-size: 1.5em !important; 
        text-align: center !important;
        color: #FFD700; 
    }

    .subtitle {
        font-size: 1em !important; 
        text-align: center !important;
        color: #FFD700; 
    }

    .text {
        text-align: center;
    }
    """

    js = """
    function createGradioAnimation() {
        var container = document.createElement('div');
        container.id = 'gradio-animation';
        container.style.fontSize = '2em';
        container.style.fontWeight = 'bold';
        container.style.textAlign = 'center';
        container.style.marginBottom = '20px';
        container.style.color = '#eba93f';

        var text = 'Welcome to DocChat !';
        for (var i = 0; i < text.length; i++) {
            (function(i){
                setTimeout(function(){
                    var letter = document.createElement('span');
                    letter.style.opacity = '0';
                    letter.style.transition = 'opacity 0.1s';
                    letter.innerText = text[i];

                    container.appendChild(letter);

                    setTimeout(function() {
                        letter.style.opacity = '0.9';
                    }, 50);
                }, i * 250);
            })(i);
        }

        var gradioContainer = document.querySelector('.gradio-container');
        gradioContainer.insertBefore(container, gradioContainer.firstChild);

        return 'Animation created';
    }
    """

    with gr.Blocks(theme=gr.themes.Citrus(), title="DocChat ", css=css, js=js) as demo:
        gr.Markdown("## DocChat: RAG Multiagente con Docling y LangGraph", elem_classes="subtitle")
        gr.Markdown("**Nota:** Sólo se aceptan los siguientes formatos: '.pdf', '.docx', '.txt', '.md'", elem_classes="text")

        # 2) Maintain the session state for retrieving doc changes
        session_state = gr.State({
            "file_hashes": frozenset(),
            "retriever": None
        })

        # 3) Layout 
        with gr.Row():
            with gr.Column():
                # Standard input components
                files = gr.Files(label="Upload Documents", file_types=constants.ALLOWED_TYPES)
                question = gr.Textbox(label="Question", lines=3)

                submit_btn = gr.Button("Submit")
                
            with gr.Column():
                answer_output = gr.Textbox(label="Answer", interactive=False)
                verification_output = gr.Textbox(label="Verification Report")


        # 5) Standard flow for question submission
        def process_question(question_text: str, uploaded_files: List, state: Dict):
            """Handle questions with document caching."""
            try:
                if not question_text.strip():
                    raise ValueError("Question cannot be empty")
                if not uploaded_files:
                    raise ValueError("No documents uploaded")

                current_hashes = _get_file_hashes(uploaded_files)
                
                if state["retriever"] is None or current_hashes != state["file_hashes"]:
                    logger.info("Processing new/changed documents...")
                    chunks = processor.process(uploaded_files)
                    retriever = retriever_builder.build_hybrid_retriever(chunks)
                    
                    state.update({
                        "file_hashes": current_hashes,
                        "retriever": retriever
                    })
                
                result = workflow.full_pipeline(
                    question=question_text,
                    retriever=state["retriever"]
                )
                
                return result["draft_answer"], result["verification_report"], state
                    
            except Exception as e:
                logger.error(f"Processing error: {str(e)}")
                return f"Error: {str(e)}", "", state

        submit_btn.click(
            fn=process_question,
            inputs=[question, files, session_state],
            outputs=[answer_output, verification_output, session_state]
        )

    demo.launch(server_name="127.0.0.1", server_port=5000, share=True)

def _get_file_hashes(uploaded_files: List) -> frozenset:
    """Generate SHA-256 hashes for uploaded files."""
    hashes = set()
    for file in uploaded_files:
        with open(file.name, "rb") as f:
            hashes.add(hashlib.sha256(f.read()).hexdigest())
    return frozenset(hashes)

if __name__ == "__main__":
    main()
