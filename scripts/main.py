# scripts/main.py

from redundancy_manager import RedundancyManager

def main():
    # Initialize the redundancy manager with the path to the configuration file
    manager = RedundancyManager('config/config.yaml')
    
    # Execute tasks with redundancy logic
    manager.execute_with_redundancy('fetch_urls')
    manager.execute_with_redundancy('scraper')
    manager.execute_with_redundancy('summarizer')
    manager.execute_with_redundancy('tagging')

if __name__ == "__main__":
    main()
