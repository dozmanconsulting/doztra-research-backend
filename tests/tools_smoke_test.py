import os
import asyncio
import logging
from typing import Dict, Any

# Optional HTTP client for simple pings
try:
    import aiohttp
except Exception:
    aiohttp = None

# Import project services
from app.services.web_scraping import web_scraping_service
from app.services.audio_transcription import audio_service
from app.services.vector_search import vector_service

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tools_smoke_test")

RESULTS: Dict[str, Any] = {}


async def test_firecrawl():
    if not os.getenv("FIRECRAWL_API_KEY"):
        RESULTS["firecrawl"] = {"status": "skipped", "reason": "FIRECRAWL_API_KEY missing"}
        return
    try:
        url = os.getenv("SMOKE_TEST_URL", "https://example.com")
        data = await web_scraping_service.scrape_url(url)
        content = data.get("markdown") or data.get("html") or ""
        RESULTS["firecrawl"] = {
            "status": "ok" if content else "empty",
            "title": data.get("metadata", {}).get("title"),
            "content_preview": (content[:160] + "...") if content else "",
        }
    except Exception as e:
        RESULTS["firecrawl"] = {"status": "error", "error": str(e)}


async def test_assemblyai():
    if not os.getenv("ASSEMBLYAI_API_KEY"):
        RESULTS["assemblyai"] = {"status": "skipped", "reason": "ASSEMBLYAI_API_KEY missing"}
        return
    # Use a tiny public audio sample
    sample_url = os.getenv(
        "SMOKE_TEST_AUDIO_URL",
        "https://storage.googleapis.com/aai-web-samples/espn-basketball.mp3",
    )
    try:
        # Override defaults to speed up
        options = {
            "speaker_labels": False,
            "auto_chapters": False,
            "sentiment_analysis": False,
            "entity_detection": False,
            "iab_categories": False,
            "content_safety": False,
            "auto_highlights": False,
            "summarization": False,
        }
        result = await audio_service.transcribe_audio(sample_url, options=options)
        text = result.get("text", "")
        RESULTS["assemblyai"] = {
            "status": "ok" if text else "empty",
            "words": len(text.split()) if text else 0,
            "transcript_id": result.get("id"),
        }
    except Exception as e:
        RESULTS["assemblyai"] = {"status": "error", "error": str(e)}


async def test_vector():
    # Requires configured vector backend (Milvus/Zilliz or Pinecone) and embeddings available
    try:
        ok = await vector_service.connect()
        if not ok:
            RESULTS["vector"] = {"status": "skipped", "reason": "Vector backend unavailable"}
            return
        # Use short sample text
        sample = "Vector smoke test: hello vectors."
        added = await vector_service.add_content(
            content_id="smoke_test_content",
            user_id=os.getenv("SMOKE_TEST_USER_ID", "test_user"),
            content_type="text",
            title="Smoke Test",
            content=sample,
            metadata={"env": "smoke"},
        )
        if not added:
            RESULTS["vector"] = {"status": "error", "error": "Failed to add content (embeddings missing? set OPENAI_API_KEY or install sentence-transformers)"}
            return
        results = await vector_service.search_similar(
            query="hello vectors",
            user_id=os.getenv("SMOKE_TEST_USER_ID", "test_user"),
            limit=3,
        )
        RESULTS["vector"] = {"status": "ok", "hits": len(results)}
        # Cleanup best-effort
        await vector_service.delete_content("smoke_test_content", os.getenv("SMOKE_TEST_USER_ID", "test_user"))
    except Exception as e:
        RESULTS["vector"] = {"status": "error", "error": str(e)}


async def test_zep():
    base = os.getenv("ZEP_API_URL")
    api_key = os.getenv("ZEP_API_KEY")
    if not base or not api_key or not aiohttp:
        RESULTS["zep"] = {"status": "skipped", "reason": "ZEP_API_URL/ZEP_API_KEY missing or aiohttp not available"}
        return
    try:
        headers = {"Authorization": f"Api-Key {api_key}", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            # Health endpoint may differ; try /health then /api/v1/health
            for path in ("/health", "/api/v1/health"):
                try:
                    async with session.get(base.rstrip("/") + path, headers=headers, timeout=10) as resp:
                        if resp.status < 500:
                            RESULTS["zep"] = {"status": "ok", "http": resp.status, "path": path}
                            return
                except Exception:
                    continue
        RESULTS["zep"] = {"status": "error", "error": "No reachable health endpoint"}
    except Exception as e:
        RESULTS["zep"] = {"status": "error", "error": str(e)}


async def test_kokoro():
    # Placeholder: integrate kokoro 82M TTS test once service is added
    RESULTS["kokoro"] = {"status": "skipped", "reason": "Kokoro TTS service not integrated yet in this repo"}


async def main():
    await asyncio.gather(
        test_firecrawl(),
        test_assemblyai(),
        test_vector(),
        test_zep(),
        test_kokoro(),
    )
    # Pretty print results
    log.info("\n=== Tools Smoke Test Results ===")
    for k, v in RESULTS.items():
        log.info("%s: %s", k, v)
    # Summarize exit code
    failed = [k for k, v in RESULTS.items() if v.get("status") == "error"]
    if failed:
        log.error("Failures: %s", ", ".join(failed))
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
