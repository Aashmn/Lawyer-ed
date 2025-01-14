from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.schema import MetadataMode
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from typing import List
from llama_index.readers.file.docs import DocxReader
import os
from llama_index.readers.file.docs import DocxReader

# Function to load all .docx files in a directory
def load_docx_from_directory(directory_path):
    documents = []
    print(f"Checking files in: {directory_path}")  # Debugging
    for filename in os.listdir(directory_path):
        print(f"Found file: {filename}")  # Debugging
        file_path = os.path.join(directory_path, filename)

        # Check if the file is a .docx file or has no extension
        if filename.endswith('.docx') or filename.endswith('.doc'):
            try:
                # Load .docx file content
                doc_content = DocxReader().load_data(file_path)
                # Ensure documents are flattened into a single list
                if isinstance(doc_content, list):
                    documents.extend(doc_content)  # Flatten if the result is a list
                else:
                    documents.append(doc_content)  # Add single document
                print(f"Processed file: {file_path}")  # Debugging
            except Exception as e:
                print(f"Error processing {file_path}: {e}")  # Handle errors
    return documents

# Load and index documents from the folder you pass
directory_path = r'C:\Users\aashm\OneDrive\Desktop\App Project\data\transcribed_data'
documents = load_docx_from_directory(directory_path)

# Check if documents are loaded
if not documents:
    print("No documents found. Please check the folder path and file contents.")
else:
    print(f"Loaded {len(documents)} documents.")

# Load and index documents
parser = SimpleNodeParser.from_defaults()
nodes = parser.get_nodes_from_documents(documents)

# Assume each node has a 'topic', 'position', 'file_name', and 'file_path' in its metadata
for i, node in enumerate(nodes):
    node.metadata['position'] = i
    node.metadata['file_name'] = f"file_{i}.txt"  # Example file name for each node
    node.metadata['file_path'] = f"/path/to/file_{i}.txt"  # Example file path
    node.excluded_llm_metadata_keys = ['file_path']  # Exclude file_path from LLM metadata

index = VectorStoreIndex(nodes)

def get_topic_position(query: str) -> int:
    # This function should identify the topic and return its position
    retriever = VectorIndexRetriever(index=index, similarity_top_k=1)
    retrieved_nodes = retriever.retrieve(query)
    
    # Check if retrieved_nodes is not empty
    if not retrieved_nodes:
        print("No matching documents found for the query.")
        return -1  # or handle it as needed (e.g., raise an exception or return a default value)
    
    return retrieved_nodes[0].metadata['position']

def filter_nodes(nodes: List, position: int) -> List:
    return [node for node in nodes if node.metadata['position'] <= position]

def group_nodes(nodes: List) -> dict:
    grouped = {}
    for node in nodes:
        topic = node.metadata.get('topic', 'Unknown')
        if topic not in grouped:
            grouped[topic] = []
        grouped[topic].append(node)
    return grouped

def chatbot():
    # Get query from user input
    query = input("Enter your query: ")

    # Get the position of the topic from the query
    topic_position = get_topic_position(query)

    if topic_position == -1:
        print("No topic found matching the query. Please try a different query.")
        return  # Exit early if no matching topic is found

    # Filter the nodes before the topic position and the current one
    filtered_nodes = filter_nodes(index.docstore.docs.values(), topic_position)

    # Group the nodes separately (apply any specific grouping logic here)
    grouped_nodes = group_nodes(filtered_nodes)

    # Create a new index with the filtered and grouped nodes
    new_index = VectorStoreIndex(list(filtered_nodes))
    
    # Create a retriever and postprocessor
    retriever = VectorIndexRetriever(index=new_index, similarity_top_k=2)
    postprocessor = MetadataReplacementPostProcessor(target_metadata_key="topic")
    
    # Create a query engine with the retriever and postprocessor
    query_engine = RetrieverQueryEngine(retriever, node_postprocessors=[postprocessor])

    # Query the engine and get the response
    response = query_engine.query(query)

    # Check if response exists
    if len(response.source_nodes) == 0:
        print("No results found in the filtered nodes.")
        return

    # Extract the first source node
    source_node = response.source_nodes[0].node
    node_content = source_node.get_content()

    # Metadata
    file_name = source_node.metadata.get('file_name', 'Unknown File')
    node_position = source_node.metadata.get('position', 'Unknown Position')
    file_path = source_node.metadata.get('file_path', 'Unknown Path') if 'file_path' in source_node.excluded_llm_metadata_keys else 'No File Path'

    # Output the response and relevant metadata
    print(f"Answer: {response}")
    print(f"File Name: {file_name}")
    print(f"Node Number: {node_position}")
    print(f"File Path: {file_path}")

# Run the chatbot
chatbot()