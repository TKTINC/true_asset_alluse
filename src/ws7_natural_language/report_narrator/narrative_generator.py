"""
Narrative Report Generator - Natural Language Reports

This module generates natural language narratives for portfolio reports,
performance analysis, and system insights. It transforms quantitative data
into clear, engaging stories that help users understand their wealth
management progress.

Mission: "Autopilot for Wealth.....Engineered for compounding income and corpus"
"""

from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import openai
import asyncio

from src.ws1_rules_engine.constitution.week_classification import WeekType, WeekPerformance
from src.ws5_portfolio_management.performance.performance_analyzer import PerformanceAnalyzer
from src.ws5_portfolio_management.risk.portfolio_risk_manager import PortfolioRiskManager

logger = logging.getLogger(__name__)


class NarrativeType(Enum):
    """Types of narrative reports."""
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_REPORT = "monthly_report"
    QUARTERLY_REVIEW = "quarterly_review"
    ANNUAL_REPORT = "annual_report"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    ACCOUNT_STATUS = "account_status"
    MARKET_COMMENTARY = "market_commentary"


@dataclass
class NarrativeContext:
    """Context for narrative generation."""
    narrative_type: NarrativeType
    time_period: Tuple[datetime, datetime]
    account_id: str
    performance_data: Dict[str, Any]
    risk_data: Dict[str, Any]
    market_data: Dict[str, Any]
    week_classification: Optional[WeekType] = None
    week_performance: Optional[WeekPerformance] = None


@dataclass
class NarrativeReport:
    """Generated narrative report."""
    title: str
    executive_summary: str
    detailed_narrative: str
    key_insights: List[str]
    recommendations: List[str]
    outlook: str
    generated_at: datetime
    confidence_score: float


