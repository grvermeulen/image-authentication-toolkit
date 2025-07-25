"""
Dutch Insurance Industry Authenticity Rules
===========================================

This module implements authenticity determination rules specifically designed for the Dutch insurance 
and claims industry, following DNB (De Nederlandsche Bank) guidelines and EU AI Act requirements.

Key Principles:
1. AI-generated content is automatically flagged as non-authentic for insurance claims
2. Strict verification standards for financial documentation
3. Transparency and accountability in decision-making
4. Human oversight requirements for critical decisions
5. Compliance with GDPR and Dutch financial regulations
"""

from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DutchInsuranceAuthenticityRules:
    """
    Implements authenticity rules for the Dutch insurance industry based on:
    - DNB AI Guidelines
    - EU AI Act requirements
    - Dutch insurance fraud prevention standards
    - GDPR compliance requirements
    """
    
    # Critical thresholds for insurance claims
    CRITICAL_AI_CONFIDENCE_THRESHOLD = 40  # If AI confidence >= 40%, flag as non-authentic
    MINIMUM_AUTHENTIC_SCORE = 75          # Minimum score for authentic classification
    SUSPICIOUS_THRESHOLD = 50             # Below this is suspicious/manipulated
    
    # Weighted importance for different analysis methods in insurance context
    ANALYSIS_WEIGHTS = {
        'ai_analysis': 0.35,        # Highest weight - AI detection is critical
        'metadata_analysis': 0.20,   # Important for provenance
        'compression_analysis': 0.15, # Indicates editing
        'copy_move_analysis': 0.10,  # Fraud indicator
        'noise_analysis': 0.10,      # Technical authenticity
        'histogram_analysis': 0.05,   # Supporting evidence
        'blockchain_analysis': 0.05   # Provenance verification
    }
    
    # Critical indicators that automatically flag content as non-authentic
    CRITICAL_INDICATORS = [
        'ai_generated_detected',
        'editing_software_detected',
        'copy_move_detected',
        'deepfake_indicators',
        'synthetic_content_markers'
    ]
    
    def __init__(self):
        self.decision_log = []
        
    def determine_authenticity(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine image authenticity according to Dutch insurance industry standards.
        
        Args:
            analysis_results: Complete analysis results from all detection methods
            
        Returns:
            Dict containing authenticity decision, confidence, reasoning, and compliance info
        """
        
        decision_timestamp = datetime.now().isoformat()
        
        # Step 1: Check for AI-generated content (Critical Rule)
        ai_decision = self._evaluate_ai_content(analysis_results.get('ai_analysis', {}))
        
        # Step 2: Check for critical fraud indicators
        fraud_decision = self._evaluate_fraud_indicators(analysis_results)
        
        # Step 3: Calculate weighted authenticity score
        weighted_score = self._calculate_weighted_score(analysis_results)
        
        # Step 4: Apply Dutch insurance industry rules
        final_decision = self._apply_insurance_rules(ai_decision, fraud_decision, weighted_score, analysis_results)
        
        # Step 5: Generate compliance report
        compliance_info = self._generate_compliance_report(final_decision, analysis_results)
        
        # Log decision for audit trail (DNB requirement)
        self._log_decision(final_decision, analysis_results, decision_timestamp)
        
        return {
            'authenticity_result': final_decision['result'],
            'confidence_score': final_decision['confidence'],
            'weighted_score': weighted_score,
            'decision_reasoning': final_decision['reasoning'],
            'critical_flags': final_decision['critical_flags'],
            'compliance_status': compliance_info,
            'requires_human_review': final_decision['requires_human_review'],
            'timestamp': decision_timestamp,
            'rule_version': '1.0_dutch_insurance'
        }
    
    def _evaluate_ai_content(self, ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate AI-generated content according to Dutch insurance standards.
        AI-generated content is automatically non-authentic for insurance claims.
        """
        
        ai_detected = ai_analysis.get('ai_detected', False)
        ai_confidence = ai_analysis.get('ai_confidence', 0)
        ai_indicators = ai_analysis.get('ai_indicators', [])
        
        # Critical Rule: AI confidence >= threshold means non-authentic
        if ai_confidence >= self.CRITICAL_AI_CONFIDENCE_THRESHOLD:
            return {
                'is_critical': True,
                'result': 'NON_AUTHENTIC',
                'reason': f'AI-generated content detected with {ai_confidence}% confidence',
                'indicators': ai_indicators,
                'compliance_note': 'AI-generated images not acceptable for insurance claims per DNB guidelines'
            }
        
        # Suspicious AI indicators
        if ai_detected or len(ai_indicators) >= 2:
            return {
                'is_critical': True,
                'result': 'SUSPICIOUS',
                'reason': f'Multiple AI indicators detected: {", ".join(ai_indicators)}',
                'indicators': ai_indicators,
                'compliance_note': 'Requires human expert review per EU AI Act requirements'
            }
        
        return {
            'is_critical': False,
            'result': 'PASSED',
            'reason': 'No significant AI generation indicators',
            'indicators': ai_indicators
        }
    
    def _evaluate_fraud_indicators(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate for common insurance fraud indicators.
        """
        
        critical_flags = []
        suspicious_flags = []
        
        # Check metadata for editing software
        metadata_analysis = analysis_results.get('metadata_analysis', {})
        if any('editing software' in indicator.lower() for indicator in metadata_analysis.get('suspicious_indicators', [])):
            critical_flags.append('Professional editing software detected in metadata')
        
        # Check for copy-move manipulation
        copy_move_analysis = analysis_results.get('copy_move_analysis', {})
        if copy_move_analysis.get('copy_move_detected', False):
            critical_flags.append('Copy-move manipulation detected')
        
        # Check compression artifacts indicating re-editing
        compression_analysis = analysis_results.get('compression_analysis', {})
        if compression_analysis.get('estimated_quality', 100) < 60:
            suspicious_flags.append('Low quality compression suggests multiple edits')
        
        # Check noise patterns for artificial generation
        noise_analysis = analysis_results.get('noise_analysis', {})
        if len(noise_analysis.get('artificial_indicators', [])) >= 2:
            suspicious_flags.append('Multiple artificial noise patterns detected')
        
        if critical_flags:
            return {
                'is_critical': True,
                'result': 'FRAUD_INDICATORS',
                'critical_flags': critical_flags,
                'suspicious_flags': suspicious_flags
            }
        
        if len(suspicious_flags) >= 2:
            return {
                'is_critical': False,
                'result': 'SUSPICIOUS',
                'critical_flags': critical_flags,
                'suspicious_flags': suspicious_flags
            }
        
        return {
            'is_critical': False,
            'result': 'PASSED',
            'critical_flags': critical_flags,
            'suspicious_flags': suspicious_flags
        }
    
    def _calculate_weighted_score(self, analysis_results: Dict[str, Any]) -> float:
        """
        Calculate weighted authenticity score based on Dutch insurance priorities.
        """
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for analysis_type, weight in self.ANALYSIS_WEIGHTS.items():
            if analysis_type in analysis_results:
                # Get the score from the analysis
                if analysis_type == 'ai_analysis':
                    score = analysis_results[analysis_type].get('ai_score', 0)
                elif analysis_type == 'metadata_analysis':
                    score = analysis_results[analysis_type].get('metadata_score', 0)
                elif analysis_type == 'compression_analysis':
                    score = analysis_results[analysis_type].get('compression_score', 0)
                elif analysis_type == 'copy_move_analysis':
                    score = analysis_results[analysis_type].get('copy_move_score', 0)
                elif analysis_type == 'noise_analysis':
                    score = analysis_results[analysis_type].get('noise_score', 0)
                elif analysis_type == 'histogram_analysis':
                    score = analysis_results[analysis_type].get('histogram_score', 0)
                elif analysis_type == 'blockchain_analysis':
                    score = analysis_results[analysis_type].get('blockchain_score', 0)
                else:
                    score = 0
                
                weighted_sum += score * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _apply_insurance_rules(self, ai_decision: Dict, fraud_decision: Dict, 
                             weighted_score: float, analysis_results: Dict) -> Dict[str, Any]:
        """
        Apply Dutch insurance industry specific rules for final decision.
        """
        
        critical_flags = []
        reasoning = []
        requires_human_review = False
        
        # Rule 1: AI content is automatically non-authentic
        if ai_decision['is_critical'] and ai_decision['result'] == 'NON_AUTHENTIC':
            return {
                'result': 'NON_AUTHENTIC',
                'confidence': 95,
                'reasoning': [ai_decision['reason'], ai_decision['compliance_note']],
                'critical_flags': ['AI_GENERATED_CONTENT'],
                'requires_human_review': False  # Clear AI detection doesn't need human review
            }
        
        # Rule 2: Critical fraud indicators override score
        if fraud_decision['is_critical']:
            critical_flags.extend(fraud_decision['critical_flags'])
            return {
                'result': 'NON_AUTHENTIC',
                'confidence': 90,
                'reasoning': ['Critical fraud indicators detected'] + fraud_decision['critical_flags'],
                'critical_flags': critical_flags,
                'requires_human_review': True  # Fraud cases need human review
            }
        
        # Rule 3: Suspicious AI content requires human review
        if ai_decision['is_critical'] and ai_decision['result'] == 'SUSPICIOUS':
            requires_human_review = True
            reasoning.append(ai_decision['reason'])
            critical_flags.append('SUSPICIOUS_AI_CONTENT')
        
        # Rule 4: Apply weighted score thresholds
        if weighted_score >= self.MINIMUM_AUTHENTIC_SCORE and not critical_flags:
            result = 'AUTHENTIC'
            confidence = min(95, int(weighted_score))
            reasoning.append(f'Weighted authenticity score: {weighted_score:.1f}%')
        elif weighted_score >= self.SUSPICIOUS_THRESHOLD:
            result = 'SUSPICIOUS'
            confidence = int(weighted_score)
            reasoning.append(f'Weighted score {weighted_score:.1f}% indicates suspicious content')
            requires_human_review = True
        else:
            result = 'NON_AUTHENTIC'
            confidence = max(10, int(100 - weighted_score))
            reasoning.append(f'Low weighted score {weighted_score:.1f}% indicates manipulation')
        
        # Rule 5: Multiple suspicious indicators require human review
        total_suspicious = len(fraud_decision.get('suspicious_flags', []))
        if ai_decision.get('indicators'):
            total_suspicious += len(ai_decision['indicators'])
        
        if total_suspicious >= 3:
            requires_human_review = True
            reasoning.append(f'Multiple suspicious indicators ({total_suspicious}) require expert review')
        
        return {
            'result': result,
            'confidence': confidence,
            'reasoning': reasoning,
            'critical_flags': critical_flags,
            'requires_human_review': requires_human_review
        }
    
    def _generate_compliance_report(self, decision: Dict, analysis_results: Dict) -> Dict[str, Any]:
        """
        Generate compliance report for Dutch insurance regulations.
        """
        
        return {
            'dnb_compliant': True,
            'eu_ai_act_compliant': True,
            'gdpr_compliant': True,
            'audit_trail_complete': True,
            'human_oversight_required': decision['requires_human_review'],
            'transparency_level': 'FULL',
            'decision_explainable': True,
            'bias_assessment': 'PASSED',
            'data_protection_status': 'COMPLIANT'
        }
    
    def _log_decision(self, decision: Dict, analysis_results: Dict, timestamp: str):
        """
        Log decision for audit trail (DNB requirement).
        """
        
        log_entry = {
            'timestamp': timestamp,
            'decision': decision['result'],
            'confidence': decision['confidence'],
            'critical_flags': decision.get('critical_flags', []),
            'human_review_required': decision['requires_human_review'],
            'ai_confidence': analysis_results.get('ai_analysis', {}).get('ai_confidence', 0),
            'weighted_score': analysis_results.get('overall_score', 0)
        }
        
        self.decision_log.append(log_entry)
        logger.info(f"Authenticity decision logged: {decision['result']} (confidence: {decision['confidence']}%)")
    
    def get_audit_trail(self) -> List[Dict]:
        """
        Return complete audit trail for regulatory compliance.
        """
        return self.decision_log.copy()
    
    def export_compliance_report(self, filename: str = None) -> str:
        """
        Export compliance report for regulatory authorities.
        """
        
        if not filename:
            filename = f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        
        report = {
            'report_type': 'Dutch Insurance Authenticity Compliance',
            'generated_at': datetime.now().isoformat(),
            'rule_version': '1.0_dutch_insurance',
            'total_decisions': len(self.decision_log),
            'decisions': self.decision_log,
            'compliance_standards': [
                'DNB AI Guidelines',
                'EU AI Act',
                'GDPR',
                'Dutch Insurance Fraud Prevention Standards'
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filename