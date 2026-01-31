"""
Agent Orchestrator
Coordinates multi-agent pipeline and generates traces
"""
from datetime import datetime, timezone
from typing import Optional
import uuid
import time

from app.schemas.trace import (
    AgentTrace, AgentStep, AgentName, AgentDecision
)
from app.schemas.search import (
    SearchRequest, SearchResponse, ProductResult, 
    AlternativeProduct, FinancialAnalysis, AffordabilityStatus
)
from app.schemas.profile import ProfileResponse


class AgentContext:
    """Context passed between agents"""
    def __init__(
        self,
        trace_id: str,
        request_id: str,
        user_id: str,
        profile: Optional[ProfileResponse],
        search_request: SearchRequest
    ):
        self.trace_id = trace_id
        self.request_id = request_id
        self.user_id = user_id
        self.profile = profile
        self.search_request = search_request
        self.steps: list[AgentStep] = []
        self.products: list[dict] = []
        self.alternatives: list[dict] = []
        self.final_decision = AgentDecision.PASS
        
    def add_step(self, step: AgentStep):
        self.steps.append(step)


class DiscoveryAgent:
    """Agent 1: Product Discovery via vector search"""
    
    async def execute(self, ctx: AgentContext) -> list[dict]:
        start = datetime.now(timezone.utc)
        start_ms = time.time() * 1000
        
        # Simulate vector search (replace with Qdrant in production)
        # In production: embed query -> search Qdrant -> return products
        products = self._mock_search(ctx.search_request)
        
        end = datetime.now(timezone.utc)
        duration_ms = int(time.time() * 1000 - start_ms)
        
        ctx.add_step(AgentStep(
            agent=AgentName.DISCOVERY,
            started_at=start,
            completed_at=end,
            duration_ms=duration_ms,
            input={
                "query": ctx.search_request.query,
                "search_type": ctx.search_request.search_type.value,
                "filters": ctx.search_request.filters.model_dump() if ctx.search_request.filters else {}
            },
            output={
                "products_found": len(products),
                "search_strategy": "semantic_vector",
                "vector_similarity_scores": [0.95, 0.89, 0.85, 0.82, 0.78][:len(products)]
            },
            decision=AgentDecision.PASS,
            confidence=0.92
        ))
        
        return products
    
    def _mock_search(self, request: SearchRequest) -> list[dict]:
        """Mock product data - replace with real Qdrant search"""
        base_products = [
            {
                "id": "prod_001",
                "name": "Sony WH-1000XM5 Wireless Headphones",
                "description": "Industry-leading noise cancellation with premium sound quality",
                "price": 349.99,
                "original_price": 399.99,
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400",
                "product_url": "https://example.com/sony-wh1000xm5",
                "brand": "Sony",
                "category": "Electronics",
                "rating": 4.8,
                "review_count": 2847,
                "in_stock": True
            },
            {
                "id": "prod_002",
                "name": "Apple AirPods Pro 2nd Gen",
                "description": "Active noise cancellation with spatial audio",
                "price": 249.00,
                "image_url": "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?w=400",
                "product_url": "https://example.com/airpods-pro",
                "brand": "Apple",
                "category": "Electronics",
                "rating": 4.7,
                "review_count": 5621,
                "in_stock": True
            },
            {
                "id": "prod_003",
                "name": "Bose QuietComfort 45",
                "description": "Legendary noise cancellation with all-day comfort",
                "price": 279.00,
                "original_price": 329.00,
                "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=400",
                "product_url": "https://example.com/bose-qc45",
                "brand": "Bose",
                "category": "Electronics",
                "rating": 4.6,
                "review_count": 1893,
                "in_stock": True
            },
            {
                "id": "prod_004",
                "name": "Sennheiser HD 660S",
                "description": "Audiophile open-back headphones for studio listening",
                "price": 499.95,
                "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=400",
                "product_url": "https://example.com/sennheiser-hd660s",
                "brand": "Sennheiser",
                "category": "Electronics",
                "rating": 4.9,
                "review_count": 456,
                "in_stock": True
            },
            {
                "id": "prod_005",
                "name": "JBL Tune 760NC",
                "description": "Affordable wireless with active noise cancelling",
                "price": 79.95,
                "original_price": 129.95,
                "image_url": "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=400",
                "product_url": "https://example.com/jbl-tune760",
                "brand": "JBL",
                "category": "Electronics",
                "rating": 4.3,
                "review_count": 3421,
                "in_stock": True
            }
        ]
        
        # Apply price filters if present
        if request.filters:
            if request.filters.min_price:
                base_products = [p for p in base_products if p["price"] >= request.filters.min_price]
            if request.filters.max_price:
                base_products = [p for p in base_products if p["price"] <= request.filters.max_price]
        
        return base_products


