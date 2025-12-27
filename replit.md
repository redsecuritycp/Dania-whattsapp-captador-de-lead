# DANIA/Fortia WhatsApp Bot

## Overview

DANIA/Fortia is a WhatsApp-based AI chatbot for intelligent lead capture and qualification. The bot receives WhatsApp messages via webhooks, automatically extracts business data from websites, researches contacts on LinkedIn, qualifies leads, stores them in MongoDB, and sends email notifications. It uses Argentine Spanish (voseo) for professional communication and integrates with Cal.com for meeting scheduling.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Framework
- **FastAPI** serves as the web framework handling WhatsApp webhooks and Cal.com integration
- **Uvicorn** runs the ASGI server on port 8000
- **APScheduler** manages background jobs for automated meeting reminders

### AI & Processing Pipeline
- **OpenAI GPT-4o** powers the conversational agent with function calling (tools)
- The agent follows a strict multi-step flow: extract web data → search LinkedIn → research challenges → save lead → send notification
- Tools are defined in `tools/definitions.py` with a comprehensive system prompt guiding the agent behavior

### Web Data Extraction (Priority Order)
1. **Firecrawl** - Primary extractor with full JavaScript rendering
2. **Jina AI** - Backup for content extraction
3. **Tavily** - Search and verification fallback
4. **Regex patterns** - Extract emails, phones, WhatsApp numbers, social links
5. **GPT-4o** - Final parsing and structuring of extracted data

### External Research Services
- **Tavily API** - LinkedIn searches, news research, web verification
- **Google Custom Search** - Fallback for LinkedIn and news
- **Apify** - News crawler (Google News + Bing News)

### Data Storage
- **MongoDB Atlas** - Stores leads, chat history, and booking information
- Database name configurable via `MONGODB_DB_NAME` environment variable
- Collections handle lead data with full contact info, company details, and qualification tiers

### Communication Services
- **WhatsApp Business API** - Receives/sends messages, handles audio transcription
- **Gmail SMTP** - Sends rich HTML lead notification emails
- **OpenAI TTS** - Converts text responses to audio when user sends voice messages

### Code Organization
```
main.py              - FastAPI app, webhook handlers, scheduler lifecycle
config.py            - Centralized environment variable management
services/            - Business logic modules (one per external service)
tools/               - OpenAI function definitions and system prompt
utils/               - Text cleaning, URL normalization helpers
```

### Key Design Patterns
- **Async throughout** - All HTTP calls use `httpx` async client
- **Graceful fallbacks** - Each service has backup methods if primary fails
- **Message deduplication** - OrderedDict cache prevents duplicate processing
- **Long message splitting** - WhatsApp messages split at 4000 char limit

## External Dependencies

### Required API Keys (Environment Variables)
| Variable | Service |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI GPT-4o and TTS |
| `MONGODB_URI` | MongoDB Atlas connection |
| `WHATSAPP_TOKEN` | WhatsApp Business API |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp sender ID |
| `WHATSAPP_VERIFY_TOKEN` | Webhook verification |
| `TAVILY_API_KEY` | Web search and research |
| `JINA_API_KEY` | Web content extraction |
| `FIRECRAWL_API_KEY` | JavaScript-rendered scraping |
| `GMAIL_USER` | Email sender address |
| `GMAIL_APP_PASSWORD` | Gmail app-specific password |
| `APIFY_API_TOKEN` | News crawler |
| `GOOGLE_API_KEY` | Google Custom Search |
| `GOOGLE_SEARCH_CX` | Google Search engine ID |

### Third-Party Integrations
- **Cal.com** - Meeting scheduling with webhook callbacks for confirmations/cancellations
- **WhatsApp Cloud API** - Meta's business messaging platform
- **MongoDB Atlas** - Cloud database hosting