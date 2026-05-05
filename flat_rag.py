import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

def setup_flat_rag(file_path: str):
    # 1. Load và Chunking
    loader = TextLoader(file_path, encoding='utf-8')
    docs = loader.load()
    
    # Text phân chia theo từng câu hoặc đoạn ngắn
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=20)
    splits = text_splitter.split_documents(docs)
    
    # 2. Embedding & Vector DB (Tạo database trong RAM)
    vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    
    return retriever

def flat_rag_query(retriever, query: str) -> str:
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    template = """Hãy trả lời câu hỏi dựa trên ngữ cảnh sau. Nếu không biết, hãy nói không biết.
    Ngữ cảnh: {context}
    Câu hỏi: {question}"""
    prompt = ChatPromptTemplate.from_template(template)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
        
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
    )
    
    return rag_chain.invoke(query).content