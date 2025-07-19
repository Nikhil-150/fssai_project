from src.orchestrator import FSSAIOrchestrator
import time


def main():
    print("Starting FSSAI PDF Download Process...")
    start_time = time.perf_counter()
    orchestrator = FSSAIOrchestrator()
    orchestrator.run()
    end_time = time.perf_counter()
    duration = end_time - start_time
    print("All downloads completed!")
    print(f"All downloads completed in {duration:.2f} seconds.")


if __name__ == "__main__":
    main()