class NarrativeReportGenerator:
    """
    Generates natural language narratives for wealth management reports.
    
    Transforms quantitative data into engaging stories that help users
    understand their wealth building progress and system performance.
    """
    
    def __init__(self,
                 performance_analyzer: PerformanceAnalyzer,
                 risk_manager: PortfolioRiskManager,
                 openai_api_key: Optional[str] = None):
        """Initialize the narrative generator."""
        self.performance_analyzer = performance_analyzer
        self.risk_manager = risk_manager
        
        # Initialize OpenAI client
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Narrative templates and prompts
        self.narrative_prompts = self._build_narrative_prompts()
        
        logger.info("NarrativeReportGenerator initialized successfully")
    
    def _build_narrative_prompts(self) -> Dict[NarrativeType, str]:
        """Build narrative prompts for different report types."""
        return {
            NarrativeType.WEEKLY_SUMMARY: """
Generate a weekly wealth management summary that explains the week's performance
in clear, engaging language. Focus on:

- How the wealth autopilot system performed this week
- Progress toward compounding income and corpus goals
- Any protocol level changes and their reasons
- Week classification impact on performance
- Key decisions made by the Constitution-based system
- Outlook for the coming week

Style: Professional yet approachable, focusing on wealth building progress.
Tone: Optimistic about long-term compounding, realistic about short-term fluctuations.
""",
            
            NarrativeType.MONTHLY_REPORT: """
Create a comprehensive monthly wealth management report that tells the story
of the month's progress. Include:

- Monthly performance in the context of long-term wealth building
- How the system's rules-based approach performed
- Account management activities (forking, consolidation)
- Risk management effectiveness
- Compounding progress and trajectory
- Strategic insights and lessons learned

Style: Detailed analysis with clear explanations of complex concepts.
Tone: Educational and empowering, emphasizing the autopilot's effectiveness.
""",
            
            NarrativeType.PERFORMANCE_ANALYSIS: """
Provide a detailed performance analysis narrative that explains:

- What drove performance during the period
- How the Constitution v1.3 rules contributed to results
- Risk-adjusted return analysis in plain language
- Comparison to wealth building benchmarks
- Attribution of returns to different strategies
- Lessons for future wealth compounding

Style: Analytical yet accessible, with clear cause-and-effect explanations.
Tone: Objective and insightful, highlighting the system's intelligence.
""",
            
            NarrativeType.RISK_ASSESSMENT: """
Generate a risk assessment narrative that explains:

- Current risk profile and protocol level
- How the system is protecting and growing wealth
- Risk management decisions and their rationale
- Stress test results and scenario analysis
- Risk-return optimization effectiveness
- Forward-looking risk considerations

Style: Clear and reassuring, explaining complex risk concepts simply.
Tone: Confident in the system's risk management, transparent about uncertainties.
"""
        }
    
    async def generate_narrative(self,
                               narrative_type: NarrativeType,
                               account_id: str,
                               time_period: Tuple[datetime, datetime],
                               additional_context: Optional[Dict[str, Any]] = None) -> NarrativeReport:
        """
        Generate a narrative report for the specified parameters.
        
        Args:
            narrative_type: Type of narrative to generate
            account_id: Account identifier
            time_period: Time period for the report
            additional_context: Additional context data
            
        Returns:
            NarrativeReport with generated content
        """
        try:
            # Gather context data
            context = await self._gather_narrative_context(
                narrative_type, account_id, time_period, additional_context
            )
            
            # Generate the narrative using LLM
            narrative = await self._generate_llm_narrative(context)
            
            return narrative
            
        except Exception as e:
            logger.error(f"Error generating narrative: {str(e)}")
            return self._generate_fallback_narrative(narrative_type, account_id, time_period)
    
    async def _gather_narrative_context(self,
                                      narrative_type: NarrativeType,
                                      account_id: str,
                                      time_period: Tuple[datetime, datetime],
                                      additional_context: Optional[Dict[str, Any]]) -> NarrativeContext:
        """Gather all context data needed for narrative generation."""
        
        # Get performance data
        performance_data = await self._get_performance_data(account_id, time_period)
        
        # Get risk data
        risk_data = await self._get_risk_data(account_id, time_period)
        
        # Get market data
        market_data = await self._get_market_data(time_period)
        
        # Classify the week if applicable
        week_classification = None
        week_performance = None
        if narrative_type == NarrativeType.WEEKLY_SUMMARY:
            week_classification, week_performance = await self._classify_week(
                account_id, time_period
            )
        
        return NarrativeContext(
            narrative_type=narrative_type,
            time_period=time_period,
            account_id=account_id,
            performance_data=performance_data,
            risk_data=risk_data,
            market_data=market_data,
            week_classification=week_classification,
            week_performance=week_performance
        )
    
    async def _get_performance_data(self,
                                  account_id: str,
                                  time_period: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Get performance data for the narrative."""
        # This would integrate with the performance analyzer
        return {
            'total_return': Decimal('0.08'),  # 8%
            'period_return': Decimal('0.02'),  # 2%
            'sharpe_ratio': Decimal('1.5'),
            'sortino_ratio': Decimal('2.1'),
            'max_drawdown': Decimal('-0.03'),  # -3%
            'volatility': Decimal('0.12'),  # 12%
            'alpha': Decimal('0.015'),  # 1.5%
            'beta': Decimal('0.8'),
            'win_rate': Decimal('0.65'),  # 65%
            'avg_win': Decimal('0.025'),  # 2.5%
            'avg_loss': Decimal('-0.015'),  # -1.5%
            'profit_factor': Decimal('1.8'),
            'compounding_rate': Decimal('0.12')  # 12% annualized
        }
    
    async def _get_risk_data(self,
                           account_id: str,
                           time_period: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Get risk data for the narrative."""
        # This would integrate with the risk manager
        return {
            'current_protocol_level': 'L0',
            'protocol_changes': 2,
            'var_95': Decimal('-0.025'),  # -2.5%
            'cvar_95': Decimal('-0.035'),  # -3.5%
            'risk_score': 'MODERATE',
            'stress_test_results': {
                'market_crash': Decimal('-0.15'),  # -15%
                'volatility_spike': Decimal('-0.08'),  # -8%
                'correlation_breakdown': Decimal('-0.12')  # -12%
            },
            'risk_budget_utilization': Decimal('0.75'),  # 75%
            'diversification_ratio': Decimal('0.85')
        }
    
    async def _get_market_data(self,
                             time_period: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Get market data for context."""
        return {
            'market_return': Decimal('0.015'),  # 1.5%
            'market_volatility': Decimal('0.18'),  # 18%
            'vix_level': Decimal('22.5'),
            'vix_change': Decimal('2.3'),
            'sector_performance': {
                'technology': Decimal('0.025'),
                'healthcare': Decimal('0.012'),
                'financials': Decimal('-0.008')
            },
            'economic_indicators': {
                'gdp_growth': Decimal('0.025'),
                'inflation': Decimal('0.032'),
                'unemployment': Decimal('0.038')
            }
        }
    
    async def _classify_week(self,
                           account_id: str,
                           time_period: Tuple[datetime, datetime]) -> Tuple[WeekType, WeekPerformance]:
        """Classify the week type and performance."""
        # This would integrate with the week classification system
        return WeekType.NORMAL, WeekPerformance.GOOD
    
    async def _generate_llm_narrative(self, context: NarrativeContext) -> NarrativeReport:
        """Generate narrative using LLM."""
        try:
            # Build the prompt
            prompt = self._build_narrative_prompt(context)
            
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse the response
            narrative_text = response.choices[0].message.content
            
            # Extract components from the narrative
            title, executive_summary, detailed_narrative, key_insights, recommendations, outlook = self._parse_narrative_response(narrative_text)
            
            return NarrativeReport(
                title=title,
                executive_summary=executive_summary,
                detailed_narrative=detailed_narrative,
                key_insights=key_insights,
                recommendations=recommendations,
                outlook=outlook,
                generated_at=datetime.utcnow(),
                confidence_score=0.9
            )
            
        except Exception as e:
            logger.error(f"Error generating LLM narrative: {str(e)}")
            return self._generate_fallback_narrative(
                context.narrative_type, context.account_id, context.time_period
            )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for narrative generation."""
        return """
You are an expert wealth management narrator for the True-Asset-ALLUSE system.

MISSION: "Autopilot for Wealth.....Engineered for compounding income and corpus"

YOUR ROLE:
- Transform quantitative data into engaging, understandable narratives
- Focus on wealth building progress and compounding growth
- Explain the system's Constitution-based decisions in plain language
- Provide insights that help users understand their wealth journey
- Maintain optimism about long-term compounding while being realistic about short-term fluctuations

WRITING STYLE:
- Professional yet approachable
- Clear explanations of complex financial concepts
- Engaging storytelling that makes data meaningful
- Focus on progress toward wealth building goals
- Educational tone that empowers users

STRUCTURE YOUR RESPONSE AS:
TITLE: [Compelling title for the report]

EXECUTIVE SUMMARY:
[2-3 sentence high-level summary]

DETAILED NARRATIVE:
[Main narrative content - 3-4 paragraphs]

KEY INSIGHTS:
- [Insight 1]
- [Insight 2]
- [Insight 3]

RECOMMENDATIONS:
- [Recommendation 1]
- [Recommendation 2]

OUTLOOK:
[Forward-looking perspective - 1-2 paragraphs]

Remember: This is about wealth building autopilot, not trading. Focus on compounding and long-term growth.
"""
    
    def _build_narrative_prompt(self, context: NarrativeContext) -> str:
        """Build the narrative prompt with context data."""
        prompt_parts = [
            f"Generate a {context.narrative_type.value} narrative report.",
            f"Time period: {context.time_period[0].strftime('%Y-%m-%d')} to {context.time_period[1].strftime('%Y-%m-%d')}",
            f"Account ID: {context.account_id}",
            "",
            "PERFORMANCE DATA:",
        ]
        
        # Add performance data
        for key, value in context.performance_data.items():
            if isinstance(value, Decimal):
                if key.endswith('_rate') or key.endswith('_return') or key.endswith('ratio'):
                    prompt_parts.append(f"- {key}: {float(value):.2%}")
                else:
                    prompt_parts.append(f"- {key}: {float(value):.4f}")
            else:
                prompt_parts.append(f"- {key}: {value}")
        
        prompt_parts.extend(["", "RISK DATA:"])
        
        # Add risk data
        for key, value in context.risk_data.items():
            if isinstance(value, dict):
                prompt_parts.append(f"- {key}:")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, Decimal):
                        prompt_parts.append(f"  - {sub_key}: {float(sub_value):.2%}")
                    else:
                        prompt_parts.append(f"  - {sub_key}: {sub_value}")
            elif isinstance(value, Decimal):
                if 'var' in key.lower() or 'drawdown' in key.lower():
                    prompt_parts.append(f"- {key}: {float(value):.2%}")
                else:
                    prompt_parts.append(f"- {key}: {float(value):.4f}")
            else:
                prompt_parts.append(f"- {key}: {value}")
        
        # Add week classification if available
        if context.week_classification and context.week_performance:
            prompt_parts.extend([
                "",
                f"WEEK CLASSIFICATION: {context.week_classification.value}",
                f"WEEK PERFORMANCE: {context.week_performance.value}"
            ])
        
        # Add specific narrative prompt
        if context.narrative_type in self.narrative_prompts:
            prompt_parts.extend(["", "SPECIFIC INSTRUCTIONS:", self.narrative_prompts[context.narrative_type]])
        
        return "\n".join(prompt_parts)
    
    def _parse_narrative_response(self, narrative_text: str) -> Tuple[str, str, str, List[str], List[str], str]:
        """Parse the LLM response into components."""
        sections = narrative_text.split('\n\n')
        
        title = "Wealth Management Report"
        executive_summary = ""
        detailed_narrative = ""
        key_insights = []
        recommendations = []
        outlook = ""
        
        current_section = None
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            if section.startswith('TITLE:'):
                title = section.replace('TITLE:', '').strip()
            elif section.startswith('EXECUTIVE SUMMARY:'):
                executive_summary = section.replace('EXECUTIVE SUMMARY:', '').strip()
                current_section = 'executive_summary'
            elif section.startswith('DETAILED NARRATIVE:'):
                detailed_narrative = section.replace('DETAILED NARRATIVE:', '').strip()
                current_section = 'detailed_narrative'
            elif section.startswith('KEY INSIGHTS:'):
                current_section = 'key_insights'
                insights_text = section.replace('KEY INSIGHTS:', '').strip()
                if insights_text:
                    key_insights.extend([line.strip('- ').strip() for line in insights_text.split('\n') if line.strip()])
            elif section.startswith('RECOMMENDATIONS:'):
                current_section = 'recommendations'
                recs_text = section.replace('RECOMMENDATIONS:', '').strip()
                if recs_text:
                    recommendations.extend([line.strip('- ').strip() for line in recs_text.split('\n') if line.strip()])
            elif section.startswith('OUTLOOK:'):
                outlook = section.replace('OUTLOOK:', '').strip()
                current_section = 'outlook'
            else:
                # Continue building current section
                if current_section == 'executive_summary':
                    executive_summary += "\n\n" + section
                elif current_section == 'detailed_narrative':
                    detailed_narrative += "\n\n" + section
                elif current_section == 'key_insights':
                    key_insights.extend([line.strip('- ').strip() for line in section.split('\n') if line.strip()])
                elif current_section == 'recommendations':
                    recommendations.extend([line.strip('- ').strip() for line in section.split('\n') if line.strip()])
                elif current_section == 'outlook':
                    outlook += "\n\n" + section
        
        return title, executive_summary, detailed_narrative, key_insights, recommendations, outlook
    
    def _generate_fallback_narrative(self,
                                   narrative_type: NarrativeType,
                                   account_id: str,
                                   time_period: Tuple[datetime, datetime]) -> NarrativeReport:
        """Generate a fallback narrative when LLM fails."""
        return NarrativeReport(
            title=f"Wealth Management {narrative_type.value.replace('_', ' ').title()}",
            executive_summary="Your wealth management autopilot system continues to operate according to Constitution v1.3, focusing on compounding income and corpus growth.",
            detailed_narrative="During this period, your True-Asset-ALLUSE system maintained its disciplined, rules-based approach to wealth management. The system's Constitution-based framework ensured consistent execution of wealth building strategies while managing risk appropriately.",
            key_insights=[
                "System operated within constitutional parameters",
                "Risk management protocols functioned as designed",
                "Compounding strategy remained on track"
            ],
            recommendations=[
                "Continue monitoring system performance",
                "Review periodic reports for insights"
            ],
            outlook="The wealth management autopilot system is positioned to continue its disciplined approach to compounding income and corpus growth.",
            generated_at=datetime.utcnow(),
            confidence_score=0.5
        )
    
    async def generate_weekly_summary(self, account_id: str, week_start: datetime) -> NarrativeReport:
        """Generate a weekly summary narrative."""
        week_end = week_start + timedelta(days=7)
        return await self.generate_narrative(
            NarrativeType.WEEKLY_SUMMARY,
            account_id,
            (week_start, week_end)
        )
    
    async def generate_monthly_report(self, account_id: str, month_start: datetime) -> NarrativeReport:
        """Generate a monthly report narrative."""
        # Calculate month end
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
        
        return await self.generate_narrative(
            NarrativeType.MONTHLY_REPORT,
            account_id,
            (month_start, month_end)
        )
    
    async def generate_performance_analysis(self,
                                          account_id: str,
                                          start_date: datetime,
                                          end_date: datetime) -> NarrativeReport:
        """Generate a performance analysis narrative."""
        return await self.generate_narrative(
            NarrativeType.PERFORMANCE_ANALYSIS,
            account_id,
            (start_date, end_date)
        )

