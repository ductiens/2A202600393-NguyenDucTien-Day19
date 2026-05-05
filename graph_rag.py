import os
import networkx as nx
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# --- BƯỚC 1: TRÍCH XUẤT THỰC THỂ & QUAN HỆ (Entity Extraction) ---
class Triple(BaseModel):
    subject: str = Field(description="Chủ thể (Node 1)")
    predicate: str = Field(description="Mối quan hệ (Edge)")
    object_: str = Field(alias="object", description="Tân ngữ (Node 2)")

class TriplesList(BaseModel):
    triples: list[Triple]

def extract_triples_from_text(text: str) -> list[tuple]:
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    structured_llm = llm.with_structured_output(TriplesList)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Bạn là một chuyên gia trích xuất dữ liệu đồ thị. Hãy đọc văn bản sau và trích xuất các bộ ba (Subject, Predicate, Object). Tên thực thể nên ngắn gọn, viết hoa đúng chuẩn (ví dụ: OpenAI, Sam Altman). Predicate nên là động từ dạng UPPERCASE (ví dụ: FOUNDED_BY, INVESTED_IN, WORKED_AT)."),
        ("human", "{text}")
    ])
    
    chain = prompt | structured_llm
    result = chain.invoke({"text": text})
    
    # Trả về list các tuples
    return [(t.subject, t.predicate, t.object_) for t in result.triples]

# --- BƯỚC 2: XÂY DỰNG ĐỒ THỊ (Graph Construction) ---
def build_networkx_graph(triples: list[tuple]) -> nx.DiGraph:
    G = nx.DiGraph()
    for sub, pred, obj in triples:
        G.add_edge(sub, obj, relation=pred)
    return G

def visualize_graph(G: nx.DiGraph, output_path="knowledge_graph.png"):
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=0.5)
    
    # Vẽ nodes và edges
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=3000, font_size=10, font_weight='bold', edge_color='gray')
    
    # Vẽ nhãn cho edges (relations)
    edge_labels = nx.get_edge_attributes(G, 'relation')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, font_color='red')
    
    plt.title("Knowledge Graph - Tech Company Corpus")
    plt.savefig(output_path)
    print(f"Đã lưu ảnh đồ thị tại: {output_path}")

# --- BƯỚC 3: DUYỆT ĐỒ THỊ VÀ TRUY VẤN (Querying) ---
def graph_rag_query(G: nx.DiGraph, query: str) -> str:
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    # 3.1 Trích xuất Entity chính từ câu hỏi
    entity_prompt = ChatPromptTemplate.from_messages([
        ("system", "Trích xuất 1 tên thực thể chính (Công ty hoặc Người) xuất hiện trong câu hỏi. CHỈ trả về tên thực thể, không thêm chữ nào khác."),
        ("human", "{query}")
    ])
    seed_entity = (entity_prompt | llm).invoke({"query": query}).content.strip()
    
    # Tìm kiếm gần đúng (xử lý case nhạy cảm)
    matched_node = None
    for node in G.nodes():
        if seed_entity.lower() in str(node).lower():
            matched_node = node
            break
            
    if not matched_node:
        return f"GraphRAG: Không tìm thấy thực thể '{seed_entity}' trong đồ thị."

    # 3.2 Duyệt đồ thị (BFS 2-hop)
    # Lấy tất cả nodes trong bán kính 2 hops (vô hướng để lấy cả quan hệ ngược)
    undirected_G = G.to_undirected()
    nearby_nodes = nx.single_source_shortest_path_length(undirected_G, matched_node, cutoff=2).keys()
    subgraph = G.subgraph(nearby_nodes)
    
    # 3.3 Textualization (Văn bản hóa)
    context_sentences = []
    for u, v, data in subgraph.edges(data=True):
        context_sentences.append(f"{u} {data['relation']} {v}")
    context_text = ". ".join(context_sentences)
    
    # 3.4 Gửi cho LLM trả lời
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", "Hãy trả lời câu hỏi của người dùng CHỈ dựa trên ngữ cảnh mối quan hệ sau đây. Nếu không có thông tin, hãy nói 'Tôi không biết'.\nNgữ cảnh: {context}"),
        ("human", "{query}")
    ])
    answer = (qa_prompt | llm).invoke({"context": context_text, "query": query}).content
    return answer