class FinancialAnalyzerAgent:
    """Agent 2: Financial Analysis and Risk Assessment"""
    
    async def execute(self, ctx: AgentContext, products: list[dict]) -> list[dict]:
        start = datetime.now(timezone.utc)
        start_ms = time.time() * 1000
        
        analyzed_products = []
        rejected_ids = []
        warnings = []
        
        for product in products:
            analysis = self._analyze_product(product, ctx.profile)
            product["financial_analysis"] = analysis
            
            if analysis["affordability_status"] == "unaffordable":
                rejected_ids.append(product["id"])
            elif analysis["affordability_status"] == "caution":
                warnings.append(f"{product['name']}: {analysis['risk_factors'][0] if analysis['risk_factors'] else 'Proceed with caution'}")
            
            analyzed_products.append(product)
        
        end = datetime.now(timezone.utc)
        duration_ms = int(time.time() * 1000 - start_ms)
        
        # Determine decision
        decision = AgentDecision.APPROVE
        reason = "Products within financial limits"
        
        if len(rejected_ids) == len(products):
            decision = AgentDecision.REJECT
            reason = "All products exceed safe spending limits"
            ctx.final_decision = AgentDecision.REJECT
        elif rejected_ids:
            decision = AgentDecision.WARN
            reason = f"{len(rejected_ids)} products flagged as unaffordable"
        
        # Calculate DTI impact
        dti_before = 0.0
        dti_after = 0.0
        if ctx.profile:
            dti_before = ctx.profile.current_debt / (ctx.profile.monthly_income * 12) if ctx.profile.monthly_income > 0 else 0
            max_price = max(p["price"] for p in products) if products else 0
            dti_after = (ctx.profile.current_debt + max_price) / (ctx.profile.monthly_income * 12) if ctx.profile.monthly_income > 0 else 0
        
        ctx.add_step(AgentStep(
            agent=AgentName.FINANCIAL,
            started_at=start,
            completed_at=end,
            duration_ms=duration_ms,
            input={
                "products_count": len(products),
                "user_income": ctx.profile.monthly_income if ctx.profile else None,
                "user_debt": ctx.profile.current_debt if ctx.profile else None
            },
            output={
                "dti_before": round(dti_before, 3),
                "dti_after": round(dti_after, 3),
                "affordability_scores": {p["id"]: p["financial_analysis"]["affordability_score"] for p in analyzed_products},
                "rejected_products": rejected_ids,
                "warnings": warnings
            },
            decision=decision,
            decision_reason=reason,
            confidence=0.88
        ))
        
        return analyzed_products
    
    def _analyze_product(self, product: dict, profile: Optional[ProfileResponse]) -> dict:
        """Analyze product affordability"""
        price = product["price"]
        
        if not profile:
            return {
                "affordability_status": "caution",
                "affordability_score": 50,
                "price_to_income_ratio": 0,
                "impact_on_dti": 0,
                "impact_on_savings": 0,
                "months_to_save": 0,
                "risk_factors": ["No financial profile - unable to assess"],
                "recommended_financing": None,
                "monthly_payment_estimate": None,
                "approval_likelihood": None
            }
        
        monthly_income = profile.monthly_income
        monthly_expenses = profile.monthly_expenses
        disposable = monthly_income - monthly_expenses
        savings = profile.savings
        
        # Calculate metrics
        pti = price / monthly_income if monthly_income > 0 else 1
        impact_on_savings = price / savings if savings > 0 else 1
        months_to_save = price / disposable if disposable > 0 else 99
        
        # Calculate affordability score (0-100)
        score = 100
        
        # Deduct for PTI
        if pti > 0.5:
            score -= 40
        elif pti > 0.3:
            score -= 20
        elif pti > 0.2:
            score -= 10
        
        # Deduct for savings impact
        if impact_on_savings > 0.5:
            score -= 30
        elif impact_on_savings > 0.25:
            score -= 15
        
        # Deduct for time to save
        if months_to_save > 6:
            score -= 20
        elif months_to_save > 3:
            score -= 10
        
        score = max(0, min(100, score))
        
        # Determine status
        if score >= 70:
            status = "affordable"
        elif score >= 40:
            status = "caution"
        else:
            status = "unaffordable"
        
        # Risk factors
        risk_factors = []
        if pti > 0.3:
            risk_factors.append(f"High price-to-income ratio ({pti:.1%})")
        if impact_on_savings > 0.3:
            risk_factors.append(f"Would use {impact_on_savings:.1%} of savings")
        if months_to_save > 3:
            risk_factors.append(f"Would take {months_to_save:.1f} months to save")
        
        # Financing recommendation
        financing = None
        monthly_payment = None
        if price > 200 and status != "affordable":
            financing = "Consider 0% APR financing if available"
            monthly_payment = price / 12
        
        return {
            "affordability_status": status,
            "affordability_score": score,
            "price_to_income_ratio": round(pti, 3),
            "impact_on_dti": round(price / (monthly_income * 12), 3) if monthly_income > 0 else 0,
            "impact_on_savings": round(impact_on_savings, 3),
            "months_to_save": round(months_to_save, 1),
            "risk_factors": risk_factors,
            "recommended_financing": financing,
            "monthly_payment_estimate": round(monthly_payment, 2) if monthly_payment else None,
            "approval_likelihood": "high" if score >= 70 else "medium" if score >= 40 else "low"
        }


