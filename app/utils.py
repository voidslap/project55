import anthropic
import os
from flask import current_app
from pytrends.request import TrendReq
import pandas as pd
from gnews import GNews
import datetime
from newspaper import Article
from datetime import datetime
import time
from .prompts import generate_chat_prompt
import re


def fetch_news_summary(keyword):
    """
    Hämta aktuella nyhetsartiklar för ett givet sökord med GNews API.
    För varje artikel, använd RSS 'description' fältet som innehållsutdrag.
    Returnerar en lista med dictionary som innehåller titel, publiceringsdatum, URL och innehåll.
    """
    try:
        google_news = GNews(
            language='en',
            country='US',
            period='1d',
            max_results=6,
            exclude_websites=['youtube.com']
        )
        news_items = google_news.get_news(keyword)
        if not news_items:
            return []
        
        summaries = []
        for article in news_items:
            try:
                title = article.get('title', 'No title') # Hämta titel, annars 'No title'
                published_date = article.get('published date', 'No date') # Hämta publiceringsdatum, annars 'No date'
                url = article.get('url', '') # Hämta URL, annars tom sträng
                # Använder 'description' fältet som innehållsutdrag
                snippet = article.get('description', '').strip()
                
                # Lägg till artikel i listan
                summaries.append({
                    'title': title,
                    'published_date': published_date,
                    'url': url,
                    'content': snippet
                })
            except Exception as e:
                current_app.logger.warning(f"Error processing article: {e}")
                continue
        
        return summaries
    except Exception as e:
        current_app.logger.error(f"Error fetching news for keyword {keyword}: {e}")
        return []

def get_hot_trends():
    """Fetch current hot trends globally"""
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Hämta aktuella trender i USA
        df = pytrends.trending_searches(pn='united_states')
        
        # Konverterar DataFrame till en lista med trender
        trends = df.values.tolist()
        
        # Tar bara de 16 första trenderna och konverterar till strängar
        trends = [str(trend[0]) for trend in trends[:16]]
        
        # Logging
        current_app.logger.debug(f"Retrieved trends: {trends}")
        
        # Returnera trender, annars standardtrender
        return trends if trends else ["AI", "Technology", "Climate Change", "Innovation", "Health"]
        
    except Exception as e:
        current_app.logger.error(f"Error in get_hot_trends: {str(e)}")
        return ["AI", "Technology", "Climate Change", "Innovation", "Health"]



# Analysera nyhetsinnehåll för att extrahera nyckelinformation och trender
def analyze_news_content(news_articles):
    """Analyze news articles to extract key information and trends"""
    try:
        # Find most recent events/updates
        recent_news = sorted(
            news_articles, 
            key=lambda x: x.get('published_date', ''), 
            reverse=True
        )[:2]
        
        # Analyze what's trending
        trending_summary = ""
        if recent_news:
            latest = recent_news[0]
            if "wins" in latest['title'].lower() or "named" in latest['title'].lower():
                trending_summary = "Recently won/named to "
            elif "super bowl" in latest['title'].lower():
                trending_summary = "Currently in Super Bowl news regarding "
            
            # Extract the main topic from the most recent article
            main_topic = latest['title'].split(':')[1].strip() if ':' in latest['title'] else latest['title']
            trending_summary += main_topic
        
        return trending_summary
    except Exception as e:
        current_app.logger.error(f"Error analyzing news content: {str(e)}")
        return "Error analyzing news content"

