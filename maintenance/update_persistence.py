import os

file_path = "agents/persistence_agent.py"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    exit(1)

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Check if methods already exist
if "async def save_feedback" in content:
    print("Feedback methods already exist.")
    exit(0)

feedback_methods = """
    async def save_feedback(self, user_id: str, role: str, rating: int, ai_response: str, 
                             comment: str = None, corrected_response: str = None, case_id: str = None):
        \"\"\"Save user feedback securely (Async).\"\"\"
        async with AsyncSessionLocal() as db:
            try:
                from database.models import Feedback
                
                enc_response = self.governance.encrypt(ai_response)
                enc_comment = self.governance.encrypt(comment) if comment else None
                enc_correction = self.governance.encrypt(corrected_response) if corrected_response else None
                
                new_fb = Feedback(
                    user_id=user_id,
                    role=role,
                    case_id=case_id,
                    ai_response_encrypted=enc_response,
                    rating=rating,
                    comment_encrypted=enc_comment,
                    corrected_response_encrypted=enc_correction
                )
                db.add(new_fb)
                await db.commit()
                return new_fb.id
            except Exception as e:
                logger.error(f"Failed to save feedback: {e}")
                await db.rollback()
                return None

    async def get_feedback_by_case(self, case_id: str):
        \"\"\"Retrieve all feedback for a specific case (Async).\"\"\"
        async with AsyncSessionLocal() as db:
            try:
                from database.models import Feedback
                from sqlalchemy import select
                
                stmt = select(Feedback).filter(Feedback.case_id == case_id).order_by(Feedback.timestamp.desc())
                res = await db.execute(stmt)
                items = res.scalars().all()
                
                results = []
                for fb in items:
                    results.append({
                        "id": fb.id,
                        "user_id": fb.user_id,
                        "role": fb.role,
                        "rating": fb.rating,
                        "comment": self.governance.decrypt(fb.comment_encrypted) if fb.comment_encrypted else None,
                        "correction": self.governance.decrypt(fb.corrected_response_encrypted) if fb.corrected_response_encrypted else None,
                        "timestamp": fb.timestamp
                    })
                return results
            except Exception as e:
                logger.error(f"Failed to fetch feedback for case {case_id}: {e}")
                return []

    async def get_feedback_analytics(self):
        \"\"\"Aggregate feedback metrics for the system (Async).\"\"\"
        async with AsyncSessionLocal() as db:
            try:
                from database.models import Feedback
                from sqlalchemy import select, func
                
                # Overall average rating
                stmt_avg = select(func.avg(Feedback.rating))
                res_avg = await db.execute(stmt_avg)
                avg_rating = res_avg.scalar() or 0.0
                
                # Count by role
                stmt_role = select(Feedback.role, func.count(Feedback.id)).group_by(Feedback.role)
                res_role = await db.execute(stmt_role)
                role_counts = {role: count for role, count in res_role.all()}
                
                # Doctor vs Patient averages
                stmt_role_avg = select(Feedback.role, func.avg(Feedback.rating)).group_by(Feedback.role)
                res_role_avg = await db.execute(stmt_role_avg)
                role_avgs = {role: float(avg) for role, avg in res_role_avg.all()}
                
                return {
                    "average_rating": float(avg_rating),
                    "total_entries": sum(role_counts.values()),
                    "role_distribution": role_counts,
                    "role_averages": role_avgs
                }
            except Exception as e:
                logger.error(f"Failed to generate feedback analytics: {e}")
                return {}
"""

# Append at the end of the class
if content.strip().endswith("}"):  # if it ends with a dict or something
    pass

# Find the last line of the class (usually ends with a method or return)
# We can just append it to the end of the file if the class is the main thing,
# but better to find the last method.
# Since we know the file ends with some methods, we'll just append.

with open(file_path, "a", encoding="utf-8") as f:
    f.write(feedback_methods)

print("Feedback methods appended successfully.")