class PathFinderAgent:
    """Agent 2.5: Find alternatives for unaffordable products"""
    
    async def execute(self, ctx: AgentContext, products: list[dict]) -> list[dict]:
        start = datetime.now(timezone.utc)
        start_ms = time.time() * 1000
        
        alternatives = []
        
        # Find alternatives for products with caution/unaffordable status
        for product in products:
            if product["financial_analysis"]["affordability_status"] in ["caution", "unaffordable"]:
                alt = self._find_alternative(product, products)
                if alt:
                    alternatives.append(alt)
        
        end = datetime.now(timezone.utc)
        duration_ms = int(time.time() * 1000 - start_ms)
        
        ctx.add_step(AgentStep(
            agent=AgentName.PATHFINDER,
            started_at=start,
            completed_at=end,
            duration_ms=duration_ms,
            input={
                "products_to_analyze": len([p for p in products if p["financial_analysis"]["affordability_status"] != "affordable"])
            },
            output={
                "alternatives_found": len(alternatives),
                "clusters_analyzed": 3,
                "alternative_products": [a["product"]["id"] for a in alternatives],
                "savings_opportunities": {a["product"]["id"]: a["savings_vs_original"] for a in alternatives}
            },
            decision=AgentDecision.PASS,
            confidence=0.85
        ))
        
        ctx.alternatives = alternatives
        return alternatives
    
    def _find_alternative(self, product: dict, all_products: list[dict]) -> Optional[dict]:
        """Find a more affordable alternative"""
        price = product["price"]
        
        # Find cheaper products in same category
        cheaper = [
            p for p in all_products 
            if p["price"] < price * 0.7 
            and p["financial_analysis"]["affordability_status"] == "affordable"
            and p["id"] != product["id"]
        ]
        
        if not cheaper:
            return None
        
        # Pick best value (highest rating among affordable)
        best = max(cheaper, key=lambda x: x.get("rating", 0))
        
        return {
            "product": best,
            "reason": f"More affordable alternative to {product['name']}",
            "savings_vs_original": round(price - best["price"], 2),
            "trade_offs": self._identify_tradeoffs(product, best)
        }
    
    def _identify_tradeoffs(self, original: dict, alternative: dict) -> list[str]:
        """Identify trade-offs between products"""
        tradeoffs = []
        
        if alternative.get("rating", 0) < original.get("rating", 0):
            tradeoffs.append(f"Lower rating ({alternative.get('rating', 'N/A')} vs {original.get('rating', 'N/A')})")
        
        if alternative.get("brand") != original.get("brand"):
            tradeoffs.append(f"Different brand ({alternative.get('brand', 'Unknown')})")
        
        if not tradeoffs:
            tradeoffs.append("Similar quality at lower price")
        
        return tradeoffs


