"""
Smart Scheduler - ML-Based Assignment System
מערכת שיבוץ חכמה מבוססת למידת מכונה

תכונות:
- לומד מדוגמאות שיבוץ קיימות (20+ דוגמאות)
- משתפר עם פידבק מהמשתמש
- אילוצים קשיחים (מנוחה, זמינות, הסמכות)
- העדפות רכות (רוטציה הוגנת, דפוסים שנלמדו)
"""

import numpy as np
import json
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import pickle
import os


class SmartScheduler:
    """
    מנוע שיבוץ חכם מבוסס ML
    משלב אילוצים קשיחים עם למידה מדוגמאות
    """

    def __init__(self, min_rest_hours: int = 16):
        # לבנות: 8 שעות עבודה + 16 שעות מנוחה
        self.min_rest_hours = min_rest_hours

        # הגבלות גודל למניעת memory leak
        self.MAX_TRAINING_EXAMPLES = 1000
        self.MAX_FEEDBACK_HISTORY = 500
        self.MAX_REJECTED_ASSIGNMENTS = 200

        # נתוני למידה
        self.training_examples = []  # דוגמאות שיבוץ טובות
        self.learned_patterns = {}   # דפוסים שנלמדו
        self.soldier_preferences = defaultdict(lambda: defaultdict(int))  # העדפות חיילים
        self.mahlaka_patterns = defaultdict(lambda: defaultdict(int))     # דפוסי מחלקות
        self.task_history = defaultdict(list)  # היסטוריית משימות לכל חייל

        # פידבק מהמשתמש
        self.user_feedback = []  # [(assignment, rating, changes)]
        self.rejected_assignments = []  # שיבוצים שנדחו

        # סטטיסטיקות
        self.stats = {
            'total_assignments': 0,
            'successful_assignments': 0,
            'user_approvals': 0,
            'user_rejections': 0,
            'manual_changes': 0
        }

    def _cleanup_history(self):
        """ניקוי היסטוריה למניעת memory leak - שומר רק X רשומות אחרונות"""
        if len(self.training_examples) > self.MAX_TRAINING_EXAMPLES:
            self.training_examples = self.training_examples[-self.MAX_TRAINING_EXAMPLES:]

        if len(self.user_feedback) > self.MAX_FEEDBACK_HISTORY:
            self.user_feedback = self.user_feedback[-self.MAX_FEEDBACK_HISTORY:]

        if len(self.rejected_assignments) > self.MAX_REJECTED_ASSIGNMENTS:
            self.rejected_assignments = self.rejected_assignments[-self.MAX_REJECTED_ASSIGNMENTS:]

    # ============================================
    # ML ENHANCEMENTS - שיפורי למידה
    # ============================================

    def calculate_adaptive_weights(self, context: Dict) -> Dict:
        """
        חישוב משקלים דינמיים לפי הקשר

        Args:
            context: {
                'day_of_week': 0-6,
                'week_number': 1-52,
                'workload_level': 'low'/'medium'/'high',
                'approval_rate': 0-1
            }

        Returns:
            dict: משקלים מותאמים
        """
        weights = {
            'rest': 2.0,
            'workload': 1.5,
            'pattern': 3.0,
            'feedback': 4.0,
            'block': 10.0,
            'mahlaka': 0.5
        }

        # התאמה לפי יום בשבוע
        day_of_week = context.get('day_of_week', 0)
        if day_of_week == 4:  # יום שישי
            weights['rest'] *= 0.7  # פחות חשוב
            weights['block'] *= 1.3  # יותר חשוב לסיים נקי
        elif day_of_week == 0:  # יום ראשון
            weights['rest'] *= 1.2  # חשוב יותר להתחיל טרי

        # התאמה לפי רמת עומס
        workload_level = context.get('workload_level', 'medium')
        if workload_level == 'high':
            weights['workload'] *= 2.0  # הרבה יותר חשוב!
            weights['rest'] *= 1.3
        elif workload_level == 'low':
            weights['workload'] *= 0.7

        # התאמה לפי ביצועי המודל
        approval_rate = context.get('approval_rate', 0.7)
        if approval_rate < 0.6:
            weights['feedback'] *= 1.5  # תקשיב יותר למשתמש!
            weights['pattern'] *= 0.8   # הדפוסים הנוכחיים לא טובים
        elif approval_rate > 0.85:
            weights['feedback'] *= 0.9
            weights['pattern'] *= 1.2   # הדפוסים עובדים טוב!

        return weights

    def _calculate_feedback_weight(self, feedback: Dict) -> float:
        """
        חישוב משקל לפידבק לפי איכותו

        Returns: משקל 0-1
        """
        weight = 1.0

        # 1. Time decay - פידבק ישן פחות רלוונטי
        try:
            feedback_age_days = (datetime.now() -
                                datetime.fromisoformat(feedback['timestamp'])).days
            time_weight = math.exp(-feedback_age_days / 90)  # decay after 90 days
            weight *= time_weight
        except:
            pass  # אם אין timestamp, השתמש במשקל 1.0

        # 2. User authority - מי נתן את הפידבק
        user_role = feedback.get('user_role', 'חייל')
        role_weights = {
            'מפ': 1.0,    # משקל מלא
            'ממ': 0.8,
            'מכ': 0.6,
            'סמל': 0.4,
            'חייל': 0.3
        }
        weight *= role_weights.get(user_role, 0.5)

        # 3. Consistency - האם זה עקבי עם פידבקים אחרים?
        soldier_id = feedback.get('soldier_id')
        task_type = feedback.get('task_type')
        rating = feedback.get('rating')

        if soldier_id and task_type:
            similar_feedbacks = [f for f in self.user_feedback
                                if f.get('soldier_id') == soldier_id
                                and f.get('task_type') == task_type]

            if len(similar_feedbacks) > 3:
                recent_feedbacks = similar_feedbacks[-5:]
                same_rating = sum(1 for f in recent_feedbacks
                                 if f.get('rating') == rating)
                consistency = same_rating / len(recent_feedbacks)
                weight *= (0.5 + 0.5 * consistency)  # 0.5-1.0

        return max(0.1, min(1.0, weight))

    def extract_temporal_features(self, task: Dict, soldier: Dict,
                                  schedules: Dict) -> Dict:
        """
        חילוץ פיצ'רים מתקדמים

        Returns: dictionary של פיצ'רים
        """
        features = {}

        # 1. Day of week effects
        day_of_week = task['day'] % 7
        features['day_of_week'] = day_of_week
        features['is_friday'] = (day_of_week == 4)
        features['is_weekend'] = (day_of_week >= 5)
        features['is_monday'] = (day_of_week == 0)

        # 2. Time of day effects
        hour = task['start_hour']
        features['is_night'] = (hour >= 22 or hour <= 6)
        features['is_prime_time'] = (8 <= hour <= 16)
        features['hour'] = hour

        # 3. Soldier fatigue patterns
        soldier_id = soldier['id']
        if soldier_id in schedules:
            recent_tasks = [t for t in schedules[soldier_id]
                           if task['day'] - t[0] <= 3]  # last 3 days
            features['recent_workload'] = sum(t[2] - t[1] for t in recent_tasks)
            features['consecutive_days'] = len(set(t[0] for t in recent_tasks))
        else:
            features['recent_workload'] = 0
            features['consecutive_days'] = 0

        # 4. Task difficulty (מבוסס על היסטוריה)
        task_type = task['type']
        rejection_rate = self._get_task_rejection_rate(task_type)
        features['task_difficulty'] = rejection_rate

        # 5. Mahlaka synergy
        mahlaka_id = soldier.get('mahlaka_id')
        if mahlaka_id:
            mahlaka_success_rate = self._get_mahlaka_success_rate(
                mahlaka_id, task_type
            )
            features['mahlaka_synergy'] = mahlaka_success_rate
        else:
            features['mahlaka_synergy'] = 0.5

        return features

    def _get_task_rejection_rate(self, task_type: str) -> float:
        """חישוב שיעור דחיות למשימה מסוג זה"""
        task_feedbacks = [f for f in self.user_feedback
                         if f.get('task_type') == task_type]

        if not task_feedbacks:
            return 0.3  # ברירת מחדל - קושי בינוני

        rejections = sum(1 for f in task_feedbacks
                        if f.get('rating') == 'rejected')
        return rejections / len(task_feedbacks)

    def _get_mahlaka_success_rate(self, mahlaka_id: int, task_type: str) -> float:
        """חישוב שיעור הצלחה של מחלקה במשימות מסוג זה"""
        mahlaka_feedbacks = []

        # מצא פידבקים של חיילים מהמחלקה הזאת במשימות מסוג זה
        for feedback in self.user_feedback:
            # נצטרך לקשר soldier_id למחלקה - נעשה זאת בצורה פשוטה
            if feedback.get('task_type') == task_type:
                mahlaka_feedbacks.append(feedback)

        if not mahlaka_feedbacks:
            return 0.5  # ברירת מחדל

        approvals = sum(1 for f in mahlaka_feedbacks
                       if f.get('rating') == 'approved')
        return approvals / len(mahlaka_feedbacks)

    def calculate_soldier_score_with_confidence(self, soldier: Dict, task: Dict,
                                               schedules: Dict,
                                               mahlaka_workload: Dict,
                                               all_soldiers: List[Dict] = None) -> Tuple[float, float]:
        """
        חישוב ציון + רמת ביטחון

        Returns: (score, confidence)
            score: ציון
            confidence: ביטחון 0-1 (0=אין מושג, 1=בטוח מאוד)
        """
        score = self.calculate_soldier_score(soldier, task, schedules,
                                             mahlaka_workload, all_soldiers)

        # חישוב ביטחון
        confidence_factors = []

        # 1. כמה נתונים יש על החייל הזה
        soldier_id = soldier['id']
        task_type = task['type']
        key = f"{soldier_id}_{task_type}"

        if key in self.learned_patterns:
            pattern = self.learned_patterns[key]
            # ככל שיותר דוגמאות, יותר ביטחון
            data_confidence = min(1.0, pattern['count'] / 20.0)
            confidence_factors.append(data_confidence)
        else:
            confidence_factors.append(0.1)  # ביטחון נמוך

        # 2. עקביות הפידבקים
        relevant_feedbacks = [f for f in self.user_feedback
                             if f.get('soldier_id') == soldier_id
                             and f.get('task_type') == task_type]

        if len(relevant_feedbacks) > 0:
            approvals = sum(1 for f in relevant_feedbacks
                           if f.get('rating') == 'approved')
            rejections = sum(1 for f in relevant_feedbacks
                            if f.get('rating') == 'rejected')
            consistency = max(approvals, rejections) / len(relevant_feedbacks)
            confidence_factors.append(consistency)

        # 3. עדכניות הנתונים
        if relevant_feedbacks:
            try:
                latest = max(relevant_feedbacks,
                           key=lambda f: datetime.fromisoformat(f['timestamp']))
                days_ago = (datetime.now() -
                           datetime.fromisoformat(latest['timestamp'])).days
                recency_confidence = math.exp(-days_ago / 30)
                confidence_factors.append(recency_confidence)
            except:
                pass

        # ביטחון כולל = ממוצע
        confidence = np.mean(confidence_factors) if confidence_factors else 0.1

        return score, confidence

    def select_soldier_with_exploration(self, scored_soldiers: List[Tuple],
                                       epsilon: float = 0.1) -> Dict:
        """
        בחירת חייל עם איזון exploration-exploitation

        Args:
            scored_soldiers: רשימה של (soldier, score)
            epsilon: סיכוי ל-exploration (0.1 = 10%)

        Returns:
            חייל נבחר
        """
        if not scored_soldiers:
            return None

        if random.random() < epsilon and len(scored_soldiers) > 1:
            # Exploration - בחר רנדומלי מה-top 5
            top_5 = scored_soldiers[:min(5, len(scored_soldiers))]
            return random.choice(top_5)[0]
        else:
            # Exploitation - בחר הטוב ביותר
            return scored_soldiers[0][0]

    def select_multiple_with_exploration(self, scored_soldiers: List[Tuple],
                                        count: int, epsilon: float = 0.05) -> List[Dict]:
        """
        בחירת מספר חיילים עם exploration קל

        Args:
            scored_soldiers: רשימה של (soldier, score)
            count: כמה חיילים לבחור
            epsilon: סיכוי ל-exploration (0.05 = 5%)

        Returns:
            רשימת חיילים נבחרים
        """
        if not scored_soldiers or count == 0:
            return []

        selected = []

        # בחר את הראשון תמיד באופן חכם (exploration)
        if random.random() < epsilon and len(scored_soldiers) > count:
            # exploration - ערבב מעט את הסדר
            top_candidates = scored_soldiers[:min(count * 2, len(scored_soldiers))]
            # בחר את הראשון רנדומלי מה-top candidates
            first = random.choice(top_candidates)[0]
            selected.append(first)
            # המשך לבחור את השאר לפי סדר (פחות הראשון)
            remaining = [s for s in scored_soldiers if s[0]['id'] != first['id']]
            selected.extend([s[0] for s in remaining[:count-1]])
        else:
            # exploitation - בחר את הטובים ביותר
            selected = [s[0] for s in scored_soldiers[:count]]

        return selected

    def explain_soldier_selection(self, soldier: Dict, task: Dict,
                                  schedules: Dict, mahlaka_workload: Dict,
                                  all_soldiers: List[Dict] = None) -> Dict:
        """
        הסבר מפורט למה בחרנו בחייל הזה

        Returns: {
            'soldier_name': str,
            'total_score': float,
            'breakdown': List[Dict],
            'confidence': float,
            'recommendation': str
        }
        """
        soldier_id = soldier['id']
        breakdown = []
        total = 0

        # 1. תפקיד
        if soldier.get('role') == 'מכ':
            contribution = 1000.0
            breakdown.append({
                'factor': '👑 תפקיד מכ',
                'contribution': contribution,
                'explanation': 'מכים מקבלים עדיפות גבוהה'
            })
            total += contribution

        # 2. מנוחה
        rest_hours = self._calculate_rest_hours(
            schedules.get(soldier_id, []),
            task['day'],
            task['start_hour']
        )
        contribution = rest_hours * 2.0
        breakdown.append({
            'factor': '😴 מנוחה',
            'contribution': contribution,
            'explanation': f'{rest_hours:.1f} שעות מאז המשימה האחרונה'
        })
        total += contribution

        # 3. עומס
        workload = self._calculate_workload(schedules.get(soldier_id, []))
        contribution = -workload * 1.5
        breakdown.append({
            'factor': '💼 עומס עבודה',
            'contribution': contribution,
            'explanation': f'{workload:.1f} שעות עבודה השבוע'
        })
        total += contribution

        # 4. ניסיון מדפוסים
        pattern_score = self._get_pattern_score(soldier, task)
        contribution = pattern_score * 3.0
        key = f"{soldier_id}_{task['type']}"
        if key in self.learned_patterns:
            count = self.learned_patterns[key]['count']
            success = self.learned_patterns[key]['success_rate']
            breakdown.append({
                'factor': '📚 ניסיון',
                'contribution': contribution,
                'explanation': f'{count} משימות מסוג {task["type"]}, {success*100:.0f}% הצלחה'
            })
        else:
            breakdown.append({
                'factor': '📚 ניסיון',
                'contribution': contribution,
                'explanation': 'אין נתונים קודמים'
            })
        total += contribution

        # 5. פידבק
        feedback_score = self._get_feedback_score(soldier, task)
        contribution = feedback_score * 4.0
        breakdown.append({
            'factor': '👍 פידבק משתמשים',
            'contribution': contribution,
            'explanation': f'{feedback_score:+.0f} (חיובי-שלילי)'
        })
        total += contribution

        # 6. לבנה
        block_score = self._get_block_consistency_score(
            soldier, task, schedules, all_soldiers
        )
        contribution = block_score * 10.0
        if block_score > 0:
            block_num = task["start_hour"]//8
            explanation = f'המחלקה כבר בלבנה {block_num * 8}-{(block_num + 1) * 8}'
        elif block_score < 0:
            explanation = 'מחלקה אחרת כבר בלבנה - עונש על ערבוב'
        else:
            explanation = 'אין עדיין משימות בלבנה זו'

        breakdown.append({
            'factor': '🧱 עקביות לבנה',
            'contribution': contribution,
            'explanation': explanation
        })
        total += contribution

        # חישוב confidence
        _, confidence = self.calculate_soldier_score_with_confidence(
            soldier, task, schedules, mahlaka_workload, all_soldiers
        )

        # המלצה
        if confidence > 0.8 and total > 100:
            recommendation = 'בחירה מצוינת ✅'
        elif confidence > 0.6:
            recommendation = 'בחירה טובה ✓'
        elif confidence > 0.4:
            recommendation = 'בחירה סבירה ⚠️ (כדאי לבדוק)'
        else:
            recommendation = '⚠️ ביטחון נמוך - אנא בדוק ידנית!'

        return {
            'soldier_name': soldier.get('name', 'לא ידוע'),
            'soldier_id': soldier_id,
            'soldier_role': soldier.get('role', 'לא ידוע'),
            'total_score': round(total, 1),
            'breakdown': breakdown,
            'confidence': round(confidence, 2),
            'recommendation': recommendation
        }

    # ============================================
    # HARD CONSTRAINTS - אילוצים קשיחים
    # ============================================

    def check_availability(self, soldier: Dict, day: int, start_hour: int,
                          length: int, schedules: Dict) -> bool:
        """
        בדיקת זמינות חייל - אילוץ קשיח

        בודק:
        1. לא משובץ בו זמנית (אי-כפילות)
        2. מנוחה מינימלית (16 שעות ללבנות)
        3. אי-זמינות (חופשות, ריתוק, התש"ב)
        """
        soldier_id = soldier['id']
        end_hour = start_hour + length

        # בדיקת חפיפה - אסור שחייל יהיה משובץ פעמיים באותו זמן
        if soldier_id in schedules:
            for assign_day, assign_start, assign_end, _, _ in schedules[soldier_id]:
                # בדוק חפיפה בזמן
                if assign_day == day:
                    if not (end_hour <= assign_start or start_hour >= assign_end):
                        print(f"⚠️  חייל {soldier_id} כבר משובץ ביום {day} בשעה {assign_start}-{assign_end}")
                        return False  # חפיפה! חייל משובץ פעמיים

        # בדיקת מנוחה מינימלית (16 שעות ללבנות - 2 לבנות של 8 שעות)
        # לבנה = 8 שעות עבודה + 16 שעות מנוחה
        if soldier_id in schedules and schedules[soldier_id]:
            last_assign = max(schedules[soldier_id], key=lambda x: (x[0], x[2]))
            last_day, _, last_end, _, _ = last_assign

            # חשב שעות מאז המשימה האחרונה
            if last_day == day:
                # אותו יום
                hours_since = start_hour - last_end
                if hours_since < self.min_rest_hours:
                    return False  # מנוחה לא מספקת
            else:
                # ימים שונים - חשב מנוחה כוללת
                hours_until_midnight = 24 - last_end
                hours_between_days = (day - last_day - 1) * 24
                hours_from_midnight = start_hour
                total_rest = hours_until_midnight + hours_between_days + hours_from_midnight

                if total_rest < self.min_rest_hours:
                    return False  # מנוחה לא מספקת בין ימים

        # בדיקת הסמכות (אם נדרש)
        # זה נבדק בשכבה גבוהה יותר

        return True

    def has_certification(self, soldier: Dict, cert_name: str) -> bool:
        """בדיקה אם לחייל יש הסמכה מסוימת"""
        return cert_name in soldier.get('certifications', [])

    def is_commander(self, soldier: Dict) -> bool:
        """בדיקה אם החייל מפקד"""
        return soldier.get('role') in ['ממ', 'מכ', 'סמל']

    def is_driver(self, soldier: Dict) -> bool:
        """בדיקה אם החייל נהג - רק לפי הסמכה"""
        return 'נהג' in soldier.get('certifications', [])

    # ============================================
    # SOFT PREFERENCES - העדפות רכות (ML)
    # ============================================

    def calculate_soldier_score(self, soldier: Dict, task: Dict,
                                schedules: Dict, mahlaka_workload: Dict,
                                all_soldiers: List[Dict] = None) -> float:
        """
        חישוב ציון לחייל למשימה מסוימת
        גבוה יותר = מתאים יותר

        מבוסס על:
        0. עדיפות תפקיד (מכ קודם!)
        1. מנוחה (כמה נח)
        2. עומס עבודה (כמה עבד השבוע)
        3. דפוסים שנלמדו (האם עשה משימה כזו בעבר)
        4. העדפות מחלקה
        5. פידבק מהמשתמש
        6. עקביות לבנה (מחלקה תופסת לבנה שלמה)
        """
        score = 0.0
        soldier_id = soldier['id']

        # 0. עדיפות למכ - מכ מקבל בונוס גדול!
        if soldier.get('role') == 'מכ':
            score += 1000.0  # בונוס גדול למכים כדי שיבחרו קודם

        # 1. מנוחה - ככל שנח יותר, ציון גבוה יותר
        rest_hours = self._calculate_rest_hours(schedules.get(soldier_id, []),
                                                 task['day'], task['start_hour'])
        score += rest_hours * 2.0  # משקל גבוה למנוחה

        # 2. עומס עבודה - העדפה למי שעבד פחות
        workload = self._calculate_workload(schedules.get(soldier_id, []))
        score -= workload * 1.5  # מי שעבד הרבה מקבל ציון נמוך

        # 3. דפוסים שנלמדו - האם החייל מתאים למשימה הזו?
        pattern_score = self._get_pattern_score(soldier, task)
        score += pattern_score * 3.0

        # 4. העדפות מחלקה - רוטציה הוגנת
        mahlaka_id = soldier.get('mahlaka_id')
        if mahlaka_id and mahlaka_id in mahlaka_workload:
            mahlaka_work = mahlaka_workload[mahlaka_id]
            score -= mahlaka_work * 0.5  # מחלקה שעבדה הרבה מקבלת ציון נמוך

        # 5. פידבק מהמשתמש
        feedback_score = self._get_feedback_score(soldier, task)
        score += feedback_score * 4.0  # משקל גבוה לפידבק!

        # 6. עקביות לבנה - מחלקה תופסת לבנה שלמה (8 שעות)
        block_consistency_score = self._get_block_consistency_score(soldier, task, schedules, all_soldiers)
        score += block_consistency_score * 10.0  # משקל מאוד גבוה ללבנה!

        return score

    def _calculate_rest_hours(self, schedule: List[Tuple], day: int, start_hour: int) -> float:
        """חישוב שעות מנוחה"""
        if not schedule:
            return 100.0  # אין משימות = מנוחה מקסימלית

        last_assign = max(schedule, key=lambda x: (x[0], x[2]))
        last_day, _, last_end, _, _ = last_assign

        if last_day == day:
            return start_hour - last_end
        else:
            hours_until_midnight = 24 - last_end
            hours_between_days = (day - last_day - 1) * 24
            hours_from_midnight = start_hour
            return hours_until_midnight + hours_between_days + hours_from_midnight

    def _calculate_workload(self, schedule: List[Tuple]) -> float:
        """חישוב עומס עבודה כולל"""
        if not schedule:
            return 0.0

        # סכום שעות בשבוע האחרון
        total_hours = sum(end - start for day, start, end, name, type_ in schedule)
        return total_hours

    def _get_pattern_score(self, soldier: Dict, task: Dict) -> float:
        """
        ציון מדפוסים שנלמדו
        האם החייל עשה משימה כזו בעבר ועבד טוב?
        """
        soldier_id = soldier['id']
        task_type = task['type']

        # בדוק במידע שנלמד
        key = f"{soldier_id}_{task_type}"
        if key in self.learned_patterns:
            pattern = self.learned_patterns[key]
            # אם המשתמש אישר שיבוצים כאלה בעבר - ציון גבוה
            return pattern.get('success_rate', 0) * 10

        # בדוק תפקיד - מפקד לסיור, נהג לסיור וכו'
        if task_type == 'סיור':
            if self.is_commander(soldier):
                return 5.0
            if soldier.get('role') == 'לוחם':
                return 3.0

        if task_type == 'שמירה':
            if soldier.get('role') == 'לוחם':
                return 4.0

        return 0.0

    def _get_feedback_score(self, soldier: Dict, task: Dict) -> float:
        """
        ציון מפידבק משתמש
        אם המשתמש אישר/דחה שיבוצים דומים בעבר
        """
        soldier_id = soldier['id']
        task_type = task['type']

        # בדוק בפידבק
        positive_feedback = 0
        negative_feedback = 0

        for feedback in self.user_feedback:
            if feedback['soldier_id'] == soldier_id and feedback['task_type'] == task_type:
                if feedback['rating'] == 'approved':
                    positive_feedback += 1
                elif feedback['rating'] == 'rejected':
                    negative_feedback += 1

        # ציון = (חיובי - שלילי)
        return positive_feedback - negative_feedback

    def _get_block_consistency_score(self, soldier: Dict, task: Dict,
                                    schedules: Dict, all_soldiers: List[Dict] = None) -> float:
        """
        ציון עקביות לבנה - שאיפה שמחלקה תופסת לבנה שלמה של 8 שעות

        לבנה = בלוק של 8 שעות (0-8, 8-16, 16-24)
        אם מחלקה כבר עולה למשימות בלבנה זו (שמירות/סיורים),
        נעדיף להמשיך עם אותה מחלקה.

        זה מבטיח רציפות ועקביות בשיבוץ.
        """
        soldier_mahlaka = soldier.get('mahlaka_id')
        if not soldier_mahlaka:
            return 0.0

        task_day = task['day']
        task_start = task['start_hour']
        task_type = task['type']

        # זיהוי הלבנה (0-8, 8-16, 16-24)
        block = task_start // 8  # 0, 1, או 2
        block_start = block * 8
        block_end = block_start + 8

        # רק משימות שמירה וסיור רלוונטיות ללבנה
        relevant_task_types = ['שמירה', 'סיור']
        if task_type not in relevant_task_types:
            return 0.0

        # בנה מיפוי soldier_id -> mahlaka_id
        soldier_to_mahlaka = {}
        if all_soldiers:
            for s in all_soldiers:
                soldier_to_mahlaka[s['id']] = s.get('mahlaka_id')

        # בדוק אילו מחלקות כבר עלו ללבנה זו ביום הזה
        mahalkot_in_block = defaultdict(int)  # מחלקה -> מספר משימות

        for soldier_id, schedule in schedules.items():
            for assign_day, assign_start, assign_end, assign_name, assign_type in schedule:
                # רק אותו יום, אותה לבנה, ומשימות רלוונטיות
                if (assign_day == task_day and
                    assign_type in relevant_task_types and
                    assign_start >= block_start and
                    assign_start < block_end):

                    # מצא את המחלקה של החייל הזה
                    soldier_mahlaka_id = soldier_to_mahlaka.get(soldier_id)
                    if soldier_mahlaka_id:
                        mahalkot_in_block[soldier_mahlaka_id] += 1

        # אם אין עדיין משימות בלבנה - אין העדפה מיוחדת
        if not mahalkot_in_block:
            return 0.0

        # אם המחלקה שלנו כבר בלבנה - בונוס גדול!
        if soldier_mahlaka in mahalkot_in_block:
            # ככל שיותר משימות למחלקה זו בלבנה, יותר בונוס
            return 20.0 * mahalkot_in_block[soldier_mahlaka]

        # אם יש מחלקה אחרת בלבנה - עונש על ערבוב מחלקות
        return -15.0

    # ============================================
    # LEARNING - למידה מדוגמאות
    # ============================================

    def train_from_example(self, example: Dict):
        """
        לומד מדוגמת שיבוץ אחת

        example = {
            'assignments': [
                {
                    'type': 'סיור',
                    'soldiers': [1, 2, 3],
                    'day': 0,
                    'start_hour': 8,
                    ...
                }
            ],
            'rating': 'excellent'  # או 'good', 'bad'
        }
        """
        self.training_examples.append(example)

        # נתח את הדוגמה ולמד דפוסים
        for assignment in example['assignments']:
            task_type = assignment['type']
            soldiers = assignment.get('soldiers', [])

            # למד איזה חיילים מתאימים למשימה הזו
            for soldier_id in soldiers:
                key = f"{soldier_id}_{task_type}"
                if key not in self.learned_patterns:
                    self.learned_patterns[key] = {
                        'count': 0,
                        'success_rate': 0.0
                    }

                self.learned_patterns[key]['count'] += 1

                # דירוג הדוגמה
                if example['rating'] == 'excellent':
                    self.learned_patterns[key]['success_rate'] += 1.0
                elif example['rating'] == 'good':
                    self.learned_patterns[key]['success_rate'] += 0.5
                # 'bad' לא מוסיף כלום

        # נרמול success_rate
        for key in self.learned_patterns:
            pattern = self.learned_patterns[key]
            if pattern['count'] > 0:
                pattern['success_rate'] = pattern['success_rate'] / pattern['count']

        # ניקוי היסטוריה
        self._cleanup_history()

    def train_from_examples(self, examples: List[Dict]):
        """לומד מרשימת דוגמאות"""
        print(f"🎓 מאמן מודל מ-{len(examples)} דוגמאות...")
        for example in examples:
            self.train_from_example(example)
        print(f"✅ אימון הושלם! נלמדו {len(self.learned_patterns)} דפוסים")
        # ניקוי היסטוריה
        self._cleanup_history()

    def add_feedback(self, assignment: Dict, rating: str, changes: Optional[Dict] = None):
        """
        הוסף פידבק מהמשתמש על שיבוץ

        rating: 'approved', 'rejected', 'modified'
        changes: מה השתנה (אם המשתמש ערך)
        """
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'assignment_id': assignment.get('id'),
            'task_type': assignment['type'],
            'soldier_id': assignment.get('soldiers', []),
            'rating': rating,
            'changes': changes
        }

        self.user_feedback.append(feedback_entry)

        # עדכן סטטיסטיקות
        if rating == 'approved':
            self.stats['user_approvals'] += 1
        elif rating == 'rejected':
            self.stats['user_rejections'] += 1
            self.rejected_assignments.append(assignment)
        elif rating == 'modified':
            self.stats['manual_changes'] += 1

        # למד מהפידבק!
        self._learn_from_feedback(feedback_entry)

        # ניקוי היסטוריה
        self._cleanup_history()

    def add_feedback_with_learning_loop(self, shavzak_id: int, assignment: Dict,
                                       rating: str, changes: Optional[Dict] = None,
                                       iteration_id: Optional[int] = None) -> Dict:
        """
        הוסף פידבק עם לולאת למידה אוטומטית

        אם הפידבק שלילי - המערכת תיצור שיבוץ חדש אוטומטית
        אם חיובי - המערכת תלמד מהשיבוץ הטוב

        Returns:
            dict: {
                'needs_regeneration': bool,  # האם צריך ליצור שיבוץ חדש
                'feedback_saved': bool,      # האם הפידבק נשמר
                'message': str,              # הודעה למשתמש
                'iteration_status': str      # מצב האיטרציה
            }
        """
        # שמור את הפידבק הרגיל
        self.add_feedback(assignment, rating, changes)

        result = {
            'needs_regeneration': False,
            'feedback_saved': True,
            'iteration_status': 'pending'
        }

        if rating == 'approved':
            # פידבק חיובי - המודל למד!
            result['message'] = '✅ תודה! המודל למד מהשיבוץ הטוב הזה'
            result['iteration_status'] = 'approved'
            result['needs_regeneration'] = False

        elif rating == 'rejected':
            # פידבק שלילי - המודל צריך לנסות שוב
            result['message'] = '🔄 השיבוץ נדחה. המערכת תיצור שיבוץ חדש אוטומטית'
            result['iteration_status'] = 'rejected'
            result['needs_regeneration'] = True

            # למד מהטעויות - הורד את הציון של השיבוץ הזה
            self._penalize_rejected_assignment(assignment, changes)

        elif rating == 'modified':
            # השתמש שינה משהו - למד מהשינויים
            result['message'] = '📝 תודה על השינויים! המודל ילמד מהעדכון'
            result['iteration_status'] = 'modified'
            result['needs_regeneration'] = False

            # למד מהשינויים שהמשתמש עשה
            if changes:
                self._learn_from_modifications(assignment, changes)

        return result

    def _penalize_rejected_assignment(self, assignment: Dict, changes: Optional[Dict] = None):
        """
        הורד ציון לשיבוץ שנדחה
        למד מה לא עבד כדי להימנע מזה בעתיד
        """
        task_type = assignment['type']
        soldiers = assignment.get('soldiers', [])

        # הורד את הציון של כל החיילים בשיבוץ הזה למשימה הזו
        for soldier_id in soldiers:
            key = f"{soldier_id}_{task_type}"
            if key not in self.learned_patterns:
                self.learned_patterns[key] = {'count': 0, 'success_rate': 0.5}

            # הורד את הציון משמעותית
            self.learned_patterns[key]['success_rate'] = max(0.0,
                self.learned_patterns[key]['success_rate'] - 0.3)
            self.learned_patterns[key]['count'] += 1

        # אם יש שינויים ספציפיים שהמשתמש רצה, למד מהם
        if changes:
            # למשל: אם המשתמש רצה חיילים שונים
            if 'preferred_soldiers' in changes:
                for soldier_id in changes['preferred_soldiers']:
                    key = f"{soldier_id}_{task_type}"
                    if key not in self.learned_patterns:
                        self.learned_patterns[key] = {'count': 0, 'success_rate': 0.5}
                    # העלה את הציון של החיילים שהמשתמש רצה
                    self.learned_patterns[key]['success_rate'] = min(1.0,
                        self.learned_patterns[key]['success_rate'] + 0.2)

    def _learn_from_modifications(self, original_assignment: Dict, changes: Dict):
        """
        למד מהשינויים שהמשתמש עשה בשיבוץ
        זה מלמד את המודל מה המשתמש באמת רוצה
        """
        task_type = original_assignment['type']

        # אם המשתמש החליף חיילים
        if 'new_soldiers' in changes and 'old_soldiers' in changes:
            # הורד ציון לחיילים הישנים
            for soldier_id in changes['old_soldiers']:
                key = f"{soldier_id}_{task_type}"
                if key not in self.learned_patterns:
                    self.learned_patterns[key] = {'count': 0, 'success_rate': 0.5}
                self.learned_patterns[key]['success_rate'] = max(0.0,
                    self.learned_patterns[key]['success_rate'] - 0.15)

            # העלה ציון לחיילים החדשים
            for soldier_id in changes['new_soldiers']:
                key = f"{soldier_id}_{task_type}"
                if key not in self.learned_patterns:
                    self.learned_patterns[key] = {'count': 0, 'success_rate': 0.5}
                self.learned_patterns[key]['success_rate'] = min(1.0,
                    self.learned_patterns[key]['success_rate'] + 0.15)

    def _learn_from_feedback(self, feedback: Dict):
        """
        למד מפידבק בודד עם Weighted Learning
        משתמש במשקלי זמן ומשקל סמכות משתמש
        """
        task_type = feedback['task_type']
        soldiers = feedback['soldier_id']
        rating = feedback['rating']

        # חשב משקל הפידבק (לפי זמן וסמכות משתמש)
        feedback_weight = self._calculate_feedback_weight(feedback)

        # עדכן דפוסים עם משקל דינמי
        for soldier_id in soldiers:
            key = f"{soldier_id}_{task_type}"
            if key not in self.learned_patterns:
                self.learned_patterns[key] = {'count': 0, 'success_rate': 0.5}

            # אם אושר - שפר את הציון (לפי משקל הפידבק)
            if rating == 'approved':
                improvement = 0.1 * feedback_weight
                self.learned_patterns[key]['success_rate'] = min(1.0,
                    self.learned_patterns[key]['success_rate'] + improvement)
            # אם נדחה - הורד את הציון (לפי משקל הפידבק)
            elif rating == 'rejected':
                penalty = 0.2 * feedback_weight
                self.learned_patterns[key]['success_rate'] = max(0.0,
                    self.learned_patterns[key]['success_rate'] - penalty)

    # ============================================
    # ASSIGNMENT LOGIC - לוגיקת שיבוץ
    # ============================================

    def assign_task(self, task: Dict, available_soldiers: List[Dict],
                   schedules: Dict, mahlaka_workload: Dict) -> Optional[Dict]:
        """
        שיבוץ משימה אחת

        תהליך:
        1. סינון חיילים לפי אילוצים קשיחים
        2. ניקוד חיילים לפי ML
        3. בחירת הטובים ביותר
        """
        task_type = task['type']

        # בחר פונקציית שיבוץ לפי סוג המשימה
        if task_type == 'סיור':
            return self._assign_patrol(task, available_soldiers, schedules, mahlaka_workload)
        elif task_type == 'שמירה':
            return self._assign_guard(task, available_soldiers, schedules, mahlaka_workload)
        elif task_type == 'כוננות א':
            return self._assign_standby_a(task, available_soldiers, schedules, mahlaka_workload)
        elif task_type == 'כוננות ב':
            return self._assign_standby_b(task, available_soldiers, schedules, mahlaka_workload)
        elif task_type == 'חמל':
            return self._assign_operations(task, available_soldiers, schedules, mahlaka_workload)
        elif task_type == 'תורן מטבח':
            return self._assign_kitchen(task, available_soldiers, schedules, mahlaka_workload)
        else:
            # ברירת מחדל - שמירה
            return self._assign_guard(task, available_soldiers, schedules, mahlaka_workload)

    def _assign_patrol(self, task: Dict, all_soldiers: List[Dict],
                      schedules: Dict, mahlaka_workload: Dict) -> Optional[Dict]:
        """
        שיבוץ סיור - קורא דרישות מהתבנית

        דרישות מהתבנית: commanders_needed, soldiers_needed, drivers_needed
        """
        # קריאת דרישות מהתבנית
        commanders_needed = task.get('commanders_needed', 1)
        soldiers_needed = task.get('soldiers_needed', 2)
        drivers_needed = task.get('drivers_needed', 0)
        same_mahlaka_required = task.get('same_mahlaka_required', False)

        # הפרד לפי תפקידים
        commanders = [s for s in all_soldiers if self.is_commander(s)]
        drivers = [s for s in all_soldiers if self.is_driver(s)]
        soldiers = [s for s in all_soldiers if not self.is_commander(s)]

        # סינון לפי זמינות (אילוץ קשיח)
        available_commanders = [c for c in commanders
                               if self.check_availability(c, task['day'], task['start_hour'],
                                                        task['length_in_hours'], schedules)]
        available_drivers = [d for d in drivers
                           if self.check_availability(d, task['day'], task['start_hour'],
                                                    task['length_in_hours'], schedules)]
        available_soldiers = [s for s in soldiers
                            if self.check_availability(s, task['day'], task['start_hour'],
                                                     task['length_in_hours'], schedules)]

        # אם דרוש שיבוץ מאותה מחלקה - נסה למצוא מחלקה שיכולה לספק את כל הדרישות
        if same_mahlaka_required:
            # קבל רשימת כל המחלקות
            mahlaka_ids = set()
            for s in all_soldiers:
                if s.get('mahlaka_id'):
                    mahlaka_ids.add(s['mahlaka_id'])

            # נסה כל מחלקה לפי סדר עומס (פחות -> יותר)
            sorted_mahalkot = sorted(mahlaka_ids, key=lambda m: mahlaka_workload.get(m, 0))

            for mahlaka_id in sorted_mahalkot:
                # סנן רק חיילים מהמחלקה הזאת
                mahlaka_commanders = [c for c in available_commanders if c.get('mahlaka_id') == mahlaka_id]
                mahlaka_drivers = [d for d in available_drivers if d.get('mahlaka_id') == mahlaka_id]
                mahlaka_soldiers = [s for s in available_soldiers if s.get('mahlaka_id') == mahlaka_id]

                # בדוק אם המחלקה יכולה לספק את כל הדרישות
                if (len(mahlaka_commanders) >= commanders_needed and
                    (drivers_needed == 0 or len(mahlaka_drivers) >= drivers_needed) and
                    len(mahlaka_soldiers) >= soldiers_needed):

                    # ניקוד וסידור לפי ML
                    scored_commanders = [(c, self.calculate_soldier_score(c, task, schedules, mahlaka_workload, all_soldiers))
                                        for c in mahlaka_commanders]
                    scored_soldiers = [(s, self.calculate_soldier_score(s, task, schedules, mahlaka_workload, all_soldiers))
                                      for s in mahlaka_soldiers]
                    scored_drivers = [(d, self.calculate_soldier_score(d, task, schedules, mahlaka_workload, all_soldiers))
                                     for d in mahlaka_drivers]

                    # מיון לפי ציון
                    scored_commanders.sort(key=lambda x: x[1], reverse=True)
                    scored_soldiers.sort(key=lambda x: x[1], reverse=True)
                    scored_drivers.sort(key=lambda x: x[1], reverse=True)

                    # בחר הטובים ביותר עם exploration קל (5%)
                    selected_commanders = self.select_multiple_with_exploration(
                        scored_commanders, commanders_needed, epsilon=0.05
                    )
                    selected_soldiers = self.select_multiple_with_exploration(
                        scored_soldiers, soldiers_needed, epsilon=0.05
                    )

                    # עדכן עומס מחלקה
                    mahlaka_workload[mahlaka_id] = mahlaka_workload.get(mahlaka_id, 0) + task['length_in_hours']

                    result = {
                        'commanders': [c['id'] for c in selected_commanders],
                        'soldiers': [s['id'] for s in selected_soldiers],
                        'mahlaka_id': mahlaka_id
                    }

                    # 🐛 תיקון: מפקד-נהג יכול למלא שני תפקידים
                    if drivers_needed > 0:
                        # בדוק כמה מהמפקדים הם גם נהגים
                        commander_ids = set(c['id'] for c in selected_commanders)
                        commanders_who_are_drivers = [d for d in mahlaka_drivers if d['id'] in commander_ids]

                        # הפחת מהדרישה את המפקדים-נהגים
                        remaining_drivers_needed = max(0, drivers_needed - len(commanders_who_are_drivers))

                        # בחר נהגים נוספים רק אם צריך (שאינם המפקדים)
                        available_non_commander_drivers = [d for d in scored_drivers
                                                          if d[0]['id'] not in commander_ids]
                        selected_drivers = [d[0] for d in available_non_commander_drivers[:remaining_drivers_needed]]

                        # הוסף את המפקדים-נהגים לרשימת הנהגים
                        result['drivers'] = ([c['id'] for c in commanders_who_are_drivers] +
                                           [d['id'] for d in selected_drivers])

                    return result

            # לא מצאנו מחלקה שיכולה לספק את כל הדרישות
            print(f"❌ סיור יום {task['day']}: אין מחלקה שיכולה לספק את כל הדרישות")
            return None

        # אם לא דרוש אותה מחלקה - התנהג כמו קודם
        # בדיקת אילוצים קשיחים מהתבנית
        missing = []
        if len(available_commanders) < commanders_needed:
            missing.append(f"מפקדים ({len(available_commanders)}/{commanders_needed})")
        if drivers_needed > 0 and len(available_drivers) < drivers_needed:
            missing.append(f"נהגים ({len(available_drivers)}/{drivers_needed})")
        if len(available_soldiers) < soldiers_needed:
            missing.append(f"חיילים ({len(available_soldiers)}/{soldiers_needed})")

        if missing:
            print(f"❌ סיור יום {task['day']}: חסרים - {', '.join(missing)}")
            return None

        # ניקוד וסידור לפי ML (כולל all_soldiers לחישוב לבנה)
        scored_commanders = [(c, self.calculate_soldier_score(c, task, schedules, mahlaka_workload, all_soldiers))
                            for c in available_commanders]
        scored_soldiers = [(s, self.calculate_soldier_score(s, task, schedules, mahlaka_workload, all_soldiers))
                          for s in available_soldiers]
        scored_drivers = [(d, self.calculate_soldier_score(d, task, schedules, mahlaka_workload, all_soldiers))
                         for d in available_drivers]

        # מיון לפי ציון (גבוה לנמוך)
        scored_commanders.sort(key=lambda x: x[1], reverse=True)
        scored_soldiers.sort(key=lambda x: x[1], reverse=True)
        scored_drivers.sort(key=lambda x: x[1], reverse=True)

        # בחר הטובים ביותר עם exploration - לפי הדרישות מהתבנית
        selected_commanders = self.select_multiple_with_exploration(
            scored_commanders, commanders_needed, epsilon=0.05
        )
        selected_soldiers = self.select_multiple_with_exploration(
            scored_soldiers, soldiers_needed, epsilon=0.05
        )

        # עדכן עומס מחלקה
        mahlaka_id = selected_commanders[0].get('mahlaka_id') if selected_commanders else None
        if mahlaka_id:
            mahlaka_workload[mahlaka_id] = mahlaka_workload.get(mahlaka_id, 0) + task['length_in_hours']

        result = {
            'commanders': [c['id'] for c in selected_commanders],
            'soldiers': [s['id'] for s in selected_soldiers],
            'mahlaka_id': mahlaka_id
        }

        # 🐛 תיקון: מפקד-נהג יכול למלא שני תפקידים
        if drivers_needed > 0:
            # בדוק כמה מהמפקדים הם גם נהגים
            commander_ids = set(c['id'] for c in selected_commanders)
            commanders_who_are_drivers = [d for d in available_drivers if d['id'] in commander_ids]

            # הפחת מהדרישה את המפקדים-נהגים
            remaining_drivers_needed = max(0, drivers_needed - len(commanders_who_are_drivers))

            # בחר נהגים נוספים רק אם צריך (שאינם המפקדים)
            available_non_commander_drivers = [d for d in scored_drivers
                                              if d[0]['id'] not in commander_ids]
            selected_drivers = [d[0] for d in available_non_commander_drivers[:remaining_drivers_needed]]

            # הוסף את המפקדים-נהגים לרשימת הנהגים
            result['drivers'] = ([c['id'] for c in commanders_who_are_drivers] +
                               [d['id'] for d in selected_drivers])

        return result

    def _assign_guard(self, task: Dict, all_soldiers: List[Dict],
                     schedules: Dict, mahlaka_workload: Dict) -> Optional[Dict]:
        """שיבוץ שמירה - 1 לוחם, המתאים ביותר לפי ML + Exploration"""
        soldiers = [s for s in all_soldiers if not self.is_commander(s)]

        # סינון לפי זמינות
        available = [s for s in soldiers
                    if self.check_availability(s, task['day'], task['start_hour'],
                                             task['length_in_hours'], schedules)]

        if not available:
            return None

        # ניקוד וסידור (כולל all_soldiers לחישוב לבנה)
        scored = [(s, self.calculate_soldier_score(s, task, schedules, mahlaka_workload, all_soldiers))
                 for s in available]
        scored.sort(key=lambda x: x[1], reverse=True)

        # בחר עם exploration (10% סיכוי לנסות חייל אחר)
        selected = self.select_soldier_with_exploration(scored, epsilon=0.1)

        return {
            'soldiers': [selected['id']],
            'mahlaka_id': selected.get('mahlaka_id')
        }

    def _assign_standby_a(self, task: Dict, all_soldiers: List[Dict],
                         schedules: Dict, mahlaka_workload: Dict) -> Optional[Dict]:
        """כוננות א' - מפקד + נהג (אם נדרש) + חיילים"""
        # קריאת דרישות מהתבנית
        soldiers_needed = task.get('soldiers_needed', 7)
        drivers_needed = task.get('drivers_needed', 0)  # כמה נהגים נדרשים
        same_mahlaka_required = task.get('same_mahlaka_required', False)

        commanders = [s for s in all_soldiers if self.is_commander(s)]
        drivers = [s for s in all_soldiers if self.is_driver(s)]
        soldiers = [s for s in all_soldiers if not self.is_commander(s)]

        # סינון
        available_commanders = [c for c in commanders
                               if self.check_availability(c, task['day'], task['start_hour'],
                                                        task['length_in_hours'], schedules)]
        available_drivers = [d for d in drivers
                           if self.check_availability(d, task['day'], task['start_hour'],
                                                    task['length_in_hours'], schedules)]
        available_soldiers = [s for s in soldiers
                            if self.check_availability(s, task['day'], task['start_hour'],
                                                     task['length_in_hours'], schedules)]

        # אם דרוש שיבוץ מאותה מחלקה
        if same_mahlaka_required:
            mahlaka_ids = set()
            for s in all_soldiers:
                if s.get('mahlaka_id'):
                    mahlaka_ids.add(s['mahlaka_id'])

            sorted_mahalkot = sorted(mahlaka_ids, key=lambda m: mahlaka_workload.get(m, 0))

            for mahlaka_id in sorted_mahalkot:
                mahlaka_commanders = [c for c in available_commanders if c.get('mahlaka_id') == mahlaka_id]
                mahlaka_drivers = [d for d in available_drivers if d.get('mahlaka_id') == mahlaka_id]
                mahlaka_soldiers = [s for s in available_soldiers if s.get('mahlaka_id') == mahlaka_id]

                if (len(mahlaka_commanders) >= 1 and
                    (drivers_needed == 0 or len(mahlaka_drivers) >= drivers_needed) and
                    len(mahlaka_soldiers) >= soldiers_needed):

                    scored_commanders = [(c, self.calculate_soldier_score(c, task, schedules, mahlaka_workload, all_soldiers))
                                        for c in mahlaka_commanders]
                    scored_drivers = [(d, self.calculate_soldier_score(d, task, schedules, mahlaka_workload, all_soldiers))
                                     for d in mahlaka_drivers]
                    scored_soldiers = [(s, self.calculate_soldier_score(s, task, schedules, mahlaka_workload, all_soldiers))
                                      for s in mahlaka_soldiers]

                    scored_commanders.sort(key=lambda x: x[1], reverse=True)
                    scored_drivers.sort(key=lambda x: x[1], reverse=True)
                    scored_soldiers.sort(key=lambda x: x[1], reverse=True)

                    mahlaka_workload[mahlaka_id] = mahlaka_workload.get(mahlaka_id, 0) + task['length_in_hours']

                    selected_commander = scored_commanders[0][0]
                    result = {
                        'commanders': [selected_commander['id']],
                        'soldiers': [s[0]['id'] for s in scored_soldiers[:soldiers_needed]],
                        'mahlaka_id': mahlaka_id
                    }

                    # 🐛 תיקון: מפקד-נהג יכול למלא שני תפקידים
                    if drivers_needed > 0:
                        # בדוק אם המפקד הוא גם נהג
                        commander_is_driver = selected_commander['id'] in [d['id'] for d in mahlaka_drivers]

                        if commander_is_driver:
                            # המפקד גם נהג - הפחת אחד מהדרישה
                            remaining_drivers_needed = max(0, drivers_needed - 1)
                            # בחר נהגים נוספים (לא המפקד)
                            other_drivers = [d for d in scored_drivers if d[0]['id'] != selected_commander['id']]
                            result['drivers'] = ([selected_commander['id']] +
                                               [d[0]['id'] for d in other_drivers[:remaining_drivers_needed]])
                        else:
                            # המפקד לא נהג - בחר נהגים רגילים
                            result['drivers'] = [d[0]['id'] for d in scored_drivers[:drivers_needed]]

                    return result

            print(f"❌ כוננות א' יום {task['day']}: אין מחלקה שיכולה לספק את כל הדרישות")
            return None

        # אם לא דרוש אותה מחלקה
        # בדיקת אילוצים קשיחים מהתבנית
        missing = []
        if not available_commanders:
            missing.append(f"מפקדים (0 זמינים)")
        if drivers_needed > 0 and len(available_drivers) < drivers_needed:
            missing.append(f"נהגים ({len(available_drivers)}/{drivers_needed})")
        if len(available_soldiers) < soldiers_needed:
            missing.append(f"חיילים ({len(available_soldiers)}/{soldiers_needed})")

        if missing:
            print(f"❌ כוננות א' יום {task['day']}: חסרים - {', '.join(missing)}")
            return None

        # ניקוד (כולל all_soldiers לחישוב לבנה)
        scored_commanders = [(c, self.calculate_soldier_score(c, task, schedules, mahlaka_workload, all_soldiers))
                            for c in available_commanders]
        scored_drivers = [(d, self.calculate_soldier_score(d, task, schedules, mahlaka_workload, all_soldiers))
                         for d in available_drivers]
        scored_soldiers = [(s, self.calculate_soldier_score(s, task, schedules, mahlaka_workload, all_soldiers))
                          for s in available_soldiers]

        scored_commanders.sort(key=lambda x: x[1], reverse=True)
        scored_drivers.sort(key=lambda x: x[1], reverse=True)
        scored_soldiers.sort(key=lambda x: x[1], reverse=True)

        # שמור את mahlaka_id של המפקד הנבחר
        selected_commander = scored_commanders[0][0]
        mahlaka_id = selected_commander.get('mahlaka_id')

        result = {
            'commanders': [selected_commander['id']],
            'soldiers': [s[0]['id'] for s in scored_soldiers[:soldiers_needed]],
            'mahlaka_id': mahlaka_id
        }

        # 🐛 תיקון: מפקד-נהג יכול למלא שני תפקידים
        if drivers_needed > 0:
            # בדוק אם המפקד הוא גם נהג
            commander_is_driver = selected_commander['id'] in [d['id'] for d in available_drivers]

            if commander_is_driver:
                # המפקד גם נהג - הפחת אחד מהדרישה
                remaining_drivers_needed = max(0, drivers_needed - 1)
                # בחר נהגים נוספים (לא המפקד)
                other_drivers = [d for d in scored_drivers if d[0]['id'] != selected_commander['id']]
                result['drivers'] = ([selected_commander['id']] +
                                   [d[0]['id'] for d in other_drivers[:remaining_drivers_needed]])
            else:
                # המפקד לא נהג - בחר נהגים רגילים
                result['drivers'] = [d[0]['id'] for d in scored_drivers[:drivers_needed]]

        return result

    def _assign_standby_b(self, task: Dict, all_soldiers: List[Dict],
                         schedules: Dict, mahlaka_workload: Dict) -> Optional[Dict]:
        """כוננות ב' - מפקד + חיילים (גמיש)"""
        # תיקון: השתמש במספר החיילים מהתבנית
        soldiers_needed = task.get('soldiers_needed', 3)
        same_mahlaka_required = task.get('same_mahlaka_required', False)

        commanders = [s for s in all_soldiers if self.is_commander(s)]
        soldiers = [s for s in all_soldiers if not self.is_commander(s)]

        available_commanders = [c for c in commanders
                               if self.check_availability(c, task['day'], task['start_hour'],
                                                        task['length_in_hours'], schedules)]
        available_soldiers = [s for s in soldiers
                            if self.check_availability(s, task['day'], task['start_hour'],
                                                     task['length_in_hours'], schedules)]

        # אם דרוש שיבוץ מאותה מחלקה
        if same_mahlaka_required:
            mahlaka_ids = set()
            for s in all_soldiers:
                if s.get('mahlaka_id'):
                    mahlaka_ids.add(s['mahlaka_id'])

            sorted_mahalkot = sorted(mahlaka_ids, key=lambda m: mahlaka_workload.get(m, 0))

            for mahlaka_id in sorted_mahalkot:
                mahlaka_commanders = [c for c in available_commanders if c.get('mahlaka_id') == mahlaka_id]
                mahlaka_soldiers = [s for s in available_soldiers if s.get('mahlaka_id') == mahlaka_id]

                if len(mahlaka_commanders) >= 1 and len(mahlaka_soldiers) >= soldiers_needed:
                    scored_commanders = [(c, self.calculate_soldier_score(c, task, schedules, mahlaka_workload, all_soldiers))
                                        for c in mahlaka_commanders]
                    scored_soldiers = [(s, self.calculate_soldier_score(s, task, schedules, mahlaka_workload, all_soldiers))
                                      for s in mahlaka_soldiers]

                    scored_commanders.sort(key=lambda x: x[1], reverse=True)
                    scored_soldiers.sort(key=lambda x: x[1], reverse=True)

                    mahlaka_workload[mahlaka_id] = mahlaka_workload.get(mahlaka_id, 0) + task['length_in_hours']

                    return {
                        'commanders': [scored_commanders[0][0]['id']],
                        'soldiers': [s[0]['id'] for s in scored_soldiers[:soldiers_needed]],
                        'mahlaka_id': mahlaka_id
                    }

            print(f"❌ כוננות ב' יום {task['day']}: אין מחלקה שיכולה לספק את כל הדרישות")
            return None

        # אם לא דרוש אותה מחלקה
        if not available_commanders or len(available_soldiers) < soldiers_needed:
            print(f"⚠️  כוננות ב' יום {task['day']}: חסרים - מפקדים: {len(available_commanders)}, חיילים: {len(available_soldiers)}/{soldiers_needed}")
            return None

        scored_commanders = [(c, self.calculate_soldier_score(c, task, schedules, mahlaka_workload, all_soldiers))
                            for c in available_commanders]
        scored_soldiers = [(s, self.calculate_soldier_score(s, task, schedules, mahlaka_workload, all_soldiers))
                          for s in available_soldiers]

        scored_commanders.sort(key=lambda x: x[1], reverse=True)
        scored_soldiers.sort(key=lambda x: x[1], reverse=True)

        # שמור את mahlaka_id של המפקד הנבחר
        selected_commander = scored_commanders[0][0]
        mahlaka_id = selected_commander.get('mahlaka_id')

        return {
            'commanders': [selected_commander['id']],
            'soldiers': [s[0]['id'] for s in scored_soldiers[:soldiers_needed]],
            'mahlaka_id': mahlaka_id
        }

    def _assign_operations(self, task: Dict, all_soldiers: List[Dict],
                          schedules: Dict, mahlaka_workload: Dict) -> Optional[Dict]:
        """
        חמל - דורש הסמכה/תפקיד נוסף (אילוץ קשיח מהתבנית)

        הסמכה = תפקיד נוסף שחייל יכול למלא במשימות
        לדוגמה: חייל עם הסמכת "חמל" יכול לשמש בחמל
        """
        cert_name = task.get('requires_certification')

        # אם התבנית לא מציינת הסמכה/תפקיד - כל אחד יכול
        if not cert_name:
            available = [s for s in all_soldiers
                        if not self.is_commander(s) and
                           self.check_availability(s, task['day'], task['start_hour'],
                                                 task['length_in_hours'], schedules)]
            if not available:
                return None

            scored = [(s, self.calculate_soldier_score(s, task, schedules, mahlaka_workload, all_soldiers))
                     for s in available]
            scored.sort(key=lambda x: x[1], reverse=True)
            selected = scored[0][0]
            return {
                'soldiers': [selected['id']],
                'mahlaka_id': selected.get('mahlaka_id')
            }

        # התבנית דורשת הסמכה - חובה!
        # חשוב: רק חיילים רגילים (לא מפקדים) יכולים לשמש בחמ"ל
        certified = [s for s in all_soldiers
                    if not self.is_commander(s) and
                       self.has_certification(s, cert_name) and
                       self.check_availability(s, task['day'], task['start_hour'],
                                             task['length_in_hours'], schedules)]

        if not certified:
            print(f"❌ {task['name']} יום {task['day']}: אין חייל (לא מפקד!) מוסמך '{cert_name}' (אילוץ קשיח)")
            return None

        scored = [(s, self.calculate_soldier_score(s, task, schedules, mahlaka_workload, all_soldiers))
                 for s in certified]
        scored.sort(key=lambda x: x[1], reverse=True)

        selected = scored[0][0]
        return {
            'soldiers': [selected['id']],
            'mahlaka_id': selected.get('mahlaka_id')
        }

    def _assign_kitchen(self, task: Dict, all_soldiers: List[Dict],
                       schedules: Dict, mahlaka_workload: Dict) -> Optional[Dict]:
        """תורן מטבח - מספר חיילים"""
        # תיקון: השתמש ב-soldiers_needed במקום needs_soldiers
        num_needed = task.get('soldiers_needed', task.get('needs_soldiers', 1))

        soldiers = [s for s in all_soldiers if not self.is_commander(s)]
        available = [s for s in soldiers
                    if self.check_availability(s, task['day'], task['start_hour'],
                                             task['length_in_hours'], schedules)]

        if len(available) < num_needed:
            print(f"⚠️  תורן מטבח יום {task['day']}: חסרים חיילים (צריך {num_needed}, זמינים {len(available)})")
            return None

        scored = [(s, self.calculate_soldier_score(s, task, schedules, mahlaka_workload, all_soldiers))
                 for s in available]
        scored.sort(key=lambda x: x[1], reverse=True)

        selected = [s[0] for s in scored[:num_needed]]

        # בדוק אם כולם מאותה מחלקה
        mahlaka_ids = set(s.get('mahlaka_id') for s in selected)
        mahlaka_id = mahlaka_ids.pop() if len(mahlaka_ids) == 1 else 'pluga'

        return {
            'soldiers': [s['id'] for s in selected],
            'mahlaka_id': mahlaka_id
        }

    # ============================================
    # PERSISTENCE - שמירה וטעינה
    # ============================================

    def save_model(self, filepath: str):
        """שמור את המודל לקובץ"""
        model_data = {
            'learned_patterns': self.learned_patterns,
            'soldier_preferences': dict(self.soldier_preferences),
            'mahlaka_patterns': dict(self.mahlaka_patterns),
            'user_feedback': self.user_feedback,
            'stats': self.stats,
            'training_examples_count': len(self.training_examples)
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"💾 מודל נשמר ל-{filepath}")

    def load_model(self, filepath: str):
        """טען מודל מקובץ"""
        if not os.path.exists(filepath):
            print(f"⚠️ קובץ מודל לא נמצא: {filepath}")
            return False

        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.learned_patterns = model_data['learned_patterns']
        self.soldier_preferences = defaultdict(lambda: defaultdict(int),
                                              model_data['soldier_preferences'])
        self.mahlaka_patterns = defaultdict(lambda: defaultdict(int),
                                           model_data['mahlaka_patterns'])
        self.user_feedback = model_data['user_feedback']
        self.stats = model_data['stats']

        print(f"✅ מודל נטען מ-{filepath}")
        print(f"   📊 {model_data['training_examples_count']} דוגמאות אימון")
        print(f"   🎯 {len(self.learned_patterns)} דפוסים נלמדו")
        return True

    def get_stats(self) -> Dict:
        """קבל סטטיסטיקות על הביצועים"""
        total = self.stats['total_assignments']
        if total == 0:
            approval_rate = 0
        else:
            approval_rate = (self.stats['user_approvals'] / total) * 100

        return {
            **self.stats,
            'approval_rate': approval_rate,
            'patterns_learned': len(self.learned_patterns),
            'feedback_count': len(self.user_feedback)
        }
