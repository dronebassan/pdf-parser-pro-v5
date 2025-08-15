import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics
from enum import Enum

class ExtractionMethod(Enum):
    LIBRARY = "library"
    LLM = "llm"
    HYBRID = "hybrid"

@dataclass
class PerformanceMetrics:
    method: str
    provider: Optional[str]
    processing_time: float
    text_length: int
    tables_count: int
    images_count: int
    confidence_score: float
    file_size: int
    page_count: int
    timestamp: str
    success: bool
    error_message: Optional[str] = None

@dataclass
class ComparisonResult:
    library_result: Optional[PerformanceMetrics]
    llm_result: Optional[PerformanceMetrics]
    winner: str
    speed_improvement: float
    accuracy_comparison: Dict[str, Any]
    recommendation: str

class PerformanceTracker:
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.comparison_history: List[ComparisonResult] = []
    
    def record_performance(
        self,
        method: str,
        provider: Optional[str],
        processing_time: float,
        text_length: int,
        tables_count: int,
        images_count: int,
        confidence_score: float,
        file_size: int,
        page_count: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> PerformanceMetrics:
        """Record performance metrics for a parsing operation"""
        metrics = PerformanceMetrics(
            method=method,
            provider=provider,
            processing_time=processing_time,
            text_length=text_length,
            tables_count=tables_count,
            images_count=images_count,
            confidence_score=confidence_score,
            file_size=file_size,
            page_count=page_count,
            timestamp=datetime.now().isoformat(),
            success=success,
            error_message=error_message
        )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def compare_methods(
        self,
        library_metrics: Optional[PerformanceMetrics],
        llm_metrics: Optional[PerformanceMetrics]
    ) -> ComparisonResult:
        """Compare performance between library and LLM methods"""
        
        # Determine winner based on multiple criteria
        winner = self._determine_winner(library_metrics, llm_metrics)
        
        # Calculate speed improvement
        speed_improvement = 0.0
        if library_metrics and llm_metrics:
            if library_metrics.processing_time > 0 and llm_metrics.processing_time > 0:
                speed_improvement = (
                    (llm_metrics.processing_time - library_metrics.processing_time) 
                    / library_metrics.processing_time * 100
                )
        
        # Accuracy comparison
        accuracy_comparison = self._compare_accuracy(library_metrics, llm_metrics)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            library_metrics, llm_metrics, winner, speed_improvement
        )
        
        comparison = ComparisonResult(
            library_result=library_metrics,
            llm_result=llm_metrics,
            winner=winner,
            speed_improvement=speed_improvement,
            accuracy_comparison=accuracy_comparison,
            recommendation=recommendation
        )
        
        self.comparison_history.append(comparison)
        return comparison
    
    def _determine_winner(
        self,
        library_metrics: Optional[PerformanceMetrics],
        llm_metrics: Optional[PerformanceMetrics]
    ) -> str:
        """Determine which method performed better"""
        
        # If only one method succeeded
        if library_metrics and library_metrics.success and not (llm_metrics and llm_metrics.success):
            return "library"
        if llm_metrics and llm_metrics.success and not (library_metrics and library_metrics.success):
            return "llm"
        
        # If both failed
        if not (library_metrics and library_metrics.success) and not (llm_metrics and llm_metrics.success):
            return "neither"
        
        # If both succeeded, use scoring system
        if library_metrics and llm_metrics and library_metrics.success and llm_metrics.success:
            library_score = self._calculate_score(library_metrics)
            llm_score = self._calculate_score(llm_metrics)
            
            if library_score > llm_score:
                return "library"
            elif llm_score > library_score:
                return "llm"
            else:
                return "tie"
        
        return "unknown"
    
    def _calculate_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate a composite score for comparison"""
        # Weights for different factors
        speed_weight = 0.3
        content_weight = 0.4
        confidence_weight = 0.3
        
        # Speed score (inverse of processing time, normalized)
        speed_score = max(0, 1 - (metrics.processing_time / 60))  # 60 seconds as baseline
        
        # Content score (based on extracted content volume)
        content_score = min(1.0, (metrics.text_length + metrics.tables_count * 100) / 1000)
        
        # Confidence score
        confidence_score = metrics.confidence_score
        
        total_score = (
            speed_weight * speed_score +
            content_weight * content_score +
            confidence_weight * confidence_score
        )
        
        return total_score
    
    def _compare_accuracy(
        self,
        library_metrics: Optional[PerformanceMetrics],
        llm_metrics: Optional[PerformanceMetrics]
    ) -> Dict[str, Any]:
        """Compare accuracy metrics between methods"""
        comparison = {
            "text_extraction": {},
            "table_detection": {},
            "image_detection": {},
            "overall_confidence": {}
        }
        
        if library_metrics and llm_metrics:
            # Text extraction comparison
            comparison["text_extraction"] = {
                "library_length": library_metrics.text_length,
                "llm_length": llm_metrics.text_length,
                "difference_percent": (
                    abs(library_metrics.text_length - llm_metrics.text_length) 
                    / max(library_metrics.text_length, llm_metrics.text_length) * 100
                    if max(library_metrics.text_length, llm_metrics.text_length) > 0 else 0
                )
            }
            
            # Table detection comparison
            comparison["table_detection"] = {
                "library_count": library_metrics.tables_count,
                "llm_count": llm_metrics.tables_count,
                "difference": abs(library_metrics.tables_count - llm_metrics.tables_count)
            }
            
            # Image detection comparison
            comparison["image_detection"] = {
                "library_count": library_metrics.images_count,
                "llm_count": llm_metrics.images_count,
                "difference": abs(library_metrics.images_count - llm_metrics.images_count)
            }
            
            # Confidence comparison
            comparison["overall_confidence"] = {
                "library_confidence": library_metrics.confidence_score,
                "llm_confidence": llm_metrics.confidence_score,
                "difference": abs(library_metrics.confidence_score - llm_metrics.confidence_score)
            }
        
        return comparison
    
    def _generate_recommendation(
        self,
        library_metrics: Optional[PerformanceMetrics],
        llm_metrics: Optional[PerformanceMetrics],
        winner: str,
        speed_improvement: float
    ) -> str:
        """Generate a recommendation based on performance comparison"""
        
        if winner == "library":
            if speed_improvement > 50:  # Library is much faster
                return "Use library method - significantly faster with good accuracy"
            else:
                return "Use library method - better overall performance"
        
        elif winner == "llm":
            if library_metrics and not library_metrics.success:
                return "Use LLM method - library extraction failed"
            else:
                return "Use LLM method - better content extraction despite slower speed"
        
        elif winner == "tie":
            return "Both methods performed similarly - consider using library for speed"
        
        elif winner == "neither":
            return "Both methods failed - document may be corrupted or unsupported"
        
        else:
            return "Unable to determine best method"
    
    def get_performance_summary(self, method: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary statistics"""
        filtered_metrics = self.metrics_history
        if method:
            filtered_metrics = [m for m in self.metrics_history if m.method == method]
        
        if not filtered_metrics:
            return {"error": "No metrics found"}
        
        successful_metrics = [m for m in filtered_metrics if m.success]
        
        if not successful_metrics:
            return {"error": "No successful operations found"}
        
        processing_times = [m.processing_time for m in successful_metrics]
        confidence_scores = [m.confidence_score for m in successful_metrics]
        
        summary = {
            "total_operations": len(filtered_metrics),
            "successful_operations": len(successful_metrics),
            "success_rate": len(successful_metrics) / len(filtered_metrics) * 100,
            "average_processing_time": statistics.mean(processing_times),
            "median_processing_time": statistics.median(processing_times),
            "min_processing_time": min(processing_times),
            "max_processing_time": max(processing_times),
            "average_confidence": statistics.mean(confidence_scores),
            "min_confidence": min(confidence_scores),
            "max_confidence": max(confidence_scores)
        }
        
        return summary
    
    def get_method_comparison_stats(self) -> Dict[str, Any]:
        """Get statistics on method comparisons"""
        if not self.comparison_history:
            return {"error": "No comparisons performed yet"}
        
        winners = [c.winner for c in self.comparison_history]
        winner_counts = {
            "library": winners.count("library"),
            "llm": winners.count("llm"),
            "tie": winners.count("tie"),
            "neither": winners.count("neither")
        }
        
        speed_improvements = [c.speed_improvement for c in self.comparison_history if c.speed_improvement != 0]
        
        stats = {
            "total_comparisons": len(self.comparison_history),
            "winner_distribution": winner_counts,
            "library_win_rate": winner_counts["library"] / len(self.comparison_history) * 100,
            "llm_win_rate": winner_counts["llm"] / len(self.comparison_history) * 100
        }
        
        if speed_improvements:
            stats["speed_analysis"] = {
                "average_speed_difference": statistics.mean(speed_improvements),
                "median_speed_difference": statistics.median(speed_improvements)
            }
        
        return stats
    
    def export_metrics(self, filename: str = "performance_metrics.json"):
        """Export all metrics to JSON file"""
        export_data = {
            "metrics_history": [asdict(m) for m in self.metrics_history],
            "comparison_history": [asdict(c) for c in self.comparison_history],
            "summary": self.get_performance_summary(),
            "method_comparison_stats": self.get_method_comparison_stats()
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return filename