# Lab 19: GraphRAG vs Flat RAG

## Giới thiệu dự án

Đây là dự án so sánh hiệu suất giữa hai phương pháp RAG (Retrieval-Augmented Generation):

- **GraphRAG**: Sử dụng đồ thị tri thức để truy vấn đa bước (multi-hop)
- **Flat RAG**: Sử dụng vector database truyền thống (ChromaDB)

## Cấu trúc thư mục

```
lab19_graphrag/
├── .env                  # Chứa API Key (không đưa lên git)
├── .env.example          # Mẫu file cấu hình API
├── .gitignore            # Git ignore rules
├── requirements.txt      # Các thư viện cần cài
├── tech_corpus.txt       # Dữ liệu đầu vào về công ty AI
├── graph_rag.py          # Logic xây dựng GraphRAG (Bước 1, 2, 3)
├── flat_rag.py           # Logic xây dựng Flat RAG truyền thống
├── main_benchmark.py     # Bước 4: Chạy so sánh và báo cáo
├── Bao_cao_Lab19.md      # Báo cáo chi tiết kết quả thực nghiệm
├── knowledge_graph.png   # Ảnh trực quan hóa đồ thị tri thức (tự động tạo)
└── README.md             # File này
```

## Cài đặt

1. Tạo virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

2. Cài đặt dependencies:

```bash
pip install -r requirements.txt
```

3. Cấu hình API key:

```bash
cp .env.example .env
# Chỉnh sửa file .env và thêm OpenAI API key của bạn
```

## Các thành phần chính

### 1. GraphRAG (`graph_rag.py`)

**Bước 1: Entity Extraction**

- Sử dụng LLM (GPT-3.5-turbo) để trích xuất các bộ ba (Subject, Predicate, Object)
- Ví dụ: `(OpenAI, FOUNDED_BY, Sam Altman)`
- Sử dụng Pydantic để đảm bảo cấu trúc output

**Bước 2: Graph Construction**

- Xây dựng đồ thị có hướng (Directed Graph) từ các triples
- Sử dụng NetworkX để quản lý cấu trúc đồ thị

**Bước 3: Graph Querying**

- Trích xuất thực thể chính từ câu hỏi
- Duyệt đồ thị 2-hop từ thực thể đó
- Chuyển đổi subgraph thành văn bản context
- Gửi context cho LLM để trả lời câu hỏi

### 2. Flat RAG (`flat_rag.py`)

- Sử dụng LangChain để load và chunk documents
- Tạo embeddings với OpenAI
- Lưu trữ trong ChromaDB (in-memory)
- Truy vấn tương tự với vector similarity

### 3. Benchmark (`main_benchmark.py`)

- So sánh 20 câu hỏi (bao gồm cả multi-hop và factoid)
- Đo thời gian, chi phí API, và chất lượng trả lời
- Xuất báo cáo dạng markdown và file ảnh đồ thị

## Vai trò của NetworkX trong dự án

### NetworkX là gì?

**NetworkX** là một thư viện Python mạnh mẽ giúp tạo, thao tác, và nghiên cứu các cấu trúc mạng, đồ thị, và thuật toán phức tạp. Trong dự án này, NetworkX đóng vai trò là "bộ não" của GraphRAG.

### NetworkX đã làm gì trong dự án?

#### 1. **Xây dựng Đồ thị Tri thức (Knowledge Graph)**

```python
def build_networkx_graph(triples: list[tuple]) -> nx.DiGraph:
    G = nx.DiGraph()  # Tạo đồ thị có hướng
    for sub, pred, obj in triples:
        G.add_edge(sub, obj, relation=pred)  # Thêm cạnh với thuộc tính
    return G
```

- Tạo **đồ thị có hướng** (`DiGraph`) từ các triples
- Mỗi thực thể (company, person) trở thành **node**
- Mối quan hệ (FOUNDED_BY, INVESTED_IN) trở thành **edge**
- Lưu trữ thông tin quan hệ trong thuộc tính của edge

#### 2. **Truy vấn Đa bước (Multi-hop Querying)**

```python
# Duyệt đồ thị 2-hop từ thực thể được tìm thấy
undirected_G = G.to_undirected()
nearby_nodes = nx.single_source_shortest_path_length(
    undirected_G, matched_node, cutoff=2
).keys()
subgraph = G.subgraph(nearby_nodes)
```

- **BFS (Breadth-First Search)**: Tìm tất cả nodes trong bán kính 2-hop
- **Subgraph extraction**: Lấy phần đồ thị liên quan đến câu hỏi
- **Path finding**: Tìm đường đi giữa các thực thể

#### 3. **Phân tích Đồ thị**

```python
# Các phân tích có thể thực hiện:
print(f"Số nodes: {G.number_of_nodes()}")
print(f"Số edges: {G.number_of_edges()}")
print(f"Các connected components: {nx.number_connected_components(G)}")
```

- Đếm số lượng thực thể và quan hệ
- Phân tích tính liên kết của đồ thị
- Tìm central nodes (nodes quan trọng nhất)

#### 4. **Visual hóa Đồ thị**

```python
def visualize_graph(G: nx.DiGraph, output_path="knowledge_graph.png"):
    pos = nx.spring_layout(G, k=0.5)  # Sắp vị trí nodes
    nx.draw(G, pos, with_labels=True, node_color='lightblue')
    edge_labels = nx.get_edge_attributes(G, 'relation')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
```

- Sắp xếp vị trí nodes tự động (spring layout)
- Vẽ nodes và edges với màu sắc tùy chỉnh
- Hiển thị nhãn quan hệ trên edges

### Tại sao NetworkX quan trọng?

1. **Efficient Graph Operations**: Các thuật toán đồ thị được tối ưu hóa
2. **Flexible Data Structure**: Hỗ trợ nhiều loại đồ thị (có hướng, vô hướng, multi-graph)
3. **Rich Algorithm Library**: BFS, DFS, shortest path, centrality, clustering
4. **Integration Friendly**: Dễ dàng kết hợp với pandas, matplotlib, và các thư viện khác

### Ví dụ thực tế từ dự án

Với dữ liệu về các công ty AI, NetworkX giúp:

- **Tìm đường đi**: `OpenAI ← FOUNDED_BY ← Sam Altman → FOUNDED_BY → ?`
- **Phát hiện mối quan hệ gián tiếp**: `Microsoft → INVESTED_IN → OpenAI ← FOUNDED_BY ← Elon Musk`
- **Truy vấn đa bước**: "Công ty nào được thành lập bởi người từng làm việc tại OpenAI?"

## Chạy dự án

```bash
python main_benchmark.py
```

**Output:**

- Bảng so sánh kết quả giữa GraphRAG và Flat RAG
- File ảnh `knowledge_graph.png`
- Phân tích chi phí và thời gian xử lý

## Kết quả mong đợi

- **GraphRAG**: Tốt hơn cho câu hỏi multi-hop, cần chi phí xây dựng cao hơn
- **Flat RAG**: Nhanh hơn cho câu hỏi factoid đơn giản, hay bị "hallucination" cho câu hỏi phức tạp

## Công nghệ sử dụng

- **LangChain**: Framework cho RAG applications
- **OpenAI**: LLM cho extraction và generation
- **ChromaDB**: Vector database cho Flat RAG
- **NetworkX**: Graph operations và visualization
- **Pydantic**: Data validation
- **Pandas**: Data analysis và reporting

## Lưu ý

- Cần có OpenAI API key để chạy
- Chi phí API sẽ được track và báo cáo
- File `.env` không nên đưa lên version control
