# Readme.txt

## Table of Contents

- [System Overview](#system-overview)
  - [Core Tasks](#core-tasks)
  - [Task Scheduling and Execution](#task-scheduling-and-execution)
- [File Structure](#file-structure)
  - [Directory Structure](#directory-structure)
  - [Key Directories:](#key-directories)
- [Codebase Walkthrough](#codebase-walkthrough)
  - [Configuration (`config/`)](#configuration-config)
    - [`config_loader.py`](#config_loaderpy)
    - [`config.yaml`](#configyaml)
    - [How Configuration Works](#how-configuration-works)
    - [Example Usage](#example-usage)
  - [Interfaces (`interfaces/`)](#interfaces-interfaces)
    - [Why Interfaces?](#why-interfaces)
    - [Interface Files](#interface-files)
      - [`url_fetcher.py`](#url_fetcherpy)
      - [`scraper.py`](#scraperpy)
      - [`summarizer.py`](#summarizerpy)
      - [`tagger.py`](#taggerpy)
    - [Example: Implementing the `URLFetcher` Interface](#example-implementing-the-urlfetcher-interface)
  - [Scripts (`scripts/`)](#scripts-scripts)
    - [Task-Specific Scripts](#task-specific-scripts)
      - [`fetch_urls`](#fetch_urls)
      - [`scraper`](#scraper)
      - [`summarizer`](#summarizer)
      - [`tagging`](#tagging)
    - [Core Execution Scripts](#core-execution-scripts)
      - [`main.py`](#mainpy)
      - [`redundancy_manager.py`](#redundancy_managerpy)
  - [Utilities (`utils/`)](#utilities-utils)
    - [`db_utils.py`](#db_utilspy)
    - [`logging_utils.py`](#logging_utilspy)
    - [`llm_utils.py`](#llm_utilspy)
    - [Task-Specific Utilities](#task-specific-utilities)
        - [`scraping_utils.py`](#scraping_utilspy)
        - [`summarizer_utils.py`](#summarizer_utilspy)
        - [`tagging_utils.py`](#tagging_utilspy)
        - [`url_fetch_utils.py`](#url_fetch_utilspy)
  - [Task Management (`task_management/`)](#task-management-task_management)
    - [`celery_app.py`](#celery_apppy)
- [How to Use the System](#how-to-use-the-system)
  - [Setting Up the Environment](#setting-up-the-environment)
  - [Running Tasks](#running-tasks)
  - [Monitoring and Logging](#monitoring-and-logging)
- [Advanced Topics](#advanced-topics)
  - [Redundancy Management](#redundancy-management)
    - [`redundancy_manager.py`](#redundancy_managerpy-1)
      - [Initialization (`__init__`)](#initialization-__init__)
      - [Configuration Loading (`load_config`)](#configuration-loading-load_config)
      - [Task Execution (`execute_with_redundancy`)](#task-execution-execute_with_redundancy)
      - [Script Execution (`execute_script`)](#script-execution-execute_script)
      - [Redundancy Logic](#redundancy-logic)
      - [Interaction with Celery](#interaction-with-celery)
      - [Example Usage](#example-usage-1)
    - [Benefits of Redundancy](#benefits-of-redundancy)
  - [Adding New RSS Feeds](#adding-new-rss-feeds)
  - [Customizing LLM Prompts](#customizing-llm-prompts)
  - [Adding New LLM Sources](#adding-new-llm-sources)
- [Troubleshooting](#troubleshooting)
  - [General Troubleshooting Tips](#general-troubleshooting-tips)
  - [Common Issues](#common-issues)
    - [Fetching URLs](#fetching-urls)
    - [Scraping Articles](#scraping-articles)
    - [Summarizing Articles](#summarizing-articles)
    - [Tagging Articles](#tagging-articles)
  - [Debugging Tips](#debugging-tips)
- [Testing Environment](#testing-environment)
  - [Setting Up the Testing Environment](#setting-up-the-testing-environment)
  - [Additional Notes](#additional-notes)

## System Overview

The Article Summarization System is a robust and automated pipeline designed to fetch, process, summarize, tag, and store news articles from various RSS feeds. The system is built with redundancy in mind to ensure reliability and completeness in handling tasks.

### Core Tasks

The system performs the following core tasks:

1.  **`fetch_urls`:** Retrieves new article URLs from enabled RSS feeds listed in the `rss_feed_list` table of the Supabase database. 
2.  **`scraper`:** Scrapes the full content of articles whose URLs were recently fetched.
3.  **`summarizer`:**  Generates summaries of scraped articles using large language models (LLMs). 
4.  **`tagging`:**  Categorizes summarized articles by assigning relevant tags and scores, aiding in content discovery and filtering. 

### Task Scheduling and Execution

The system's task scheduling and execution logic is handled by Celery, a powerful task queue and scheduler.

-   **Timing:**
    -   `fetch_urls` runs every 2 minutes.
    -   `scraper`, `summarizer`, and `tagging` are triggered if `fetch_urls` adds new URLs. They run one after the other, so one starts only when the previous is finished - regardless of success or failure. We have a timeout backup just in case, which terminates a task and moves onto the next if it hits that timeout window.
    -   If no new URLs are added, `scraper`, `summarizer`, and `tagging` still run every 30 minutes.
    -   For all executions of the additional, remaining 3 tasks, they are never called directly but they are added to a queue. This ensures we never call these remaining tasks simultaneously, as they try to write into the same DB record.  
-   **Queue:**
    -   A task queue ensures that the `scraper`, `summarizer`, and `tagging` tasks are executed sequentially, preventing them from running simultaneously and potentially causing conflicts when updating the same database records.
    -   The queue is processed every minute to check for pending tasks.

**In Summary:** The Article Summarization System efficiently and reliably handles the entire pipeline, from fetching URLs to producing tagged summaries. The use of Celery and a task queue ensures smooth scheduling and conflict-free execution, making the system suitable for handling large volumes of articles.

## File Structure

### Directory Structure 

The project's file structure is organized to enhance clarity and maintainability. Here's an overview:

project_root/
├── scripts/               # Contains task-specific Python scripts
│   └── [TASK-NAME]/         # Task-specific subdirectories (e.g., fetch_urls, scraper)
│       └── [SCRIPT-NAME].py # Individual scripts for each task
├── interfaces/            # Python files defining task interfaces
│   └── [INTERFACE].py     # Interface definitions (e.g., URLFetcher, Scraper)
├── utils/                 # Utility functions for various purposes
│   ├── [UTIL].py         # Utility scripts (e.g., db_utils, logging_utils)
├── config/                # Configuration files
│   ├── config_loader.py   # Loads configuration settings
│   ├── config.yaml       # YAML file containing configuration details
└── .env                    # Environment variables (not included in version control)

### Key Directories:

-   **`scripts`:**  This directory houses the core scripts that perform the main tasks of the system (fetching URLs, scraping, summarizing, and tagging). Each task has its own subdirectory with one or more Python scripts implementing the task logic.
-   **`interfaces`:** This directory contains Python interface definitions. Interfaces act as contracts, specifying the methods and properties that each task implementation must provide. This promotes modularity and flexibility in the codebase.
-   **`utils`:** This directory holds various utility functions used across the system. These functions handle database interactions, logging, large language model (LLM) interactions, and other common tasks.
-   **`config`:** This directory stores configuration files. `config.yaml` holds system prompts, API keys (as placeholders), and other settings. `config_loader.py` loads configurations from `config.yaml` and environment variables.
-   **`.env`:** This file contains environment variables for storing sensitive information like API keys and database credentials. It is not tracked in version control to ensure security.

## Codebase Walkthrough

### Configuration (`config/`)

The `config` directory contains the configuration files responsible for loading and managing the settings used throughout the article summarization system.

#### `config_loader.py`

This script is the heart of configuration loading. It serves two primary functions:

1.  **Loads Environment Variables:** It uses the `python-dotenv` library to load environment variables from the `.env` file located in the project root. This is crucial for storing sensitive information like API keys and database credentials securely. 

2.  **Loads Configuration from YAML:** It reads the `config.yaml` file and parses it using the `yaml` library. This file contains the main configuration settings, which are then merged with the loaded environment variables.

    ```python
    # Replace placeholders with actual values from environment variables
    config['supabase']['url'] = os.getenv('SUPABASE_URL')
    config['supabase']['key'] = os.getenv('SUPABASE_KEY')
    config['api_keys']['anthropic'] = os.getenv('ANTHROPIC_API_KEY')
    config['api_keys']['groq'] = os.getenv('GROQ_API_KEY')
    ```

    The script takes care of replacing placeholders (e.g., `${SUPABASE_URL}`) in the YAML configuration with the actual values loaded from environment variables.

#### `config.yaml`

This YAML file serves as the central repository for configuration settings. It is structured into several sections:

-   **`systemPrompt`:**  Defines the system prompts used to guide the large language models (LLMs) during summarization and tagging tasks.
    
-   **`supabase`:** Specifies the Supabase database connection details (URL and key). *Note:* These are placeholders replaced with actual values from `.env` at runtime.
    
-   **`api_keys`:** Stores API keys for the LLM providers (Anthropic and Groq). *Note:* These are also placeholders replaced with actual values from `.env`.
    
-   **`celery`:** Configures Celery settings, including broker URL and result backend.
    
-   **`interfaces`:** Defines the hierarchy of primary and fallback implementations for each task (fetching URLs, scraping, summarizing, and tagging). For example:
    
    ```yaml
    interfaces:
      fetch_urls:
        primary: fetch_urls_feedparser   # Main script for fetching URLs
        fallbacks: []                    # No fallback scripts in this case
    ```

#### How Configuration Works

1.  When any script needs configuration settings, it imports the `load_config` function from `config_loader.py`.
2.  `load_config` reads `.env` and `config.yaml`, merges them, and returns a dictionary containing all the settings.
3.  Scripts can then access the required settings from this dictionary.

#### Example Usage

```python
from config.config_loader import load_config

config = load_config()
supabase_url = config['supabase']['url']
```

### Interfaces (`interfaces/`)

Interfaces in this project serve as blueprints that define the contracts for various components within the system. They establish a set of methods that any class implementing the interface must provide. This ensures consistency, modularity, and flexibility in the codebase.

#### Why Interfaces?

-   **Modularity:** Interfaces allow different parts of the system to be developed independently. As long as a component adheres to the interface, it can be swapped out with another implementation without affecting the rest of the system.
-   **Flexibility:**  Interfaces make it easier to add new functionalities or replace existing ones in the future. You can introduce new scripts for fetching URLs, scraping, summarizing, or tagging by simply implementing the respective interface.
-   **Testability:** Interfaces facilitate the creation of mock objects during testing, allowing you to isolate and test individual components.

#### Interface Files

Each file in the `interfaces` directory defines an interface for a specific task within the article summarization system:

-   **`url_fetcher.py`:**  Defines the `URLFetcher` interface. This interface specifies a single method:

    ```python
    @abstractmethod
    def fetch_and_store_urls(self):
        """
        Fetch and store URLs.

        Returns:
            None
        """
        pass
    ```

    Any class that implements `URLFetcher` must provide an implementation for `fetch_and_store_urls`. This method is responsible for fetching new URLs from sources like RSS feeds and storing them in the database.

-   **`scraper.py`:** Defines the `Scraper` interface. This interface specifies a single method:

    ```python
    @abstractmethod
    def scrape(self, url):
        """
        Scrape content from the given URL.

        Args:
            url (str): The URL to scrape content from.

        Returns:
            str: The scraped content.
        """
        pass
    ```

    Any class that implements `Scraper` must provide an implementation for `scrape`. This method is responsible for extracting the content from a given URL.

-   **`summarizer.py`:** Defines the `Summarizer` interface. This interface specifies a single method:

    ```python
    @abstractmethod
    def summarize(self, content):
        """
        Summarize the given article content.

        Args:
            content (str): The article content to summarize.

        Returns:
            dict: A dictionary containing the summary parts (intro, bullet points, conclusion).
        """
        pass
    ```

    Any class that implements `Summarizer` must provide an implementation for `summarize`. This method is responsible for generating a summary of the given article content.

-   **`tagger.py`:** Defines the `Tagger` interface. This interface specifies a single method:

    ```python
    @abstractmethod
    def tag(self, summary):
        """
        Tag the given article summary.

        Args:
            summary (dict): The summarized article content to tag.

        Returns:
            dict: A dictionary containing tags and their relevancy scores.
        """
        pass
    ```

    Any class that implements `Tagger` must provide an implementation for `tag`. This method is responsible for assigning tags to the given article summary.

#### Example: Implementing the `URLFetcher` Interface

In the `scripts/fetch_urls/fetch_urls_feedparser.py` file, you'll find the `FeedparserFetcher` class, which implements the `URLFetcher` interface:

```python
class FeedparserFetcher(URLFetcher):
    # ... implementation details ...
```

### Scripts (`scripts/`)

The `scripts` directory is the core of the article summarization system, housing the Python scripts that implement the primary tasks and manage their execution. Each task—`fetch_urls`, `scraper`, `summarizer`, and `tagging`—has its own subdirectory within `scripts`.

#### Task-Specific Scripts

##### `fetch_urls`

-   **`fetch_urls_feedparser.py`:** This script is responsible for fetching new article URLs from RSS feeds using the `feedparser` library. It implements the `URLFetcher` interface and interacts with the Supabase database to store newly discovered URLs.

##### `scraper`

-   **`scrape_puppeteer.py`:** This script utilizes the `pyppeteer` library, which provides a high-level API to control headless Chrome or Chromium browsers. It scrapes the content of articles from their URLs, extracting the main body text and saving it in the database.

##### `summarizer`

-   **`summarizer_groq_llama8b.py`:**  This script generates article summaries using the Llama 8B model via the Groq API. It fetches articles that haven't been summarized yet from the database, processes them, and updates the database with the generated summaries.
-   **`summarizer_claude_haiku.py`:** This script is a fallback summarizer that utilizes the Claude API for generating article summaries. It follows a similar process to `summarizer_groq_llama8b.py`, fetching unsummarized articles and updating the database with summaries.
-   **`summarizer_gemini_flash.py`:** This script generates article summaries using the Gemini Flash model via the Gemini API. It fetches articles that haven't been summarized yet from the database, processes them, and updates the database with the generated summaries.
-   **`summarizer_togetherai_llama.py`:** This script generates article summaries using the Llama 2 70B chat model via the TogetherAI API. It fetches articles that haven't been summarized yet from the database, processes them, and updates the database with the generated summaries.
-   **`summarizer_replicate_llama8b.py`:** This script generates article summaries using the Llama 8B Instruct model via the Replicate API. It fetches articles that haven't been summarized yet from the database, processes them, and updates the database with the generated summaries.

##### `tagging`

-   **`tagging_groq_llama8b.py`:**  This script is responsible for assigning tags and scores to summarized articles using the Llama 8B model through the Groq API. It fetches summarized articles that haven't been tagged yet, processes them, and updates the database with the generated tags and scores.
-   **`tagging_gemini_flash.py`:** This script is the primary script responsible for assigning tags and scores to summarized articles using the Gemini Flash model through the Gemini API. It fetches summarized articles that haven't been tagged yet, processes them, and updates the database with the generated tags and scores.
-   **`tagging_togetherai_llama.py`:** This script serves as a fallback for assigning tags and scores to summarized articles, utilizing the Llama 2 70B chat model through the TogetherAI API. It operates similarly to the primary tagging script, fetching untagged summarized articles and updating the database with generated tags and scores if the primary script fails.
-   **`tagging_replicate_llama.py`:** This script acts as another fallback for tag assignment and scoring, employing the Llama 8B Instruct model via the Replicate API. It mirrors the functionality of the previous fallback script, stepping in if the primary and previous fallback scripts encounter issues.
-   **`tagging_claude_haiku.py`:** This script is yet another fallback option for tagging articles, leveraging the Claude API (Anthropic). It operates in the same manner as the other fallback scripts, providing an additional layer of redundancy in the tagging process.


#### Core Execution Scripts

-   **`main.py`:** This script serves as the main entry point for the system. It is called by Celery with a task name as an argument, determining which task to execute (`fetch_urls`, `scrape_content`, `summarize_articles`, or `tag_articles`). If no argument is provided, it runs all tasks sequentially.

-   **`redundancy_manager.py`:**  This script manages the execution of tasks with redundancy. It ensures that each task is attempted using all available implementations (primary and fallbacks) to guarantee that the work is completed even if some scripts fail. This enhances the system's robustness by providing backups for critical operations.

### Utilities (`utils/`)

The `utils` directory contains various utility modules that provide essential functions for database interactions, logging, large language model (LLM) interactions, and task-specific operations. These modules are used across different scripts in the system to streamline common tasks and enhance code reusability.

#### `db_utils.py`

-   **Database Interaction:** This module provides functions for interacting with the Supabase database:
    -   `get_supabase_client()`: Initializes and returns a Supabase client instance, ensuring a single point of client creation.
    -   `fetch_table_data()`: Retrieves data from a specified table with optional filtering and column selection.
    -   `update_table_data()`: Updates records in a table based on a given condition.
    -   `fetch_articles_with_logic()`: Fetches articles from the `summarizer_flow` table with specific criteria (e.g., scraped but not summarized).

#### `logging_utils.py`

-   **Logging:** This module handles logging of script execution status and duration to the Supabase database:
    -   `log_status()`: Logs the status ("Success," "Partial," or "Error") of a script along with relevant log messages.
    -   `log_duration()`: Records the start and end times of a script's execution, along with the total duration.

#### `llm_utils.py`

-   **LLM Interaction:** This module provides a function for interacting with large language model APIs:
    -   `call_llm_api()`: A generic function to call different LLM APIs (Groq, Anthropic, Gemini, Replicate, TogetherAI) based on the specified model and parameters. It handles authentication and constructs API requests, returning the raw response from the LLM. It then parses the raw response, as the raw response often contains metadata or other elements, so we parse it to just the content from the large language model


#### Task-Specific Utilities

##### `scraping_utils.py`

-   **`fetch_and_process_urls(table_name, fetch_condition, scraping_function, update_fields, script_name)`:**

    1.  **Retrieving URLs:** Fetches URLs from the specified `table_name` (usually `summarizer_flow`) in the database based on a `fetch_condition` (e.g., `{'scraped': False}`).

    2.  **Logging Setup:**  Initializes logging for the scraping process, including the start time and an empty list to store log entries.

    3.  **Iterating and Scraping:**
        -   Loops through each fetched URL.
        -   Calls the provided `scraping_function` (from the relevant scraping script) to extract content from the URL.
        -   If successful, it prepares a dictionary `update_data` with the scraped content and sets the `scraped` flag to `True`.
        -   Updates the corresponding database record with `update_data`.
        -   Logs the success or failure of each scraping operation.

    4.  **Status Logging:**  Determines the overall status ("Success," "Partial," or "Error") of the scraping process based on whether any URLs failed to be scraped. Logs the final status and the total duration of the process.

-   **`run_puppeteer_scraper(scraping_function, script_name)`:**

    1.  **Wrapper for `fetch_and_process_urls`:**  Calls `fetch_and_process_urls` with specific parameters tailored for Puppeteer-based scraping:
        -   `table_name`: 'summarizer_flow'
        -   `fetch_condition`:  `{'scraped': False}`
        -   `update_fields`:  `['content']` (to store the scraped content)

    2.  **Error Handling:** Includes a `try-except` block to catch exceptions during the scraping process and log them appropriately.

##### `summarizer_utils.py`

-   **custom_escape_quotes(json_str)`:** 
    -   Ensures that quotes within JSON strings are properly escaped (e.g., replacing double quotes with `\"`) to avoid errors during JSON parsing. This is particularly important for the `BulletPointSummary` field, which is stored as JSON in the database.

-   **`extract_section(content, start_key, end_key=None)`:**
    -   Extracts a specific section of text from the `content` based on a `start_key` and an optional `end_key`. This is used to parse the LLM response and extract the `IntroParagraph`, `BulletPointSummary`, and `ConcludingParagraph` sections.

-   **`summarize_article(article_id, content, status_entries, systemPrompt, api_call_func)`:**

    1.  **LLM Call:** Calls the provided `api_call_func` (from `llm_utils.py`) to request a summary of the article `content` using the specified `systemPrompt`.
    2.  **Response Parsing:** Extracts the `IntroParagraph`, `BulletPointSummary`, and `ConcludingParagraph` sections from the LLM response.
    3.  **JSON Validation:**  Checks if `BulletPointSummary` is valid JSON. If not, it's set to `None` and an error is logged.
    4.  **Database Update:** Updates the `summarizer_flow` table with the extracted summary components and sets the `summarized` flag to `True`.

-   **`process_articles(script_name, api_call_func=None)`:**

    1.  **Configuration and Fetching:** Loads the configuration settings and fetches articles that need summarization from the database (i.e., those with `scraped` set to `True` but various summary fields null or empty).
    2.  **Summarization:** Iterates over each fetched article and calls `summarize_article` to generate and store the summary.
    3.  **Logging:** Logs the status ("Success," "Partial," or "Error") of the summarization process based on whether any articles failed to be summarized, along with the total duration of the process.

##### `tagging_utils.py`

-   **`process_tags(article_id, chat_completion, status_entries)`:**
    -   Parses the JSON response from the LLM containing tags and scores for the article with the given article_id.
    -   Inserts each tag and its score into the article_tags table.
    -   If a tag insertion fails because the tag is not in the preset list, the tag is skipped (and logged), and the process continues.
    -   If at least one tag is successfully inserted for the article, it updates the ProductionReady flag to True in the summarizer_flow table.
    -   Tracks and logs any errors during tag insertion.

-   **`construct_system_prompt()`:**
    -   Loads system prompts from `config.yaml`.
    -   Fetches enabled tags and their descriptions from the `all_tags` table.
    -   Constructs a comprehensive system prompt for the tagging LLM, incorporating the fetched tags and descriptions.

-   **`fetch_articles()`:**
    -   Fetches articles from the `summarizer_flow` table that have been summarized (`summarized` is `True`) but are not yet ready for production (`ProductionReady` is `False`).

-   **`process_articles(script_name, primary=True, api_call_func=None)`:**

    1.  **Setup:** Constructs the system prompt and fetches articles that need tagging.
    2.  **Tagging:** Iterates over each article, calling the LLM API (via `api_call_func`) to generate tags based on the article content and system prompt.
    3.  **Processing and Logging:**  Processes the tags using `process_tags`, updates the database, and logs the status and duration of the entire tagging process.


##### `url_fetch_utils.py`

-   **`fetch_existing_urls(table_name, batch_size=1000)`:**
    -   Retrieves existing URLs from the specified table in batches to avoid overloading the database.
    -   Returns a set of URLs for efficient deduplication.

-   **`deduplicate_urls(new_urls, existing_urls)`:**
    -   Compares the `new_urls` fetched from RSS feeds with the `existing_urls` already in the database.
    -   Returns a list of deduplicated URLs that are not already present in the database.

-   **`insert_new_entries(table_name, new_entries, log_entries)`:**
    -   Inserts the `new_entries` (URLs and associated data) into the specified table one by one.
    -   Logs the success or failure of each insertion.

-   **`process_feeds(table_name="summarizer_flow", parse_feed=None, script_name="script", app=None)`:**

    1.  **Feed Retrieval:** Fetches enabled RSS feeds from the `rss_feed_list` table.
    2.  **Parsing and Deduplication:** For each feed:
        -   Calls the `parse_feed` function to extract new entries.
        -   Fetches existing URLs and deduplicates the new entries.
    3.  **Insertion and Logging:** Inserts deduplicated entries into the database and logs the result for each URL.
    4.  **Status and Duration Logging:** Logs the overall status ("Success," "Partial," or "Error") of the feed processing along with the total duration.

### Task Management (`task_management/`)

#### `celery_app.py`

-   **Task Scheduling and Orchestration:** This script is the core of task management. It defines the tasks that need to be executed, their dependencies, and their schedule using Celery. It schedules periodic tasks like `fetch_urls` and manages the queue for sequential execution of `scraper`, `summarizer`, and `tagging`. It also handles error conditions and triggers subsequent tasks based on the results of previous ones.
    
    -   **Tasks:**
        -   `fetch_urls()`: Fetches new URLs every 2 minutes.
        -   `scraper()`, `summarizer()`, `tagging()`: Tasks for scraping, summarizing, and tagging, respectively, with time limits and error handling. These are never called directly and always added to the queue to stop any conflicts on the DB. They also run back to back (with a timelimit), so one only begins when the other finishes, regardless of success or failure.
        -   `process_task_queue()`: Processes the task queue and launches tasks as needed.
        -   `execute_additional_tasks()`: Chains the scraper, summarizer, and tagging tasks together for execution after new URLs are fetched.
        -   `check_execute_additional_tasks()`:  Checks if the additional tasks need to be added to the queue.
    
    -   **Task Chaining:** The script uses Celery's `chain` to link the `scraper`, `summarizer`, and `tagging` tasks, ensuring they run in sequence after new URLs are added.
    
    -   **Queue Management:** It maintains a `task_queue` to ensure sequential execution of the dependent tasks.
    
    -   **Error Handling:** The script includes mechanisms to handle errors during task execution, ensuring that the system can recover gracefully.

This comprehensive task management system ensures the smooth and efficient operation of the article summarization pipeline, providing reliability, scalability, and the ability to handle large volumes of articles.

## How to Use the System

This section will guide you through setting up the environment, running tasks, and monitoring the article summarization system.

### Setting Up the Environment

1.  **Install Dependencies:**
    -   Ensure you have Python 3 installed.
    -   Create a virtual environment and make sure to name it as follows: `python3 -m venv as-env`
    -   Activate the environment: `source as-env/bin/activate`
    -   Install the required packages: `pip install -r requirements.txt`
    -   Install system-level dependencies (Ubuntu): `sudo apt-get install rabbitmq-server`

2.  **Set Environment Variables:**
    -   Create a `.env` file in the project's root directory.
    -   Add the following environment variables, replacing the placeholders with your actual values:

    ```
    SUPABASE_URL=<your_supabase_url>
    SUPABASE_KEY=<your_supabase_api_key>
    ANTHROPIC_API_KEY=<your_anthropic_api_key>
    GROQ_API_KEY=<your_groq_api_key>
    ```

### Running Tasks

1.  **Start Celery Worker:**
    -   Open a terminal and run: `celery -A task_management.celery_app worker --loglevel=info`
    -   This will start the Celery worker, which will execute tasks in the background.

2.  **Start Celery Beat:**
    -   Open another terminal and run: `celery -A task_management.celery_app beat --loglevel=info`
    -   This will start the Celery beat scheduler, which will trigger tasks based on their defined schedule.

3.  **Manually Trigger Tasks (Optional):**
    -   If you want to run a task immediately, you can use the following command: `celery -A task_management.celery_app call <task_name>`
    -   For example, to trigger the `fetch_urls` task, run: `celery -A task_management.celery_app call task_management.celery_app.fetch_urls`

### Monitoring and Logging

-   **Task Monitoring:**
    -   Celery provides various tools for monitoring task execution, including Flower (a real-time monitor and web admin interface).
    -   You can start Flower by running: `celery -A task_management.celery_app flower`
    -   Then, access the Flower dashboard in your web browser at `http://localhost:5555`.

-   **Log Inspection:**
    -   Script execution logs are stored in the `log_script_status` table in your Supabase database.
    -   You can view these logs using the Supabase dashboard or by querying the database directly.
    -   The `log_script_duration` table stores information about the execution time of each script.

## Advanced Topics

### Redundancy Management

The Article Summarization System is designed with a robust redundancy mechanism to ensure reliable and uninterrupted operation even in the face of potential failures. This mechanism is implemented primarily through the `redundancy_manager.py` script.

#### `redundancy_manager.py`

This script acts as the central controller for managing the execution of tasks with redundancy. Here's a breakdown of its key components and functions:

##### Initialization (`__init__`)

-   Loads configuration from the YAML file specified in `config_path`.
-   Sets up a logger to record information about the execution process.

##### Configuration Loading (`load_config`)

-   Opens and parses the YAML configuration file using the `yaml` library.
-   Returns a Python dictionary representation of the configuration settings.

##### Task Execution (`execute_with_redundancy`)

-   This is the core function responsible for executing tasks with redundancy.
-   It takes the `task_name` as input and looks up the corresponding configuration in the loaded YAML file.
-   The configuration specifies a `primary` implementation and a list of `fallbacks` for the given task.
-   The script creates a list of implementations, starting with the primary and followed by the fallbacks.
-   It iterates through this list, executing each implementation sequentially.

##### Script Execution (`execute_script`)

-   This function is called within `execute_with_redundancy` for each implementation.
-   It executes the specified script as a subprocess using `subprocess.run`.
-   Captures and logs the standard output and standard error of the subprocess.
-   Returns a status indicating the success or failure of the script execution ("Success," "Partial," or "Error").

##### Redundancy Logic

-   The redundancy manager runs all implementations (primary and fallbacks) of a given task sequentially.
-   It logs the status and duration of each script execution.
-   The overall status of the task is determined based on the individual script results:
    -   If any script encounters an "Error," the overall task status is "Error."
    -   If any script returns "Partial" success, the overall task status is "Partial."
    -   If all scripts succeed, the overall task status is "Success."

##### Interaction with Celery

-   If the `send_status` flag is set to `True`, the script uses Celery to send the task status and result to a central queue.
-   For the `fetch_urls` task, if new URLs are found, it triggers the execution of dependent tasks (`scraper`, `summarizer`, `tagging`) using Celery.

##### Example Usage

```python
from redundancy_manager import RedundancyManager

manager = RedundancyManager('config/config.yaml')
total_new_urls = manager.execute_with_redundancy('fetch_urls')  # Fetch URLs with redundancy
```

#### Benefits of Redundancy
-   Reliability: Ensures that tasks are completed even if the primary implementation fails, as fallbacks are available.
-   Fault Tolerance: Provides a level of resilience against errors and unexpected situations.
-   Flexibility: Allows easy addition of new implementations or replacement of existing ones without disrupting the system.

## Advanced Topics

### Adding New RSS Feeds

The system is designed to be easily expandable to include new sources of news articles. To add a new RSS feed, follow these steps:

1.  **Database Entry:**
    -   Insert a new record into the `rss_feed_list` table in your Supabase database.
    -   The record should include:
        -   `rss_feed`: The URL of the RSS feed.
        -   `isEnabled`: Set to `True` to enable fetching from this feed.

2.  **Verification:**
    -   Manually trigger the `fetch_urls` task to ensure the new feed is being fetched correctly.
    -   Check the `summarizer_flow` table for new URLs from the added feed.

### Customizing LLM Prompts

The system prompts play a crucial role in guiding the behavior of large language models during summarization and tagging tasks. You can customize these prompts to refine the system's output.

1.  **Locate Prompts:**
    -   Open the `config.yaml` file.
    -   Find the `systemPrompt` section for summarization and the `systemPrompt-Tagger-1` and `systemPrompt-Tagger-2` sections for tagging.

2.  **Modify Prompts:**
    -   Carefully edit the instructions within these sections. You can change the desired format, tone, level of detail, and specific requirements for the LLM outputs.

3.  **Test and Iterate:**
    -   After modifying the prompts, re-run the affected tasks (`summarizer` or `tagging`) to evaluate the changes in the output.
    -   Iterate on the prompts until you achieve the desired results.

### Adding New LLM Sources

The system is designed to be flexible and adaptable to different LLM providers. To add support for a new LLM source, follow these steps:

1.  **Update `llm_utils.py`:**
    -   Open the `llm_utils.py` file in the `utils` directory.
    -   Add a new conditional branch within the `call_llm_api` function to handle the new LLM client.
    -   The branch should check for the `client_type` and initialize the corresponding client using the appropriate library and API key.
    -   Structure the request payload (messages, parameters) according to the API specifications of the new LLM.

2.  **Modify Configuration:**
    -   In the `config.yaml` file, update the `interfaces` section to include the new LLM model in the list of available summarizers or taggers.
    -   Ensure that you specify the correct model name and client type.

3.  **Create New Scripts (If Needed):**
    -   If the new LLM requires a significantly different implementation for summarization or tagging, create separate scripts (e.g., `summarizer_newllm.py`) and add them to the `interfaces` configuration.

4.  **Test Thoroughly:**
    -   Test the integration with the new LLM thoroughly to ensure that it works as expected.
    -   Pay attention to the output format, error handling, and any specific requirements of the new LLM.

## Troubleshooting

This section provides guidance on troubleshooting common issues and errors you might encounter while using the Article Summarization System.

### General Troubleshooting Tips

1.  **Check Logs:** The first step in troubleshooting is to check the logs. The system logs script execution status and duration to the `log_script_status` and `log_script_duration` tables in your Supabase database. Look for any errors or warnings that might indicate the source of the problem.

2.  **Examine Celery Status:** If tasks are not being executed or scheduled correctly, check the status of Celery worker and beat processes. You can use Celery's monitoring tools like Flower to get detailed insights into task queues and worker states.

3.  **Verify Environment Variables:** Ensure that all environment variables in your `.env` file are correctly set with valid values. Incorrect or missing API keys, database credentials, or other settings can lead to failures.

4.  **Inspect Code Changes:** If you've recently modified the codebase, carefully review your changes to identify any potential issues. Consider reverting to a previous working version if necessary.

### Common Issues

#### Fetching URLs

-   **No New URLs Found:**  If the `fetch_urls` task doesn't find any new URLs, verify that the RSS feeds in the `rss_feed_list` table are enabled and contain up-to-date content. You might need to adjust the fetching frequency or add new RSS feeds.

-   **Error Fetching Feeds:** If errors occur during the feed parsing process, check the logs for details. Common causes include invalid feed URLs, network connectivity issues, or changes in the feed structure.

#### Scraping Articles

-   **Timeout Errors:** If the scraping process times out, consider increasing the timeout limits in `celery_app.py` or optimizing the scraping implementation.
-   **Content Extraction Failures:** If the scraper fails to extract content properly, examine the website structure and adjust the scraping logic in `scrape_puppeteer.py` as needed.

#### Summarizing Articles

-   **LLM API Errors:** If there are errors from the LLM API (Groq or Claude), check your API keys and usage limits. Also, review the API documentation for error codes and troubleshooting guides.
-   **Invalid Summary Format:** Ensure that the LLM response follows the expected format. If not, refine the system prompt or adjust the parsing logic in `summarizer_utils.py`.

#### Tagging Articles

-   **Tag Generation Errors:** Similar to summarization errors, LLM API issues can cause tag generation failures. Verify API keys and usage, and consider refining the system prompt.
-   **Database Insertion Errors:** If tags are not being inserted into the database correctly, check for database connection problems, unique constraint violations, or incorrect column names in the `article_tags` table.

### Debugging Tips

-   **Enable Debug Logging:** Increase the log level to `DEBUG in Celery and other scripts to get more detailed information about the execution flow and potential issues.
-   **Use a Debugger:** If you encounter complex errors, use a Python debugger like `pdb` or an IDE's debugging tools to step through the code and identify the problem.
-   **Isolate Components:** Try isolating the problematic task by manually running it with specific inputs. This can help narrow down the source of the error.
-   **Check Dependencies:** Ensure that all required libraries and dependencies are correctly installed and up-to-date.

If you encounter any persistent issues, consider seeking assistance from the development team or community forums.

## Testing Environment

To ensure the reliability and maintainability of the Article Summarization System, a comprehensive testing environment has been set up. This environment allows developers to run tests without affecting production data.

### Setting Up the Testing Environment

1. **Environment Variables:**
   - Ensure that you have a `.env.test` file in your project root. This file should contain environment variables specific to the testing environment, including:
     ```plaintext
     APP_ENV=testing
     SUPABASE_URL=<your_test_supabase_url>
     SUPABASE_KEY=<your_test_supabase_key>
     ANTHROPIC_API_KEY=<your_test_anthropic_api_key>
     GROQ_API_KEY=<your_test_groq_api_key>
     GEMINI_API_KEY=<your_test_gemini_api_key>
     REPLICATE_API_KEY=<your_test_replicate_api_key>
     AIML_API_KEY=<your_test_aiml_api_key>
     TOGETHERAI_API_KEY=<your_test_togetherai_api_key>
     ```

2. **Configuration Files:**
   - The `test_config.yaml` file contains configurations specific to the testing environment. Ensure this file is correctly set up with test-specific table names and settings.

3. **Switching to the Test Environment:**
   - To run your application or tests in the test environment, set the `APP_ENV` variable to `testing`. This can be done in several ways:
     - **Command Line:**
       ```bash
       export APP_ENV=testing
       ```
     - **Using `.env.test`:** Ensure your test scripts or CI pipeline loads the `.env.test` file.

4. **Directory Structure:**
   - Ensure your project has a `tests` directory structured as follows:
     ```
     ── tests/
         ├── __init__.py
         ├── conftest.py
         ├── mocks/
         │   ├── __init__.py
         │   └── mock_llm.py
         └── test_summarizer_utils.py
     ```

5. **Mocking External Dependencies:**
   - The `mock_llm.py` file contains mock functions for simulating LLM API responses. These mocks are used to test the system's behavior without making real API calls.

6. **Pytest Fixtures:**
   - The `conftest.py` file defines fixtures that apply these mocks across multiple test cases, ensuring consistency and reducing redundancy.

7. **Running Tests:**
   - Use Pytest to run your tests. Ensure you are in the root directory of your project and execute the following command:
     ```bash
     pytest tests/
     ```

8. **Expected Test Behavior:**
   - Tests are designed to simulate various scenarios, including successful API responses, errors, and edge cases. Ensure that your tests are set up to expect these conditions.

9. **Troubleshooting:**
   - If you encounter import errors, ensure that all directories have an `__init__.py` file and that you are running tests from the correct directory.
   - Use the `PYTHONPATH` environment variable if necessary to ensure the correct path is set:
     ```bash
     PYTHONPATH=. pytest tests/
     ```

### Additional Notes

- **Mocks and Fixtures:** The testing suite uses mocks and fixtures to simulate external dependencies and manage test data setup and teardown.
- **Continuous Integration:** The testing suite is integrated into the CI pipeline, ensuring that tests are automatically run on commits and pull requests.

By following these steps, you can effectively use the testing environment to validate the functionality of the Article Summarization System without affecting production data.
