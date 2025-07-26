from src.orchestrator import FSSAIOrchestrator
import time


def main():
    print("👋 Hi! Welcome to the FSSAI data processing tool.")
    print("👉 Do you want to work with Segment 1 or Segment 2?")
    print("📌 Type '1' for Segment 1 (Registration + Application)")
    print("📌 Type '2' for Segment 2 (Licence Certificate Only)")

    segment_choice = input("Enter your choice (1 or 2): ").strip()

    if segment_choice in {"1", "2"}:
        print(f"✅ You have selected Segment {segment_choice}.")
        start_time = time.perf_counter()

        orchestrator = FSSAIOrchestrator(segment=segment_choice)
        orchestrator.run()

        duration = time.perf_counter() - start_time
        print(f"✅ All downloads completed in {duration:.2f} seconds.")
    else:
        print("❌ Invalid choice. Please run the script again and enter either 1 or 2.")


if __name__ == "__main__":
    main()
