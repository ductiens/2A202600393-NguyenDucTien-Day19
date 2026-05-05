import time
import pandas as pd
from langchain_community.callbacks.manager import get_openai_callback

# Import các hàm từ 2 file vừa tạo
from graph_rag import extract_triples_from_text, build_networkx_graph, visualize_graph, graph_rag_query
from flat_rag import setup_flat_rag, flat_rag_query

def main():
    print("="*50)
    print("BẮT ĐẦU LAB 19: GRAPHRAG VS FLAT RAG")
    print("="*50)

    # 1. Đọc dữ liệu
    with open("tech_corpus.txt", "r", encoding="utf-8") as f:
        text_data = f.read()

    # 2. Xây dựng Flat RAG (Vector DB)
    print("\n[1/4] Đang khởi tạo Flat RAG (ChromaDB)...")
    flat_retriever = setup_flat_rag("tech_corpus.txt")

    # 3. Xây dựng GraphRAG (LLM Extraction + NetworkX)
    print("[2/4] Đang trích xuất Triples và xây dựng GraphRAG...")
    with get_openai_callback() as cb:
        start_time = time.time()
        
        triples = extract_triples_from_text(text_data)
        G = build_networkx_graph(triples)
        
        build_time = time.time() - start_time
        build_tokens = cb.total_tokens
        build_cost = cb.total_cost

    print(f" -> Trích xuất thành công {len(triples)} triples.")
    for t in triples:
        print(f"    {t}")
        
    # Lưu ảnh đồ thị
    visualize_graph(G, "knowledge_graph.png")

    # 4. BENCHMARK (So sánh 5 câu hỏi multi-hop)
    # Lưu ý: Lab yêu cầu 20 câu, ở đây cung cấp 5 câu đa bước điển hình. 
    # Bạn có thể copy-paste thêm vào list này để đủ 20 câu.
    questions = [
        # Nhóm câu hỏi Multi-hop (Khẳng định sức mạnh GraphRAG)
        "Công ty nào được thành lập bởi những người từng làm việc tại OpenAI?",
        "Ai là người sáng lập ra công ty cạnh tranh với Microsoft nhờ khoản đầu tư từ Amazon?",
        "Người sáng lập Mistral AI từng làm việc tại công ty nào trước đây?",
        "Công ty nào mà Google mua lại có người từng thành lập Mistral AI?",
        "Microsoft và Sam Altman có liên kết với nhau qua thực thể nào?",
        "Arthur Mensch và Demis Hassabis có điểm chung gì về nơi làm việc?",
        "Dario Amodei và Arthur Mensch giống nhau ở điểm nào trong sự nghiệp?",
        "Ai đã đầu tư vào công ty do cựu Phó chủ tịch nghiên cứu của OpenAI thành lập?",
        "Elon Musk và Microsoft có liên kết chung với tổ chức nào?",
        "Google và Arthur Mensch có mối liên hệ gián tiếp qua công ty nào?",
        
        # Nhóm câu hỏi Factoid (Cả 2 đều trả lời được)
        "OpenAI được thành lập vào năm nào?",
        "Sam Altman là ai?",
        "Microsoft đã đầu tư bao nhiêu tiền vào OpenAI?",
        "Google đã mua lại công ty nào?",
        "Demis Hassabis là ai?",
        "Arthur Mensch đã lập ra công ty nào vào năm 2023?",
        "Dario Amodei từng giữ chức vụ gì ở OpenAI?",
        "Tại sao Dario Amodei rời OpenAI?",
        "Amazon đầu tư bao nhiêu tiền vào Anthropic?",
        "Mục đích Amazon đầu tư vào Anthropic là gì?"
    ]

    print("\n[3/4] Bắt đầu Benchmark...")
    results = []
    
    for i, q in enumerate(questions, 1):
        print(f"\nQ{i}: {q}")
        
        # Test Flat RAG
        ans_flat = flat_rag_query(flat_retriever, q)
        
        # Test GraphRAG
        ans_graph = graph_rag_query(G, q)
        
        results.append({
            "Câu hỏi": q,
            "Flat RAG (Vector)": ans_flat,
            "Graph RAG (Mạng lưới)": ans_graph
        })
        
        print(f"  - Flat RAG: {ans_flat}")
        print(f"  - GraphRAG: {ans_graph}")

    # 5. XUẤT BÁO CÁO (Deliverables)
    print("\n" + "="*50)
    print("PHẦN 6: BÁO CÁO KẾT QUẢ (DELIVERABLES)")
    print("="*50)
    
    # Bảng so sánh
    df = pd.DataFrame(results)
    print("\n1. BẢNG SO SÁNH (Ghi nhận trường hợp Flat RAG bị ảo giác):")
    print(df.to_markdown(index=False))
    
    # Phân tích chi phí
    print("\n2. PHÂN TÍCH CHI PHÍ XÂY DỰNG ĐỒ THỊ (INDEXING):")
    print(f"- Thời gian chạy (Latency): {build_time:.2f} giây")
    print(f"- Số Token sử dụng (Token usage): {build_tokens} tokens")
    print(f"- Chi phí API (Cost): ${build_cost:.5f}")
    
    print("\nHoàn tất Lab 19! Hãy kiểm tra file 'knowledge_graph.png' trong thư mục.")

if __name__ == "__main__":
    main()