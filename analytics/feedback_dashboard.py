import logging
import asyncio
from typing import Dict, Any, List
from sqlalchemy import select, func
from database.models import AsyncSessionLocal, Feedback, UserRole

logger = logging.getLogger(__name__)

class FeedbackAnalytics:
    """
    Analytics module for the Feedback Dashboard.
    Tracks clinical vs UX performance metrics.
    """
    def __init__(self):
        pass

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Aggregate all metrics for the dashboard.
        """
        async with AsyncSessionLocal() as db:
            try:
                # 1. Total samples
                total_stmt = select(func.count(Feedback.id))
                total_res = await db.execute(total_stmt)
                total_samples = total_res.scalar() or 0
                
                # 2. Average rating by Role
                avg_role_stmt = select(Feedback.role, func.avg(Feedback.rating)).group_by(Feedback.role)
                avg_role_res = await db.execute(avg_role_stmt)
                role_averages = {role: round(float(avg), 2) for role, avg in avg_role_res.all()}
                
                # 3. Most corrected outputs (cases with doctor corrections)
                correction_stmt = select(Feedback.case_id, func.count(Feedback.id)).filter(
                    Feedback.corrected_response_encrypted != None
                ).group_by(Feedback.case_id).order_by(func.count(Feedback.id).desc()).limit(5)
                correction_res = await db.execute(correction_stmt)
                most_corrected_cases = {case: count for case, count in correction_res.all()}
                
                # 4. Rating distribution (0-5)
                dist_stmt = select(Feedback.rating, func.count(Feedback.id)).group_by(Feedback.rating).order_by(Feedback.rating)
                dist_res = await db.execute(dist_stmt)
                rating_distribution = {rating: count for rating, count in dist_res.all()}
                
                return {
                    "overview": {
                        "total_feedback_samples": total_samples,
                        "global_average": round(sum(role_averages.values()) / len(role_averages), 2) if role_averages else 0.0
                    },
                    "performance": {
                        "role_averages": role_averages,
                        "rating_distribution": rating_distribution
                    },
                    "clinical_quality": {
                        "total_corrections": sum(most_corrected_cases.values()),
                        "most_corrected_cases": most_corrected_cases
                    }
                }
            except Exception as e:
                logger.error(f"Analytics Dashboard: Failed to aggregate data: {e}")
                return {"error": str(e)}

    def generate_static_report(self, data: Dict[str, Any]):
        """
        Generates a human-readable text report for logs/emails.
        """
        report = "--- FEEDBACK ANALYTICS REPORT ---\n"
        report += f"Total Samples: {data['overview']['total_feedback_samples']}\n"
        report += "Role Averages:\n"
        for role, avg in data['performance']['role_averages'].items():
            report += f"  - {role.capitalize()}: {avg}/5.0\n"
        report += f"Total Clinical Corrections: {data['clinical_quality']['total_corrections']}\n"
        report += "---------------------------------\n"
        return report

# Singleton
analytics_engine = FeedbackAnalytics()
