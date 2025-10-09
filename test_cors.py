"""
Test script to verify CORS configuration locally.
Run this script and then access http://localhost:8000/test-cors in your browser.
"""
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI()

# Configure CORS with the same settings as your main app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://doztra.ai",
        "https://doztra.netlify.app",
        "https://www.doztra.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>CORS Test</title>
            <script>
                async function testCORS() {
                    const origins = [
                        "http://localhost:3000",
                        "http://localhost:8000",
                        "https://doztra.ai",
                        "https://doztra.netlify.app",
                        "https://www.doztra.netlify.app"
                    ];
                    
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = '';
                    
                    for (const origin of origins) {
                        const resultItem = document.createElement('div');
                        resultItem.innerHTML = `Testing origin: ${origin}... `;
                        resultsDiv.appendChild(resultItem);
                        
                        try {
                            const response = await fetch('/api/test-cors', {
                                method: 'OPTIONS',
                                headers: {
                                    'Origin': origin,
                                    'Access-Control-Request-Method': 'GET',
                                    'Access-Control-Request-Headers': 'Content-Type'
                                }
                            });
                            
                            const headers = {};
                            for (const [key, value] of response.headers.entries()) {
                                headers[key] = value;
                            }
                            
                            if (headers['access-control-allow-origin'] === origin) {
                                resultItem.innerHTML += `<span style="color: green;">PASS</span>`;
                                resultItem.innerHTML += `<pre>${JSON.stringify(headers, null, 2)}</pre>`;
                            } else {
                                resultItem.innerHTML += `<span style="color: red;">FAIL</span>`;
                                resultItem.innerHTML += `<pre>${JSON.stringify(headers, null, 2)}</pre>`;
                            }
                        } catch (error) {
                            resultItem.innerHTML += `<span style="color: red;">ERROR: ${error.message}</span>`;
                        }
                    }
                }
            </script>
        </head>
        <body>
            <h1>CORS Test</h1>
            <button onclick="testCORS()">Test CORS Configuration</button>
            <div id="results"></div>
        </body>
    </html>
    """

@app.options("/api/test-cors")
async def test_cors_preflight(request: Request):
    return {}

@app.get("/api/test-cors")
async def test_cors():
    return {"message": "CORS test successful"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
