#!/usr/bin/env python3
"""
Test script for Dutch Insurance Authenticity Rules
"""

import requests
import json
import os

def test_image_analysis(image_path, expected_result=None):
    """Test image analysis with Dutch insurance rules"""
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"\n🔍 Testing image: {os.path.basename(image_path)}")
    print("=" * 50)
    
    try:
        # Send image for analysis
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {'filename': os.path.basename(image_path)}
            
            response = requests.post('http://localhost:5000/analyze', files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"📊 Overall Result: {result['overall_result']}")
            print(f"📈 Overall Score: {result['overall_score']}%")
            
            # Dutch Insurance Compliance Information
            if 'dutch_insurance_compliance' in result:
                compliance = result['dutch_insurance_compliance']
                print(f"\n🇳🇱 Dutch Insurance Compliance:")
                print(f"   Rule Version: {compliance['rule_version']}")
                print(f"   Weighted Score: {compliance['weighted_score']:.1f}%")
                print(f"   Human Review Required: {'Yes' if compliance['requires_human_review'] else 'No'}")
                
                if compliance['critical_flags']:
                    print(f"   🚨 Critical Flags: {', '.join(compliance['critical_flags'])}")
                
                if compliance['decision_reasoning']:
                    print(f"   📝 Decision Reasoning:")
                    for reason in compliance['decision_reasoning']:
                        print(f"      - {reason}")
            
            # AI Detection Results
            ai_analysis = result.get('ai_analysis', {})
            print(f"\n🤖 AI Detection:")
            print(f"   AI Generated: {'Yes' if ai_analysis.get('ai_detected', False) else 'No'}")
            print(f"   AI Confidence: {ai_analysis.get('ai_confidence', 0)}%")
            print(f"   AI Score: {ai_analysis.get('ai_score', 0)}%")
            
            if ai_analysis.get('ai_indicators'):
                print(f"   AI Indicators: {', '.join(ai_analysis['ai_indicators'])}")
            
            # Other key metrics
            print(f"\n📋 Key Metrics:")
            print(f"   Metadata Score: {result['metadata_analysis']['metadata_score']}%")
            print(f"   Compression Score: {result['compression_analysis']['compression_score']}%")
            print(f"   Copy-Move Score: {result['copy_move_analysis']['copy_move_score']}%")
            
            if expected_result:
                if result['overall_result'] == expected_result:
                    print(f"\n✅ Test PASSED: Expected {expected_result}, got {result['overall_result']}")
                else:
                    print(f"\n❌ Test FAILED: Expected {expected_result}, got {result['overall_result']}")
            
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error testing image: {e}")

def test_audit_trail():
    """Test audit trail functionality"""
    print(f"\n📋 Testing Audit Trail")
    print("=" * 30)
    
    try:
        response = requests.get('http://localhost:5000/compliance/audit-trail')
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Audit trail retrieved successfully")
            print(f"   Total decisions: {result['total_decisions']}")
            print(f"   Compliance standards: {', '.join(result['compliance_standards'])}")
            
            if result['audit_trail']:
                print(f"   Latest decision: {result['audit_trail'][-1]}")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing audit trail: {e}")

if __name__ == "__main__":
    print("🇳🇱 Dutch Insurance Authenticity Rules - Test Suite")
    print("=" * 60)
    
    # Test with available images
    test_images = [
        "c:\\Users\\nuben\\Google Drive\\CCS\\Projects\\Image-authentication-toolkit\\images\\11e4c56f-7dde-47e4-84e0-a5048b657fcf.png",
        "c:\\Users\\nuben\\Google Drive\\CCS\\Projects\\Image-authentication-toolkit\\test_image.png"
    ]
    
    for image_path in test_images:
        if os.path.exists(image_path):
            test_image_analysis(image_path)
    
    # Test audit trail
    test_audit_trail()
    
    print(f"\n✅ Test suite completed!")