class RankingAgent:
    """Agent 3: Thompson Sampling-based ranking"""
    
    async def execute(self, ctx: AgentContext, products: list[dict]) -> list[dict]:
        start = datetime.now(timezone.utc)
        start_ms = time.time() * 1000
        
        # Apply Thompson Sampling ranking
        ranked = self._thompson_rank(products, ctx.user_id)
        
        end = datetime.now(timezone.utc)
        duration_ms = int(time.time() * 1000 - start_ms)
        
        ctx.add_step(AgentStep(
            agent=AgentName.RANKING,
            started_at=start,
            completed_at=end,
            duration_ms=duration_ms,
            input={
                "products_count": len(products),
                "user_id": ctx.user_id
            },
            output={
                "method": "thompson_sampling",
                "arm_selections": {p["id"]: i + 1 for i, p in enumerate(ranked)},
                "exploitation_vs_exploration": 0.7,
                "selected_order": [p["id"] for p in ranked]
            },
            decision=AgentDecision.PASS,
            confidence=0.90
        ))
        
        ctx.products = ranked
        return ranked
    
    def _thompson_rank(self, products: list[dict], user_id: str) -> list[dict]:
        """Apply Thompson Sampling ranking"""
        import random
        
        # In production: fetch alpha/beta from Redis per product
        # For now: rank by affordability score + some exploration
        
        def score(p):
            base = p["financial_analysis"]["affordability_score"]
            exploration = random.gauss(0, 5)  # Add noise for exploration
            return base + exploration
        
        return sorted(products, key=score, reverse=True)


class ExplainerAgent:
    """Agent 4: Generate human-readable explanations"""
    
    async def execute(self, ctx: AgentContext, products: list[dict]) -> list[dict]:
        start = datetime.now(timezone.utc)
        start_ms = time.time() * 1000
        
        summaries = {}
        
        for product in products:
            summary, why = self._generate_explanation(product, ctx.profile)
            product["ai_summary"] = summary
            product["why_recommended"] = why
            summaries[product["id"]] = summary
        
        end = datetime.now(timezone.utc)
        duration_ms = int(time.time() * 1000 - start_ms)
        
        ctx.add_step(AgentStep(
            agent=AgentName.EXPLAINER,
            started_at=start,
            completed_at=end,
            duration_ms=duration_ms,
            input={
                "products_count": len(products)
            },
            output={
                "summaries": summaries,
                "decision_explanation": self._get_overall_explanation(ctx),
                "key_factors": ["affordability", "user_preferences", "value_score"],
                "user_specific_insights": self._get_user_insights(ctx.profile)
            },
            decision=AgentDecision.PASS,
            confidence=0.95
        ))
        
        return products
    
    def _generate_explanation(self, product: dict, profile: Optional[ProfileResponse]) -> tuple[str, str]:
        """Generate AI summary and recommendation reason"""
        analysis = product["financial_analysis"]
        status = analysis["affordability_status"]
        score = analysis["affordability_score"]
        
        # Summary
        if status == "affordable":
            summary = f"This {product['brand']} product fits well within your budget with an affordability score of {score}/100."
        elif status == "caution":
            summary = f"Consider carefully - this purchase would use a significant portion of your disposable income (score: {score}/100)."
        else:
            summary = f"This exceeds recommended spending limits (score: {score}/100). Consider alternatives or saving up first."
        
        # Why recommended
        if score >= 70:
            why = "Recommended because it balances quality and affordability for your financial situation."
        elif score >= 40:
            why = "Included for comparison, but proceed with caution given your current financial goals."
        else:
            why = "Shown for reference only - we recommend looking at more affordable alternatives."
        
        return summary, why
    
    def _get_overall_explanation(self, ctx: AgentContext) -> str:
        """Get overall decision explanation"""
        if ctx.final_decision == AgentDecision.REJECT:
            return "Based on your financial profile, the requested products exceed safe spending limits. We've included alternatives that better match your budget."
        return "Products have been ranked by how well they fit your financial situation, with the most affordable options shown first."
    
    def _get_user_insights(self, profile: Optional[ProfileResponse]) -> list[str]:
        """Generate user-specific insights"""
        if not profile:
            return ["Complete your financial profile for personalized recommendations"]
        
        insights = []
        
        disposable = profile.monthly_income - profile.monthly_expenses
        if disposable > 1000:
            insights.append("Your healthy disposable income gives you flexibility for larger purchases")
        elif disposable > 500:
            insights.append("You have moderate spending flexibility - consider saving for bigger items")
        else:
            insights.append("Focus on essential purchases while building your savings buffer")
        
        if profile.savings > profile.monthly_expenses * 6:
            insights.append("Strong emergency fund - you can make discretionary purchases with confidence")
        elif profile.savings > profile.monthly_expenses * 3:
            insights.append("Good savings buffer - maintain it while making planned purchases")
        else:
            insights.append("Consider building emergency fund before large discretionary purchases")
        
        return insights


