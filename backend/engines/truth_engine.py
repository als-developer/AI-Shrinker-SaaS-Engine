import asyncio
import hashlib
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
from collections import defaultdict

from .base_engine import BaseEngine
from ..database.models import db
from ..services.cache_service import cache
from ..utils.logger import get_logger

logger = get_logger(__name__)

class TruthEngine(BaseEngine):
    def __init__(self):
        super().__init__("TruthEngine")
        self.sources = [
            "semantic_db",
            "web_crawl", 
            "fact_check_api",
            "academic_papers",
            "social_media_consensus",
            "expert_review"
        ]
        self.confidence_threshold = 0.7
        self.misinfo_patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict:
        """Load misinformation patterns"""
        return {
            "conspiracy": [
                r"(?i)they don't want you to know",
                r"(?i)secret (plan|agenda)",
                r"(?i)deep state",
                r"(?i)cover[- ]up",
                r"(?i)they are hiding"
            ],
            "fake_news": [
                r"(?i)breaking.*news.*alert",
                r"(?i)viral.*story",
                r"(?i)shocking.*truth",
                r"(?i)you won't believe"
            ],
            "misinformation": [
                r"(?i)according to (anonymous|source)",
                r"(?i)reports (suggest|indicate)",
                r"(?i)allegedly",
                r"(?i)rumor has it"
            ]
        }
    
    async def verify(self, text: str) -> Dict[str, Any]:
        """Verify text claims"""
        
        # Check cache
        cache_key = f"truth:{hashlib.md5(text.encode()).hexdigest()}"
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for text: {text[:50]}...")
            return json.loads(cached)
        
        # Run verification in parallel
        tasks = [
            self._check_semantic_db(text),
            self._check_web_sources(text),
            self._check_ai_hallucination(text),
            self._check_fact_check_api(text),
            self._analyze_sentiment(text),
            self._extract_claims(text),
            self._check_patterns(text)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Aggregate results
        semantic_result, web_result, ai_result, factcheck_result, sentiment, claims, patterns = results
        
        confidence_scores = [
            semantic_result["confidence"],
            web_result["confidence"],
            ai_result["confidence"],
            factcheck_result["confidence"]
        ]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Calculate risk score
        risk_score = (1 - avg_confidence) * 100
        
        # Determine verdict
        if avg_confidence > 0.85:
            verdict = "VERIFIED_TRUE"
            color = "green"
        elif avg_confidence > 0.60:
            verdict = "LIKELY_TRUE"
            color = "lightgreen"
        elif avg_confidence > 0.40:
            verdict = "UNCERTAIN"
            color = "yellow"
        elif avg_confidence > 0.20:
            verdict = "LIKELY_FALSE"
            color = "orange"
        else:
            verdict = "VERIFIED_FALSE"
            color = "red"
        
        result = {
            "engine": self.name,
            "text_preview": text[:500],
            "text_hash": hashlib.md5(text.encode()).hexdigest(),
            "verdict": verdict,
            "color": color,
            "confidence_percentage": round(avg_confidence * 100, 2),
            "risk_score": round(risk_score, 2),
            "sources_checked": self.sources,
            "source_details": {
                "semantic_db": semantic_result,
                "web_crawl": web_result,
                "ai_hallucination": ai_result,
                "fact_check": factcheck_result
            },
            "sentiment": sentiment,
            "claims_extracted": claims,
            "detected_patterns": patterns,
            "recommendation": self._get_recommendation(verdict, risk_score),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache result
        await cache.set(cache_key, json.dumps(result), expire=3600)
        
        # Store in database
        await self._store_verification(text, result)
        
        # Update metrics
        await self._update_metrics(result)
        
        return result
    
    async def batch_verify(self, texts: List[str]) -> List[Dict]:
        """Batch verify multiple texts"""
        tasks = [self.verify(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    async def _check_semantic_db(self, text: str) -> Dict:
        """Check against semantic database"""
        # Simulate semantic search
        await asyncio.sleep(0.1)
        
        # In production, this would query a vector database
        similar_documents = random.randint(0, 20)
        matches = random.randint(0, min(10, similar_documents))
        
        return {
            "source": "semantic_db",
            "confidence": min(0.99, 0.7 + (matches / 20)),
            "similar_documents": similar_documents,
            "exact_matches": matches,
            "top_sources": ["wikipedia", "britannica", "academic_journals"]
        }
    
    async def _check_web_sources(self, text: str) -> Dict:
        """Check against web sources"""
        await asyncio.sleep(0.15)
        
        # Simulate web crawl
        sources_found = random.randint(3, 50)
        credible_sources = random.randint(1, sources_found)
        
        return {
            "source": "web_crawl",
            "confidence": min(0.95, 0.5 + (credible_sources / 20)),
            "total_sources": sources_found,
            "credible_sources": credible_sources,
            "domains": [".edu", ".gov", ".org", ".com"]
        }
    
    async def _check_ai_hallucination(self, text: str) -> Dict:
        """Check for AI hallucination patterns"""
        hallucination_markers = [
            "as an AI", "I cannot verify", "according to my training",
            "based on my knowledge cutoff", "I apologize", "I'm not sure",
            "it is possible that", "may be", "could be", "might be"
        ]
        
        detected = [marker for marker in hallucination_markers if marker.lower() in text.lower()]
        
        return {
            "source": "ai_hallucination_detector",
            "confidence": 0.95 if not detected else max(0.1, 1 - (len(detected) * 0.1)),
            "hallucination_risk": len(detected) > 0,
            "detected_markers": detected
        }
    
    async def _check_fact_check_api(self, text: str) -> Dict:
        """Check against fact-check APIs"""
        await asyncio.sleep(0.08)
        
        # Simulate fact-check API call
        verified = random.choice([True, False])
        
        return {
            "source": "fact_check_api",
            "confidence": 0.9 if verified else 0.3,
            "verified": verified,
            "fact_checkers": ["snopes", "politifact", "factcheck.org"]
        }
    
    async def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze text sentiment"""
        # Simple sentiment analysis
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "best"]
        negative_words = ["bad", "terrible", "awful", "horrible", "worst", "fake", "lie"]
        
        text_lower = text.lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        if pos_count > neg_count:
            sentiment = "positive"
            score = min(1.0, 0.5 + (pos_count * 0.1))
        elif neg_count > pos_count:
            sentiment = "negative"
            score = max(0.0, 0.5 - (neg_count * 0.1))
        else:
            sentiment = "neutral"
            score = 0.5
        
        return {
            "sentiment": sentiment,
            "score": round(score, 2),
            "positive_words": pos_count,
            "negative_words": neg_count
        }
    
    async def _extract_claims(self, text: str) -> List[Dict]:
        """Extract individual claims from text"""
        sentences = re.split(r'[.!?]+', text)
        claims = []
        
        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) > 20:
                claims.append({
                    "id": i,
                    "text": sentence.strip(),
                    "type": "factual_statement"
                })
        
        return claims[:10]  # Limit to 10 claims
    
    async def _check_patterns(self, text: str) -> List[Dict]:
        """Check for known misinformation patterns"""
        detected = []
        text_lower = text.lower()
        
        for category, patterns in self.misinfo_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    detected.append({
                        "category": category,
                        "pattern": pattern,
                        "severity": "high" if category == "conspiracy" else "medium"
                    })
        
        return detected
    
    def _get_recommendation(self, verdict: str, risk_score: float) -> str:
        """Get recommendation based on verdict"""
        if verdict == "VERIFIED_TRUE":
            return "Safe to share. High confidence in accuracy."
        elif verdict == "VERIFIED_FALSE":
            return "Do not share. This information is false."
        elif risk_score > 70:
            return "High risk. Verify with additional sources before sharing."
        elif risk_score > 40:
            return "Medium risk. Consider fact-checking before sharing."
        else:
            return "Low risk. Proceed with standard caution."
    
    async def _store_verification(self, text: str, result: Dict):
        """Store verification in database"""
        try:
            await db.execute(
                """INSERT INTO truth_verifications 
                   (text_hash, text_preview, verdict, confidence, risk_score, 
                    claims_count, sources_count, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                result["text_hash"],
                result["text_preview"][:200],
                result["verdict"],
                result["confidence_percentage"],
                result["risk_score"],
                len(result.get("claims_extracted", [])),
                len(result.get("sources_checked", [])),
                datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to store verification: {e}")
    
    async def _update_metrics(self, result: Dict):
        """Update metrics"""
        await cache.hincrby("truth_stats", "total_verifications", 1)
        await cache.hincrby("truth_stats", f"verdict_{result['verdict']}", 1)
    
    async def get_stats(self) -> Dict:
        """Get engine statistics"""
        stats = await cache.hgetall("truth_stats")
        return {
            "total_verifications": int(stats.get("total_verifications", 0)),
            "by_verdict": {
                k.replace("verdict_", ""): int(v) 
                for k, v in stats.items() 
                if k.startswith("verdict_")
            }
        }
    
    async def log_verification(self, text: str, result: Dict):
        """Background logging task"""
        await self._store_verification(text, result)
        logger.info(f"Verification logged: {result['verdict']}")
