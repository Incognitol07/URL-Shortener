# URL Shortener Web Application

This project is a feature-rich URL Shortener API and web application, allowing users to generate short URLs with added functionalities like password protection, expiration dates, and click tracking analytics.

---

## Features

- **URL Shortening:** Create shortened versions of long URLs for easy sharing.
- **Password Protection:** Add optional password protection to secure your URLs.
- **Expiration Dates:** Set expiration dates for URLs to ensure limited accessibility.
- **Click Tracking:** View the number of times each shortened URL is accessed.
- **Domain Validation:** Automatically checks the validity of target URLs before redirection.
- **Background Tasks:** Perform operations (e.g., click tracking) asynchronously for optimized performance.

---

## Installation

Follow these steps to set up the project locally:

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/url-shortener.git
   cd url-shortener
   ```

2. **Set Up the Virtual Environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate    # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the Environment:**
   - Create a `.env` file in the root directory.

        ```cmd
        copy .env.example .env
        ```

5. **Start the Application:**

   ```bash
   uvicorn main:app --reload
   ```

6. **Access the App:**
   - API documentation is available at `http://127.0.0.1:8000/docs`.
   - Visit the web interface at `http://127.0.0.1:8000`.
