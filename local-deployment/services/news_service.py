"""
News and Sentiment Integration Service
Real-time financial news and sentiment analysis for True-Asset-ALLUSE
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

try:
    from newsapi import NewsApiClient
    NEWSAPI_AVAILABLE = True
except ImportError:
    NEWSAPI_AVAILABLE = False
    logging.warning("newsapi-python not available. News API integration disabled.")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logging.warning("textblob not available. Sentiment analysis disabled.")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logging.warning("vaderSentiment not available. Advanced sentiment analysis disabled.")

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    logging.warning("feedparser not available. RSS feed parsing disabled.")

import httpx

from config_enhanced import config, DEFAULT_SYMBOLS

logger = logging.getLogger(__name__)

class NewsService:
    """News and sentiment service for market intelligence"""
    
    def __init__(self):
        self.news_client = None
        self.sentiment_analyzer = None
        self.connected = False
        self.news_cache = {}
        self.sentiment_cache = {}
        self.last_update = {}
        
        # Initialize sentiment analyzer
        if VADER_AVAILABLE:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        if not NEWSAPI_AVAILABLE:
            logger.warning("News service initialized without newsapi library")
    
    async def connect(self) -> bool:
        """Initialize news API client"""
        if not NEWSAPI_AVAILABLE or not config.news_enabled or not config.news_api_key:
            logger.info("News API integration disabled or API key not provided")
            return False
        
        try:
            self.news_client = NewsApiClient(api_key=config.news_api_key)
            
            # Test connection with a simple request
            test_news = self.news_client.get_top_headlines(
                sources='bloomberg',
                page_size=1
            )
            
            if test_news and test_news.get('status') == 'ok':
                self.connected = True
                logger.info("Connected to News API successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect to News API: {e}")
            self.connected = False
            return False
    
    async def get_financial_news(self, symbols: List[str] = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent financial news"""
        if not self.connected:
            return await self._get_fallback_news(symbols, hours)
        
        try:
            symbols = symbols or DEFAULT_SYMBOLS[:3]  # Limit to 3 symbols for API efficiency
            all_news = []
            
            # Get general financial news
            general_news = self.news_client.get_everything(
                q='finance OR stock market OR trading OR economy',
                sources=config.news_sources,
                from_param=(datetime.now() - timedelta(hours=hours)).isoformat(),
                sort_by='publishedAt',
                page_size=10
            )
            
            if general_news and general_news.get('articles'):
                for article in general_news['articles']:
                    news_item = await self._process_news_article(article, 'general')
                    if news_item:
                        all_news.append(news_item)
            
            # Get symbol-specific news
            for symbol in symbols:
                symbol_news = self.news_client.get_everything(
                    q=f'{symbol} stock OR {symbol} earnings OR {symbol} company',
                    from_param=(datetime.now() - timedelta(hours=hours)).isoformat(),
                    sort_by='publishedAt',
                    page_size=5
                )
                
                if symbol_news and symbol_news.get('articles'):
                    for article in symbol_news['articles']:
                        news_item = await self._process_news_article(article, symbol)
                        if news_item:
                            all_news.append(news_item)
            
            # Sort by publication date and remove duplicates
            unique_news = {}
            for news in all_news:
                url = news.get('url', '')
                if url not in unique_news:
                    unique_news[url] = news
            
            sorted_news = sorted(
                unique_news.values(),
                key=lambda x: x.get('published_at', ''),
                reverse=True
            )
            
            self.news_cache['latest'] = sorted_news[:20]  # Keep latest 20 articles
            self.last_update['news'] = datetime.now()
            
            return sorted_news[:20]
            
        except Exception as e:
            logger.error(f"Failed to get financial news: {e}")
            return await self._get_fallback_news(symbols, hours)
    
    async def _process_news_article(self, article: Dict[str, Any], symbol: str = 'general') -> Optional[Dict[str, Any]]:
        """Process and analyze a news article"""
        try:
            title = article.get('title', '')
            description = article.get('description', '')
            content = f"{title}. {description}"
            
            # Perform sentiment analysis
            sentiment_data = await self.analyze_sentiment(content)
            
            # Determine relevance and impact
            relevance_score = self._calculate_relevance(content, symbol)
            impact_score = self._calculate_impact(content, sentiment_data)
            
            return {
                'headline': title,
                'description': description,
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'published_at': article.get('publishedAt', ''),
                'symbol': symbol,
                'sentiment': sentiment_data,
                'relevance_score': relevance_score,
                'impact_score': impact_score,
                'category': self._categorize_news(content),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process news article: {e}")
            return None
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using multiple methods"""
        try:
            sentiment_data = {
                'compound_score': 0.0,
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 0.0,
                'classification': 'neutral',
                'confidence': 0.0
            }
            
            # VADER sentiment analysis (financial text optimized)
            if VADER_AVAILABLE and self.sentiment_analyzer:
                vader_scores = self.sentiment_analyzer.polarity_scores(text)
                sentiment_data.update({
                    'compound_score': vader_scores['compound'],
                    'positive': vader_scores['pos'],
                    'negative': vader_scores['neg'],
                    'neutral': vader_scores['neu']
                })
                
                # Classify based on compound score
                if vader_scores['compound'] >= 0.05:
                    sentiment_data['classification'] = 'positive'
                    sentiment_data['confidence'] = abs(vader_scores['compound'])
                elif vader_scores['compound'] <= -0.05:
                    sentiment_data['classification'] = 'negative'
                    sentiment_data['confidence'] = abs(vader_scores['compound'])
                else:
                    sentiment_data['classification'] = 'neutral'
                    sentiment_data['confidence'] = 1 - abs(vader_scores['compound'])
            
            # TextBlob sentiment analysis (backup)
            elif TEXTBLOB_AVAILABLE:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                
                sentiment_data.update({
                    'compound_score': polarity,
                    'positive': max(polarity, 0),
                    'negative': abs(min(polarity, 0)),
                    'neutral': 1 - abs(polarity)
                })
                
                if polarity > 0.1:
                    sentiment_data['classification'] = 'positive'
                elif polarity < -0.1:
                    sentiment_data['classification'] = 'negative'
                else:
                    sentiment_data['classification'] = 'neutral'
                
                sentiment_data['confidence'] = abs(polarity)
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            return {
                'compound_score': 0.0,
                'classification': 'neutral',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _calculate_relevance(self, content: str, symbol: str) -> float:
        """Calculate relevance score for content"""
        try:
            content_lower = content.lower()
            relevance_score = 0.0
            
            # Symbol-specific relevance
            if symbol != 'general':
                if symbol.lower() in content_lower:
                    relevance_score += 0.5
                
                # Company name mapping (simplified)
                company_names = {
                    'AAPL': 'apple',
                    'MSFT': 'microsoft',
                    'GOOGL': 'google',
                    'TSLA': 'tesla'
                }
                
                company_name = company_names.get(symbol, '').lower()
                if company_name and company_name in content_lower:
                    relevance_score += 0.3
            
            # Financial keywords
            financial_keywords = [
                'earnings', 'revenue', 'profit', 'loss', 'guidance',
                'dividend', 'buyback', 'acquisition', 'merger',
                'ipo', 'stock', 'shares', 'market', 'trading'
            ]
            
            for keyword in financial_keywords:
                if keyword in content_lower:
                    relevance_score += 0.1
            
            # Market impact keywords
            impact_keywords = [
                'federal reserve', 'fed', 'interest rates', 'inflation',
                'gdp', 'unemployment', 'recession', 'bull market', 'bear market'
            ]
            
            for keyword in impact_keywords:
                if keyword in content_lower:
                    relevance_score += 0.2
            
            return min(relevance_score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate relevance: {e}")
            return 0.5
    
    def _calculate_impact(self, content: str, sentiment_data: Dict[str, Any]) -> float:
        """Calculate potential market impact score"""
        try:
            impact_score = 0.0
            content_lower = content.lower()
            
            # Base impact from sentiment strength
            sentiment_strength = abs(sentiment_data.get('compound_score', 0))
            impact_score += sentiment_strength * 0.5
            
            # High-impact keywords
            high_impact_keywords = [
                'bankruptcy', 'lawsuit', 'investigation', 'fraud',
                'acquisition', 'merger', 'ipo', 'earnings beat',
                'earnings miss', 'guidance raised', 'guidance lowered'
            ]
            
            for keyword in high_impact_keywords:
                if keyword in content_lower:
                    impact_score += 0.3
            
            # Market-wide impact keywords
            market_keywords = [
                'federal reserve', 'interest rates', 'inflation',
                'recession', 'market crash', 'volatility'
            ]
            
            for keyword in market_keywords:
                if keyword in content_lower:
                    impact_score += 0.4
            
            return min(impact_score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate impact: {e}")
            return 0.3
    
    def _categorize_news(self, content: str) -> str:
        """Categorize news content"""
        try:
            content_lower = content.lower()
            
            if any(word in content_lower for word in ['earnings', 'revenue', 'profit', 'loss']):
                return 'earnings'
            elif any(word in content_lower for word in ['acquisition', 'merger', 'deal']):
                return 'corporate_action'
            elif any(word in content_lower for word in ['fed', 'federal reserve', 'interest rates']):
                return 'monetary_policy'
            elif any(word in content_lower for word in ['regulation', 'sec', 'lawsuit']):
                return 'regulatory'
            elif any(word in content_lower for word in ['product', 'launch', 'innovation']):
                return 'product_news'
            else:
                return 'general'
                
        except Exception as e:
            logger.error(f"Failed to categorize news: {e}")
            return 'general'
    
    async def get_market_sentiment_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get overall market sentiment summary"""
        try:
            news_articles = await self.get_financial_news(hours=hours)
            
            if not news_articles:
                return self._get_mock_sentiment_summary()
            
            # Aggregate sentiment data
            total_articles = len(news_articles)
            positive_count = sum(1 for article in news_articles if article.get('sentiment', {}).get('classification') == 'positive')
            negative_count = sum(1 for article in news_articles if article.get('sentiment', {}).get('classification') == 'negative')
            neutral_count = total_articles - positive_count - negative_count
            
            # Calculate weighted sentiment
            total_sentiment = sum(
                article.get('sentiment', {}).get('compound_score', 0) * article.get('relevance_score', 0.5)
                for article in news_articles
            )
            
            weighted_sentiment = total_sentiment / total_articles if total_articles > 0 else 0
            
            # Determine overall sentiment
            if weighted_sentiment > 0.1:
                overall_sentiment = 'positive'
            elif weighted_sentiment < -0.1:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            # Calculate confidence based on article count and sentiment consistency
            confidence = min(total_articles / 20, 1.0) * (1 - abs(weighted_sentiment - (positive_count - negative_count) / total_articles))
            
            return {
                'overall_sentiment': overall_sentiment,
                'sentiment_score': weighted_sentiment,
                'confidence': confidence,
                'article_count': total_articles,
                'positive_articles': positive_count,
                'negative_articles': negative_count,
                'neutral_articles': neutral_count,
                'positive_percentage': (positive_count / total_articles * 100) if total_articles > 0 else 0,
                'negative_percentage': (negative_count / total_articles * 100) if total_articles > 0 else 0,
                'top_categories': self._get_top_categories(news_articles),
                'high_impact_news': [
                    article for article in news_articles 
                    if article.get('impact_score', 0) > 0.7
                ][:5],
                'timestamp': datetime.now().isoformat(),
                'data_source': 'News_API_Live'
            }
            
        except Exception as e:
            logger.error(f"Failed to get market sentiment summary: {e}")
            return self._get_mock_sentiment_summary()
    
    def _get_top_categories(self, news_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get top news categories"""
        try:
            category_counts = {}
            
            for article in news_articles:
                category = article.get('category', 'general')
                category_counts[category] = category_counts.get(category, 0) + 1
            
            sorted_categories = sorted(
                category_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return [
                {'category': cat, 'count': count}
                for cat, count in sorted_categories[:5]
            ]
            
        except Exception as e:
            logger.error(f"Failed to get top categories: {e}")
            return []
    
    async def _get_fallback_news(self, symbols: List[str] = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Fallback news using RSS feeds"""
        if not FEEDPARSER_AVAILABLE:
            return self._get_mock_news()
        
        try:
            # RSS feeds for financial news
            rss_feeds = [
                'https://feeds.bloomberg.com/markets/news.rss',
                'https://www.cnbc.com/id/100003114/device/rss/rss.html',
                'https://feeds.reuters.com/reuters/businessNews'
            ]
            
            all_news = []
            
            async with httpx.AsyncClient() as client:
                for feed_url in rss_feeds:
                    try:
                        response = await client.get(feed_url, timeout=10)
                        if response.status_code == 200:
                            feed = feedparser.parse(response.text)
                            
                            for entry in feed.entries[:5]:  # Limit to 5 per feed
                                news_item = {
                                    'headline': entry.get('title', ''),
                                    'description': entry.get('summary', ''),
                                    'url': entry.get('link', ''),
                                    'source': feed.feed.get('title', 'RSS Feed'),
                                    'published_at': entry.get('published', ''),
                                    'symbol': 'general',
                                    'sentiment': await self.analyze_sentiment(entry.get('title', '') + ' ' + entry.get('summary', '')),
                                    'relevance_score': 0.5,
                                    'impact_score': 0.3,
                                    'category': 'general',
                                    'timestamp': datetime.now().isoformat()
                                }
                                all_news.append(news_item)
                    
                    except Exception as e:
                        logger.error(f"Failed to fetch RSS feed {feed_url}: {e}")
                        continue
            
            return all_news[:15]  # Return top 15 articles
            
        except Exception as e:
            logger.error(f"RSS fallback failed: {e}")
            return self._get_mock_news()
    
    def _get_mock_news(self) -> List[Dict[str, Any]]:
        """Generate mock news data"""
        mock_headlines = [
            "Market opens higher on positive economic data",
            "Tech stocks lead gains in morning trading",
            "Federal Reserve maintains current interest rate policy",
            "Earnings season shows mixed results across sectors",
            "Options activity increases amid market volatility"
        ]
        
        mock_news = []
        for i, headline in enumerate(mock_headlines):
            mock_news.append({
                'headline': headline,
                'description': f"Market analysis and implications of {headline.lower()}",
                'url': f"https://example.com/news/{i}",
                'source': 'Mock Financial News',
                'published_at': (datetime.now() - timedelta(hours=i)).isoformat(),
                'symbol': 'general',
                'sentiment': {
                    'classification': 'positive' if i % 2 == 0 else 'neutral',
                    'compound_score': 0.3 if i % 2 == 0 else 0.0,
                    'confidence': 0.7
                },
                'relevance_score': 0.8,
                'impact_score': 0.4,
                'category': 'general',
                'timestamp': datetime.now().isoformat()
            })
        
        return mock_news
    
    def _get_mock_sentiment_summary(self) -> Dict[str, Any]:
        """Generate mock sentiment summary"""
        return {
            'overall_sentiment': 'positive',
            'sentiment_score': 0.15,
            'confidence': 0.75,
            'article_count': 15,
            'positive_articles': 8,
            'negative_articles': 3,
            'neutral_articles': 4,
            'positive_percentage': 53.3,
            'negative_percentage': 20.0,
            'top_categories': [
                {'category': 'general', 'count': 8},
                {'category': 'earnings', 'count': 4},
                {'category': 'monetary_policy', 'count': 3}
            ],
            'high_impact_news': [],
            'timestamp': datetime.now().isoformat(),
            'data_source': 'Mock_Data'
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check news service health"""
        if not NEWSAPI_AVAILABLE:
            return {
                "status": "limited",
                "message": "newsapi library not available, using RSS fallback",
                "connected": False,
                "fallback_available": FEEDPARSER_AVAILABLE
            }
        
        if not config.news_enabled:
            return {
                "status": "disabled",
                "message": "News API integration disabled in configuration",
                "connected": False
            }
        
        if not config.news_api_key:
            return {
                "status": "no_api_key",
                "message": "News API key not provided, using fallback",
                "connected": False,
                "fallback_available": FEEDPARSER_AVAILABLE
            }
        
        if not self.connected:
            connected = await self.connect()
            if not connected:
                return {
                    "status": "connection_failed",
                    "message": "Failed to connect to News API, using fallback",
                    "connected": False,
                    "fallback_available": FEEDPARSER_AVAILABLE
                }
        
        try:
            # Test with a simple news request
            test_news = await self.get_financial_news(hours=1)
            
            return {
                "status": "healthy",
                "message": "Connected to News API",
                "connected": True,
                "sources": config.news_sources.split(','),
                "last_article_count": len(test_news),
                "sentiment_analysis_available": VADER_AVAILABLE or TEXTBLOB_AVAILABLE
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"News API error: {e}",
                "connected": False
            }

# Global service instance
news_service = NewsService()

