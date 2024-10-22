Implement Mocks and Fixtures to Control Test Conditions

[ ] - **Mock External LLM API Calls:**
- - Use `unittest.mock` or `responses` library to mock LLM API calls (Groq, Anthropic, Gemini, etc.).
- - Simulate various API responses, including normal responses and errors.
[ ] - **Mock Supabase Interactions:**
- - Configure tests to use the testing tables.
- - Use mocking or a test database instance to prevent interaction with production data.
[ ] - **Configure Celery for Testing:**
- - Set Celery to run tasks synchronously in testing mode.
- - Use an in-memory broker like `memory` for fast execution.
[ ] - **Implement Fixtures:**
- - Use Pytest fixtures or Behave’s `before_scenario` and `after_scenario` hooks.
- - Set up initial state before tests and clean up after tests.
[ ] - **Control Test Conditions:**
- - Ensure tests can simulate different scenarios by controlling external dependencies.
#### **Acceptance Criteria:**
- - All external dependencies (LLM APIs, Supabase, Celery) are mocked in the test environment.
- - Fixtures are in place to set up and tear down test data for each test.
- - Tests run in isolation without affecting external systems or production data.
- - Tests can simulate different responses and errors from LLM APIs.
- - Documentation is provided on how mocks and fixtures are implemented and how to extend them.