# Hämta nyhetsartiklar för ett givet sökord och generera en sammanfattning
def fetch_trend_summary(keywords, timeframe='now 1-d', geo='US'):
    """Enhanced trend analysis with detailed summaries"""
    try:
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
        pytrends.cookies.update({
            'CONSENT': 'YES+cb.20210328-17-p0.en+FX+{}'.format(hash(str(datetime.now())))
        })
        summaries = []

        # Sanitize keywords before use
        sanitized_keywords = [sanitize_keyword(k) for k in keywords]

        for keyword in sanitized_keywords:
            try:
                # Build payload with proper parameters
                kw_list = [keyword]
                pytrends.build_payload(
                    kw_list=kw_list,
                    cat=0,
                    timeframe=timeframe,
                    geo=geo,
                    gprop=''
                )

                # Delay för att undvika rate limits
                time.sleep(0.3)

                # Get interest over time with error handling
                try:
                    interest_over_time_df = pytrends.interest_over_time()
                except Exception as e:
                    current_app.logger.error(f"Error getting interest over time: {str(e)}")
                    interest_over_time_df = pd.DataFrame()

                # Add delay between requests
                time.sleep(0.3)

                # Get related topics with error handling
                try:
                    related_topics = pytrends.related_topics()
                except Exception as e:
                    current_app.logger.error(f"Error getting related topics: {str(e)}")
                    related_topics = {}

                time.sleep(0.3)

                # Get related queries with error handling
                try:
                    related_queries = pytrends.related_queries()
                except Exception as e:
                    current_app.logger.error(f"Error getting related queries: {str(e)}")
                    related_queries = {}

                time.sleep(0.3)

                # Get geographical data with error handling
                try:
                    interest_by_region = pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True)
                except Exception as e:
                    current_app.logger.error(f"Error getting interest by region: {str(e)}")
                    interest_by_region = pd.DataFrame()

                # Initialize summary dictionary
                summary = {
                    "title": keyword,
                    "trend_summary": f"Analysis for {keyword}",
                    "interest_data": {
                        "average": 0,
                        "peak": 0,
                        "current": 0,
                        "peak_date": "N/A"
                    },
                    "related_topics": [],
                    "related_queries": [],
                    "geographic_data": [],
                    "news_articles": []
                }

                # Process interest over time if available
                if not interest_over_time_df.empty and keyword in interest_over_time_df.columns:
                    series = interest_over_time_df[keyword]
                    summary["interest_data"].update({
                        "average": float(series.mean()),
                        "peak": int(series.max()),
                        "current": int(series.iloc[-1]),
                        "peak_date": series.idxmax().strftime('%Y-%m-%d')
                    })

                # Process related topics if available
                if keyword in related_topics and related_topics[keyword]:
                    for topic_type in ['rising', 'top']:
                        topic_data = related_topics[keyword].get(topic_type)
                        if topic_data is not None and not topic_data.empty:
                            for _, row in topic_data.head(5).iterrows():
                                summary["related_topics"].append({
                                    "topic": row.get("topic_title", "Unknown"),
                                    "type": topic_type,
                                    "value": row.get("value", 0)
                                })

                # Process related queries if available
                if keyword in related_queries and related_queries[keyword]:
                    for query_type in ['rising', 'top']:
                        query_data = related_queries[keyword].get(query_type)
                        if query_data is not None and not query_data.empty:
                            for _, row in query_data.head(5).iterrows():
                                summary["related_queries"].append({
                                    "query": row.get("query", "Unknown"),
                                    "type": query_type,
                                    "value": row.get("value", 0)
                                })

                # Process geographic data if available
                if not interest_by_region.empty and keyword in interest_by_region.columns:
                    top_regions = interest_by_region[keyword].nlargest(5)
                    summary["geographic_data"] = [
                        {"region": region, "value": int(value)}
                        for region, value in top_regions.items()
                    ]

                # Get news articles
                news = fetch_news_summary(keyword)
                summary["news_articles"] = news

                # Generate a more focused trend summary
                current_trend = ""
                
                if news:
                    news_analysis = analyze_news_content(news)
                    if news_analysis:
                        current_trend += news_analysis
                
                if summary["interest_data"]["average"] > 0:
                    peak_date = summary["interest_data"]["peak_date"]
                    if peak_date == datetime.now().strftime('%Y-%m-%d'):
                        current_trend += f". Reaching peak interest today"
                    else:
                        current_trend += f". Had peak interest on {peak_date}"
                
                if summary["geographic_data"]:
                    top_region = summary["geographic_data"][0]["region"]
                    current_trend += f", with strongest interest from {top_region}"
                
                summary["trend_summary"] = current_trend + "."
                
                # Add quick stats
                if summary["related_queries"]:
                    top_queries = [q["query"] for q in summary["related_queries"] if q["type"] == "top"][:3]
                    if top_queries:
                        summary["trend_summary"] += f" People are also searching for: {', '.join(top_queries)}."

                summaries.append(summary)
                current_app.logger.debug(f"Generated summary for {keyword}: {summary}")

            except Exception as e:
                current_app.logger.error(f"Error analyzing trend for {keyword}: {str(e)}")
                # Add this news-focused fallback summary when trend analysis fails
                summary = {
                    "title": keyword,
                    "trend_summary": "Currently in the news for: ",
                    "interest_data": {"average": 0, "peak": 0, "current": 0, "peak_date": "N/A"},
                    "related_topics": [],
                    "related_queries": [],
                    "geographic_data": [],
                    "news_articles": fetch_news_summary(keyword)
                }
                if summary["news_articles"]:
                    news_analysis = analyze_news_content(summary["news_articles"])
                    summary["trend_summary"] += news_analysis if news_analysis else "Recent developments"
                summaries.append(summary)
                continue

        return summaries if summaries else None

    except Exception as e:
        current_app.logger.error(f"Error in fetch_trend_summary: {str(e)}")
        return [{
            "title": keyword,
            "trend_summary": "Unable to fetch trend data at this time",
            "interest_data": {"average": 0, "peak": 0, "current": 0, "peak_date": "N/A"},
            "related_topics": [],
            "related_queries": [],
            "geographic_data": [],
            "news_articles": []
        } for keyword in keywords]



