import sys
sys.path.append('src')

from pipelines.query_pipeline import create_query_pipeline
from common.document_store import initialize_document_store, get_qdrant_store

def test_pipeline():
    # Create the pipeline using our code-defined pipeline function
    print("Creating pipeline...")
    pipeline = create_query_pipeline()
    
    # Print success message
    print("Pipeline created successfully!")
    
    # Print pipeline structure information
    print("\nPipeline component names:")
    for component_name in pipeline.graph.nodes:
        print(f"  - {component_name}")

        # Test running the pipeline with a sample query
    try:
        print("\nTesting pipeline with a sample query...")
        
        # Create inputs for each component that needs the query
        sample_query = "What is Haystack?"
        inputs = {
            "query_embedder": {"text": sample_query},
            "bm25_retriever": {"query": sample_query},
            "prompt_builder": {"query": sample_query},
            "answer_builder": {"query": sample_query}
        }
        
        # Run the pipeline
        results = pipeline.run(inputs)
        
        print(f"Pipeline run successful. Result keys: {results.keys()}")
        
        # Check if we got an answer
        if "answer_builder" in results and "answers" in results["answer_builder"]:
            print(f"Got answer: {results['answer_builder']['answers'][0]}")
        else:
            print(f"No answer generated. Available results: {results}")
            
    except Exception as e:
        print(f"Error running pipeline: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_pipeline() 