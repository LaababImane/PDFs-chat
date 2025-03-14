import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore
from langchain_community.llms import OpenAI
from transformers import pipeline
from langchain_community.llms import GPT4All  
from langchain.memory import ConversationBufferMemory 
from langchain.chains import ConversationalRetrievalChain # type: ignore
from htmlTemplate import css , bot_template , user_template
import os

def get_pdf_text(pdf_docs):
    pdf_text = ""
    for pdf_doc in pdf_docs:
        pdf_reader = PdfReader(pdf_doc)
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()
    return pdf_text

def get_text_chunks(pdf_text):
    text_splitter = CharacterTextSplitter( separator= "\n" , chunk_size= 1000 , chunk_overlap= 200 , length_function= len )  
    chunks = text_splitter.split_text(pdf_text)
    return chunks

def get_vectorstore(chunks):
    # embeddings = OpenAIEmbeddings()
    model_path = "hkunlp/instructor-large"
    embeddings = HuggingFaceInstructEmbeddings(
        model_name= model_path,
        # model_name= 'hkunlp/instructor-xl',
        model_kwargs={"device": "cpu"}  # Change to "cuda" if using GPU
    )
    print("Model loaded successfully!")
    vectorstore = FAISS.from_texts(chunks, embeddings)
    return vectorstore


def get_conversation_chain(vectorstore):
    # llm = ChatOpenAI()
    llm = GPT4All(model="TheBloke/Mistral-7B-Instruct-v0.1-GGUF", device='cpu')
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=vectorstore.as_retriever(), memory=memory)
    return conversation_chain


def handle_user_question(user_question):
    response = st.session_state.conversation({'question' :user_question})
    st.session_state.chat_history = response['chat_history']

    for i , message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(bot_template.replace("{{MSG}}", message.content) , unsafe_allow_html=True)
        else:
            st.write(user_template.replace("{{MSG}}", message) , unsafe_allow_html=True)



def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with multiple PDFs", page_icon=":books:", layout="wide")

    st.write(css, unsafe_allow_html=True) 
    
    if "conversation" not in st.session_state:
        st.session_state.conversation = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
        
    st.header("Chat with multiple PDFs :books:")
    user_question = st.text_input("Ask a question about your PDFs :")
    if user_question:
        handle_user_question(user_question)

    with st.sidebar:
        st.subheader("PDFs")
        pdf_docs = st.file_uploader("Upload PDFs here", type="pdf", accept_multiple_files=True)
        if st.button("Process PDFs") :
            with st.spinner("Processing PDFs..."):
                # get pdf text
                pdf_text = get_pdf_text(pdf_docs)
                # st.write(pdf_text)

                # get text chunks
                chunks = get_text_chunks(pdf_text)
                # st.write(chunks)
                # create vector embeddings
                vectorstore = get_vectorstore(chunks)

                # create conversation 
                st.session_state.conversation = get_conversation_chain(vectorstore)


if __name__ == '__main__':
    main()