class AgentOrchestrator:
    """Orchestrates the multi-agent pipeline"""
    
    def __init__(self):
        self.discovery = DiscoveryAgent()
        self.financial = FinancialAnalyzerAgent()
        self.pathfinder = PathFinderAgent()
        self.ranking = RankingAgent()
        self.explainer = ExplainerAgent()
        
        # Trace storage (use Redis in production)
        self._traces: dict[str, AgentTrace] = {}
    
    async def search(
        self,
        request: SearchRequest,
        user_id: str,
        profile: Optional[ProfileResponse],
        request_id: str
    ) -> tuple[SearchResponse, AgentTrace]:
        """Execute full agent pipeline"""
        trace_id = str(uuid.uuid4())
        start = datetime.now(timezone.utc)
        start_ms = time.time() * 1000
        
        # Create context
        ctx = AgentContext(
            trace_id=trace_id,
            request_id=request_id,
            user_id=user_id,
            profile=profile,
            search_request=request
        )
        
        # Execute agents in sequence
        # 1. Discovery
        products = await self.discovery.execute(ctx)
        
        # 2. Financial Analysis
        products = await self.financial.execute(ctx, products)
        
        # 3. PathFinder (alternatives)
        alternatives = await self.pathfinder.execute(ctx, products)
        
        # 4. Ranking
        products = await self.ranking.execute(ctx, products)
        
        # 5. Explainer
        products = await self.explainer.execute(ctx, products)
        
        end = datetime.now(timezone.utc)
        total_duration = int(time.time() * 1000 - start_ms)
        
        # Build trace
        trace = AgentTrace(
            trace_id=trace_id,
            request_id=request_id,
            user_id=user_id,
            started_at=start,
            completed_at=end,
            total_duration_ms=total_duration,
            agents=ctx.steps,
            final_decision=ctx.final_decision if ctx.final_decision != AgentDecision.PASS else AgentDecision.APPROVE,
            products_returned=len(products),
            alternatives_returned=len(alternatives),
            original_query=request.query,
            applied_filters=request.filters.model_dump() if request.filters else {}
        )
        
        # Store trace
        self._traces[trace_id] = trace
        
        # Build response
        product_results = [
            ProductResult(
                id=p["id"],
                name=p["name"],
                description=p["description"],
                price=p["price"],
                original_price=p.get("original_price"),
                currency="USD",
                image_url=p["image_url"],
                product_url=p["product_url"],
                brand=p.get("brand"),
                category=p["category"],
                rating=p.get("rating"),
                review_count=p.get("review_count"),
                in_stock=p.get("in_stock", True),
                financial_analysis=FinancialAnalysis(**p["financial_analysis"]),
                ai_summary=p["ai_summary"],
                why_recommended=p.get("why_recommended")
            )
            for p in products
        ]
        
        alternative_results = [
            AlternativeProduct(
                product=ProductResult(
                    id=a["product"]["id"],
                    name=a["product"]["name"],
                    description=a["product"]["description"],
                    price=a["product"]["price"],
                    original_price=a["product"].get("original_price"),
                    currency="USD",
                    image_url=a["product"]["image_url"],
                    product_url=a["product"]["product_url"],
                    brand=a["product"].get("brand"),
                    category=a["product"]["category"],
                    rating=a["product"].get("rating"),
                    review_count=a["product"].get("review_count"),
                    in_stock=a["product"].get("in_stock", True),
                    financial_analysis=FinancialAnalysis(**a["product"]["financial_analysis"]),
                    ai_summary=a["product"]["ai_summary"],
                    why_recommended=a["product"].get("why_recommended")
                ),
                reason=a["reason"],
                savings_vs_original=a["savings_vs_original"],
                trade_offs=a["trade_offs"]
            )
            for a in alternatives
        ]
        
        response = SearchResponse(
            trace_id=trace_id,
            request_id=request_id,
            products=product_results,
            alternatives=alternative_results,
            total_results=len(product_results),
            page=request.page,
            page_size=request.page_size,
            total_pages=1,
            query_understood=f"Searching for: {request.query}",
            filters_applied=request.filters.model_dump() if request.filters else {},
            search_time_ms=total_duration
        )
        
        return response, trace
    
    def get_trace(self, trace_id: str) -> Optional[AgentTrace]:
        """Retrieve trace by ID"""
        return self._traces.get(trace_id)
    
    def get_user_traces(self, user_id: str, page: int = 1, page_size: int = 10) -> list[AgentTrace]:
        """Get traces for a user"""
        user_traces = [t for t in self._traces.values() if t.user_id == user_id]
        user_traces.sort(key=lambda t: t.started_at, reverse=True)
        
        start = (page - 1) * page_size
        return user_traces[start:start + page_size]


# Global orchestrator instance
orchestrator = AgentOrchestrator()
