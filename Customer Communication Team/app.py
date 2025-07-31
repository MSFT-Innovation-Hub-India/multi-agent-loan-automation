import logging
import os
from pathlib import Path

from aiohttp import web
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential, DefaultAzureCredential
from dotenv import load_dotenv

from rtmt import RTMiddleTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicerag")

async def create_app():
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        logger.info("Running in development mode, loading from .env file")
        load_dotenv()

    llm_key = os.environ.get("AZURE_OPENAI_API_KEY")

    credential = None
    if not llm_key:
        if tenant_id := os.environ.get("AZURE_TENANT_ID"):
            logger.info("Using AzureDeveloperCliCredential with tenant_id %s", tenant_id)
            credential = AzureDeveloperCliCredential(tenant_id=tenant_id, process_timeout=60)
        else:
            logger.info("Using DefaultAzureCredential")
            credential = DefaultAzureCredential()
    llm_credential = AzureKeyCredential(llm_key) if llm_key else credential
    
    app = web.Application()

    rtmt = RTMiddleTier(
        credentials=llm_credential,
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment=os.environ["AZURE_OPENAI_REALTIME_DEPLOYMENT"],
        voice_choice=os.environ.get("AZURE_OPENAI_REALTIME_VOICE_CHOICE") or "alloy"
        )
    rtmt.system_message = "You are a friendly sales representative from Global Trust Bank, one of India's leading financial institutions. " + \
                          "When a customer connects, immediately greet them warmly and congratulate them on their recently approved loan from Global Trust Bank. " + \
                          "After the congratulations, inform them that based on their excellent credit profile and banking history with us, " + \
                          "you can offer them an additional loan product at a special interest rate starting from 8.5% per annum. " + \
                          "Ask if they would be interested in learning more about this exclusive offer. " + \
                          "If they show interest, provide details about loan amounts (₹2 lakh to ₹50 lakh), flexible tenure (1-7 years), " + \
                          "minimal documentation, and quick processing within 24-48 hours. " + \
                          "Since customers are listening via audio, keep responses brief and conversational - ideally 1-2 sentences at a time. " + \
                          "Be enthusiastic but professional, and always emphasize the benefits of being a valued Global Trust Bank customer. " + \
                          "Use Indian Rupees (₹) for all amounts and mention that rates are subject to credit assessment."

    rtmt.attach_to_app(app, "/realtime")

    current_directory = Path(__file__).parent
    app.add_routes([web.get('/', lambda _: web.FileResponse(current_directory / 'static/index.html'))])
    app.router.add_static('/', path=current_directory / 'static', name='static')
    
    return app

if __name__ == "__main__":
    host = "localhost"
    port = 8765
    web.run_app(create_app(), host=host, port=port)
