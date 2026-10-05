================================================================================
PAYJOY - CURRENCY CONVERTER
Technical Assessment for Automation Engineer - Tools Specialist (L2)
================================================================================
--------------------------------------------------------------------------------
OVERVIEW
--------------------------------------------------------------------------------

This project automates a common customer interaction:

    "I bought my phone for $200 USD. How much is my monthly installment in
    my local currency?"

The solution converts a customer's USD installment amount into a selected
local currency through a REST API integrated with a Landbot chatbot.

SCOPE CLARIFICATION

The requirement was clarified before implementation:

    - The USD amount entered by the customer is treated directly as the
      installment amount.
    - The API performs currency conversion only.
    - The API does not calculate financing terms, interest, loan duration,
      or monthly payments.
    - Currency codes are validated strictly against ISO 4217.
    - For example, the Philippine peso uses PHP, not PHL.
--------------------------------------------------------------------------------
AUTHOR
--------------------------------------------------------------------------------

    Camilo Melo

    Colombia

    GitHub:
    https://github.com/expcamilo-cpu
--------------------------------------------------------------------------------
LIVE DEMO
--------------------------------------------------------------------------------

REPOSITORY

    https://github.com/expcamilo-cpu/payjoy-currency-converter

LANDBOT

    https://landbot.online/v3/H-3523713-BM0FM3HS6VKO0OEV/index.html

API

    Base URL:
    https://payjoy-currency-converter-dsmj.onrender.com

    Swagger UI:
    https://payjoy-currency-converter-dsmj.onrender.com/docs

    Example conversion endpoint:
    https://payjoy-currency-converter-dsmj.onrender.com/convert?amount=200&currency=BRL

    Health check:
    https://payjoy-currency-converter-dsmj.onrender.com/health


--------------------------------------------------------------------------------
EXTERNAL SERVICES
--------------------------------------------------------------------------------

    ExchangeRate-API:  https://www.exchangerate-api.com
    FastForex:         https://fastforex.io
    Landbot:           https://landbot.io
    Render:            https://render.com

--------------------------------------------------------------------------------
ARCHITECTURE
--------------------------------------------------------------------------------

The solution has three main components:

    Customer
       |
       v
    Landbot
       |
       | HTTPS webhook
       v
    FastAPI REST API
       |
       +--> ExchangeRate-API (primary)
       |
       +--> FastForex (fallback)
       |
       v
    JSON response
       |
       v
    Landbot
       |
       v
    Customer

COMPONENTS

    1. REST API
       - Python 3.11
       - FastAPI
       - Pydantic validation
       - ISO 4217 currency validation
       - ExchangeRate-API as the primary provider
       - FastForex as a fallback provider

    2. Chatbot
       - Landbot
       - Numeric installment input
       - ISO currency selection
       - Webhook integration with the REST API
       - Success and error handling

    3. Deployment
       - Render
       - Public HTTPS endpoint
       - Environment variables for API credentials


--------------------------------------------------------------------------------
LOCAL SETUP
--------------------------------------------------------------------------------

REQUIREMENTS

    - Python 3.11+
    - Git
    - pip
    - ExchangeRate-API key
    - FastForex API key

Both providers offer free tiers.

STEP 1 - CLONE THE REPOSITORY

    git clone https://github.com/expcamilo-cpu/payjoy-currency-converter.git
    cd payjoy-currency-converter

STEP 2 - CREATE A VIRTUAL ENVIRONMENT

    On macOS or Linux:

        python3.11 -m venv .venv
        source .venv/bin/activate

    On Windows:

        python3.11 -m venv .venv
        .venv\Scripts\activate

STEP 3 - INSTALL DEPENDENCIES

    pip install -r requirements.txt

STEP 4 - CONFIGURE ENVIRONMENT VARIABLES

    Create a file named ".env" in the project root with the following
    content:

        EXCHANGE_RATE_API_KEY="your_exchangerate_api_key"
        FASTFOREX_API_KEY="your_fastforex_api_key"

    Never commit ".env" to Git.

    A ".env.example" file is included as a template.

STEP 5 - RUN THE API

    uvicorn app.main:app --reload

    The API will be available at:

        http://127.0.0.1:8000

    Swagger UI:

        http://127.0.0.1:8000/docs

--------------------------------------------------------------------------------
API REFERENCE
--------------------------------------------------------------------------------

GET /convert

    Converts a USD installment amount into the requested currency.

    Parameters:

        amount    float, required
                  USD amount, greater than 0

        currency  string, required
                  ISO 4217 target currency code

    Example:

        curl "http://127.0.0.1:8000/convert?amount=200&currency=BRL"

    Example response:

        {
          "amount_usd": 200.0,
          "currency": "BRL",
          "converted": 1045.62,
          "rate": 5.2281,
          "provider": "exchangerate-api",
          "fallback_used": false
        }

    Response fields:

        amount_usd     Original USD amount.
        currency       Target ISO 4217 currency code.
        converted      Converted amount in the target currency.
        rate           Exchange rate used.
        provider       Provider that served the request.
        fallback_used  Indicates whether the fallback provider was used.