# Skicka meddelande till Anthropic API med kontext
def send_message_to_anthropic(message, model_name, user=None, chat=None):
    """Send message to Anthropic API with context"""
    api_key = current_app.config['ANTHROPIC_API_KEY']
    if not api_key:
        current_app.logger.error("Anthropic API key not found")
        return "I apologize, but I'm not configured properly. Please contact support."
        
    client = anthropic.Anthropic(api_key=api_key)
    
    try:
        # For news content summaries, use the message directly
        if isinstance(message, str) and message.startswith("You are a professional news summarizer"):
            prompt = message
        else:
            # For chat messages, use context-aware prompt
            chat_config = chat.get_config() if chat else {}
            company = user.company if user else None
            prompt = generate_chat_prompt(company, chat_config, message)
        
        # Add logging of the prompt being sent
        current_app.logger.info(f"Sending prompt to Anthropic API:\n{prompt}")
        current_app.logger.info(f"Using model: {model_name}")
        
        response = client.messages.create(
            model=model_name,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        if hasattr(response, 'content') and response.content:
            # Log the response
            current_app.logger.info(f"Received response from Anthropic API:\n{response.content[0].text[:200]}...")
            return response.content[0].text
        else:
            current_app.logger.error("Unexpected API response format")
            return "I received an unexpected response. Please try again."
            
    except Exception as e:
        current_app.logger.error(f"Error calling Anthropic API: {str(e)}")
        return f"An error occurred: {str(e)}"


# Hämta en sammanfattning av alla nyhetsartiklar från Anthropic API
def get_combined_news_summary(news_articles):
    """Get a combined summary of all news articles using Anthropic API"""
    try:
        # Extract full text from all articles
        all_articles_text = []
        for article in news_articles:
            try:
                news_article = Article(article['url'])
                news_article.download()
                news_article.parse()
                all_articles_text.append(f"Article: {article['title']}\n{news_article.text}\n\n")
            except Exception as e:
                current_app.logger.warning(f"Error extracting article text: {str(e)}")
                continue

        if not all_articles_text:
            return "Unable to extract articles for summarization."

        # Prepare prompt for Anthropic
        prompt = f"""You are a professional news summarizer whose goal is to produce clear, concise, and factually accurate summaries of news content. Based solely on the information provided below, generate a summary that:
- Accurately reflects all key events, facts, and context included in the content.
- Is written in a neutral tone without adding any extra details or opinions.
- Uses only the information given and does not introduce any unverified or extraneous details.
- Is limited to no more than 150 words.

Content to summarize:
{' '.join(all_articles_text)}

Please provide ONLY the summary and NOTHING ELSE."""

        # Get summary from Anthropic
        summary = send_message_to_anthropic(prompt, model_name="claude-3-haiku-20240307")
        return summary

    except Exception as e:
        current_app.logger.error(f"Error getting combined summary: {str(e)}")
        return "Error generating combined summary."


def sanitize_keyword(keyword):
    """Sanitize search keyword"""
    # Remove any dangerous characters
    return re.sub(r'[^a-zA-Z0-9\s-]', '', keyword)