GET /health

    Returns the API health status.

    Example:

        curl "http://127.0.0.1:8000/health"

    Example response:

        {
          "status": "ok",
          "fallback_configured": true
        }

--------------------------------------------------------------------------------
ERROR HANDLING
--------------------------------------------------------------------------------

The API uses HTTP status codes to distinguish validation errors from external
service failures.

400 - INVALID CURRENCY

    Returned when the currency code is not a valid ISO 4217 code.

    Example:

        curl "http://127.0.0.1:8000/convert?amount=200&currency=PHL"

    Response:

        {
          "detail": "Invalid currency code: 'PHL'. Please use a valid ISO 4217 code."
        }

422 - INVALID OR MISSING PARAMETERS

    Examples include:

        - Missing currency
        - Missing amount
        - Negative amount
        - Zero amount
        - Valid ISO currency not supported by the enabled providers

502 - EXTERNAL PROVIDERS UNAVAILABLE

    Returned when both exchange-rate providers fail.

    The customer receives a generic error message while internal logs retain
    the provider and exception information.

    Sensitive provider URLs containing API credentials are never logged.

--------------------------------------------------------------------------------
PROVIDER FAILOVER
--------------------------------------------------------------------------------

ExchangeRate-API is the required primary provider.

FastForex is used as an automatic fallback when the primary provider fails
because of conditions such as:

    - Timeout
    - Network failure
    - HTTP 5xx error
    - Provider/account failure

The response identifies which provider served the request.

    ExchangeRate-API
           |
           X
           |
           v
    FastForex
           |
           v
    Customer response

This keeps the chatbot independent from the specific external exchange-rate
provider.

--------------------------------------------------------------------------------
CHATBOT FLOW
--------------------------------------------------------------------------------

The Landbot flow contains six main steps:

    1. Greeting + installment amount
                |
                v
    2. Currency selection
                |
                v
    3. Conversion confirmation
                |
                v
    4. Webhook to FastAPI
                |
           +----+----+
           |         |
          200       4xx/5xx
           |         |
           v         v
    5. Success    Error message
           |
           v
    6. Closing

STEP 1 - AMOUNT

    The chatbot asks for the installment amount in USD.

    The input is numeric to keep the API contract deterministic.

STEP 2 - CURRENCY

    The customer selects the target currency from predefined options.

    The current flow includes:

        - Brazil        - BRL
        - Mexico        - MXN
        - South Africa  - ZAR
        - Colombia      - COP
        - Philippines   - PHP
        - Nigeria       - NGN

    Using predefined buttons avoids ambiguous currency input and guarantees
    that the API receives a valid ISO code.

STEP 3 - CONFIRMATION

    The chatbot displays a short message such as:

        Converting $200 USD to BRL...

    This also provides immediate feedback while the API request is being
    processed.

STEP 4 - WEBHOOK

    Landbot calls:

        GET https://payjoy-currency-converter-dsmj.onrender.com/convert

    with:

        amount    = customer amount
        currency  = selected ISO code

STEP 5 - RESULT

    Successful response:

        Done! Your monthly installment of $200 USD is equivalent to
        1045.62 BRL.

    If the API returns an error:

        Sorry, we couldn't convert that currency right now.
        Please try again or contact support.

--------------------------------------------------------------------------------
PROJECT STRUCTURE
--------------------------------------------------------------------------------

    payjoy-currency-converter/
    |
    +-- app/
    |   +-- __init__.py
    |   +-- main.py
    |   +-- config.py
    |   +-- schemas.py
    |   +-- exceptions.py
    |   |
    |   +-- providers/
    |       +-- __init__.py
    |       +-- exchangerate.py
    |       +-- fastforex.py
    |
    +-- tests/
    |   +-- __init__.py
    |   +-- conftest.py
    |   +-- test_convert.py
    |
    +-- .env.example
    +-- .gitignore
    +-- requirements.txt
    +-- runtime.txt
    +-- README.md
    +-- PLAYBOOK.md

SEPARATION OF CONCERNS

    main.py        API routes and HTTP layer.
    config.py      Application configuration.
    schemas.py     Request/response models.
    exceptions.py  Domain-specific exceptions.
    providers/     External exchange-rate integrations.
    tests/         Automated tests.

--------------------------------------------------------------------------------
TESTING
--------------------------------------------------------------------------------

The test suite uses "pytest" and mocked external providers.

External APIs are not called during the standard test suite. This keeps tests:

    - Fast
    - Deterministic
    - Independent of provider availability
    - Independent of API quotas

Run:

    pytest tests/ -v

The current test suite covers:

    - Successful conversion through the primary provider
    - Invalid ISO 4217 currency codes
    - The PHL typo scenario
    - Missing parameters
    - Negative amounts
    - Provider failover
    - Both providers failing
    - Valid ISO currencies unsupported by the providers
    - /health endpoint

--------------------------------------------------------------------------------
TECHNICAL DECISIONS
--------------------------------------------------------------------------------

PYTHON + FASTAPI

    FastAPI was selected because it provides:

        - Request validation through Pydantic
        - Automatic OpenAPI/Swagger documentation
        - A lightweight structure for REST integrations
        - Good support for building API services quickly

STRICT ISO 4217 VALIDATION

    Currency codes are validated before reaching an external provider.

    For example:

        PHP  -> valid
        PHL  -> invalid

    This prevents malformed currency codes from reaching the provider layer.

PROVIDER ABSTRACTION AND FAILOVER

    The application keeps the external provider behind the API layer.

    This allows the chatbot to remain independent of:

        - Provider authentication
        - Provider response format
        - Provider availability
        - Future provider changes

DECIMAL FOR MONETARY VALUES

    "Decimal" is used for monetary calculations and explicit rounding
    instead of relying on binary floating-point arithmetic.

ENVIRONMENT-BASED SECRETS

    API keys are never hardcoded.

    Local development uses ".env".

    Production uses Render environment variables.

SCOPE DISCIPLINE

    The assignment focuses on currency conversion, so the implementation
    intentionally does not include:

        - Financing calculations
        - Interest calculations
        - Loan terms
        - LLM-based calculation
        - Database persistence
        - Distributed caching

    These would add complexity without being necessary for the requested
    scope.

--------------------------------------------------------------------------------
WHAT I WOULD IMPROVE WITH MORE TIME
--------------------------------------------------------------------------------

The current implementation is intentionally small. For a production
deployment, I would prioritize:

1. EXCHANGE-RATE CACHING

    Cache the exchange-rate table with a defined TTL to reduce external API
    calls and latency.

    For a multi-instance deployment, a shared cache such as Redis could be
    used.

2. CIRCUIT BREAKER

    If a provider consistently fails, temporarily stop calling it and route
    requests directly to the fallback provider.

3. OBSERVABILITY

    Add structured logs, dashboards and alerts for:

        - Request volume
        - Error rate
        - Latency
        - Provider failures
        - Fallback usage
        - Bot completion rate

4. SECURITY AND OPERATIONAL HARDENING

    Add:

        - API authentication
        - Rate limiting
        - CI/CD
        - Automated security checks
        - Secret rotation procedures

--------------------------------------------------------------------------------
PRODUCTION SUCCESS METRICS
--------------------------------------------------------------------------------

The technical solution should ultimately be measured by customer and business
outcomes.

1. BOT HANDLE RATE (BHR)

    Percentage of eligible conversion requests resolved by the bot without
    human-agent intervention.

    The initial target would be established after measuring the production
    baseline.

2. CONVERSION COMPLETION RATE

    Percentage of customers who start the conversion flow and successfully
    receive a conversion result.

        Completed conversions
        ---------------------
        Conversion attempts

3. API ERROR RATE

    Percentage of API requests returning 4xx or 5xx responses.

    Initial target:

        < 1%

4. FALLBACK USAGE RATE

    Percentage of requests served by the fallback provider.

    A sustained rate above approximately 5% would indicate degradation of
    the primary provider and should trigger investigation.

5. LATENCY

    Measure end-to-end API response time.

    Initial target:

        < 500 ms

    under normal operating conditions.

6. CUSTOMER SATISFACTION

    Measure CSAT/BSAT at the end of the chatbot interaction.

7. COST PER CONTACT

    Compare the operational cost of automated interactions against the
    previous manual-agent process.

--------------------------------------------------------------------------------
DEPLOYMENT
--------------------------------------------------------------------------------

The API is deployed on Render using HTTPS.

Production start command:

    uvicorn app.main:app --host 0.0.0.0 --port $PORT

Environment variables configured in production:

    EXCHANGE_RATE_API_KEY
    FASTFOREX_API_KEY

The Render free tier may put the service to sleep after inactivity. The
first request after inactivity can therefore experience a cold-start delay.

For a live demonstration, the "/health" endpoint can be called beforehand
to wake the service.

--------------------------------------------------------------------------------
SECURITY NOTE
--------------------------------------------------------------------------------

During development, an early commit briefly contained development API
credentials.

The credentials were:

    1. Rotated immediately.
    2. Replaced in the production environment.
    3. Removed from Git history.
    4. The cleaned history was force-pushed.
    5. The repository was searched to verify that the old credentials were
       no longer present.
    6. The API and chatbot were redeployed and verified.

Current API credentials are stored only through environment variables and
are not committed to the repository.

--------------------------------------------------------------------------------
AI TOOLS DISCLOSURE
--------------------------------------------------------------------------------

I used ChatGPT (OpenAI) as a technical assistant during development.

AI assistance was used for:

    - Initial project structure brainstorming
    - Documentation and README drafting
    - Discussing implementation alternatives
    - Reviewing error-handling approaches
    - Evaluating architectural trade-offs

The implementation was reviewed and tested manually. I understand the code,
API contract, provider integrations, tests, deployment configuration and
architectural decisions and can explain them during the technical
walkthrough.

The deployment, Landbot configuration, provider integrations, testing and
security remediation were verified directly.


================================================================================
END OF README
================================================================================