"""
Underwriting Agent Module for Loan Verification System
Integrates credit underwriting analysis after document verification
"""

import json
import pyodbc
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class UnderwritingAgent:
    """Simplified underwriting agent for integration with loan verification system"""
    
    def __init__(self):
        self.db_connection = None
        self.db_connected = False
    
    def initialize_database_connection(self):
        """Initialize Azure SQL Database connection"""
        try:
            # Global Trust Bank Azure SQL Database connection
            server = 'global-trust-bank.database.windows.net'
            database = 'Global_Trust_Bank'
            username = 'Password_is_Pa_ss_12_3_add_at_inbetween_dont_include_underscore'
            password = 'Pass@123'
            
            # Try multiple driver options in order of preference
            drivers_to_try = [
                '{ODBC Driver 18 for SQL Server}',
                '{ODBC Driver 17 for SQL Server}',
                '{SQL Server}'
            ]
            
            connection_string = None
            for driver in drivers_to_try:
                try:
                    if 'ODBC Driver' in driver:
                        connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
                    else:
                        connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Connection Timeout=30;'
                    
                    print(f"🔄 Trying database driver: {driver}")
                    test_connection = pyodbc.connect(connection_string)
                    test_connection.close()
                    print(f"✅ Database connected with driver: {driver}")
                    break
                except Exception:
                    connection_string = None
                    continue
            
            if not connection_string:
                raise Exception("No compatible ODBC driver found")
            
            # Establish the actual connection
            self.db_connection = pyodbc.connect(connection_string)
            self.db_connected = True
            print("✅ Underwriting Agent: Connected to Global Trust Bank Database")
            return True
            
        except Exception as e:
            print(f"⚠️ Underwriting Agent: Database connection failed: {str(e)}")
            print("📊 Running underwriting analysis with verification data only")
            self.db_connected = False
            return False
    
    def get_customer_data(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve customer data from database"""
        if not self.db_connected or not self.db_connection:
            return None
            
        try:
            cursor = self.db_connection.cursor()
            
            # Simplified query for essential underwriting data
            query = """
            SELECT 
                m.Customer_ID,
                m.Name,
                m.Age,
                m.Annual_Income_Range,
                m.Risk_Category,
                m.KYC_Status,
                e.Monthly_Income,
                e.Total_Monthly_Income,
                e.Employment_Status,
                e.Work_Experience_Years,
                l.Loan_Amount,
                l.Credit_Score,
                l.Loan_Type,
                l.EMI,
                l.Tenure_Months,
                b.Account_Balance,
                b.Average_Monthly_Balance
            FROM Master_Customer_Data m
            LEFT JOIN Employment_Info e ON m.Customer_ID = e.Customer_ID
            LEFT JOIN Loan_Info l ON m.Customer_ID = l.Customer_ID
            LEFT JOIN Bank_Info b ON m.Customer_ID = b.Customer_ID
            WHERE m.Customer_ID = ?
            """
            
            cursor.execute(query, customer_id)
            row = cursor.fetchone()
            
            if not row:
                print(f"⚠️ No database record found for customer {customer_id}")
                return None
                
            # Structure the data
            customer_data = {
                'customer_id': row.Customer_ID,
                'name': row.Name,
                'age': row.Age,
                'monthly_income': float(row.Monthly_Income) if row.Monthly_Income else 0,
                'total_monthly_income': float(row.Total_Monthly_Income) if row.Total_Monthly_Income else 0,
                'employment_status': row.Employment_Status,
                'work_experience_years': row.Work_Experience_Years,
                'loan_amount': float(row.Loan_Amount) if row.Loan_Amount else 0,
                'credit_score': row.Credit_Score,
                'loan_type': row.Loan_Type,
                'emi': float(row.EMI) if row.EMI else 0,
                'tenure_months': row.Tenure_Months,
                'account_balance': float(row.Account_Balance) if row.Account_Balance else 0,
                'average_monthly_balance': float(row.Average_Monthly_Balance) if row.Average_Monthly_Balance else 0,
                'kyc_status': row.KYC_Status,
                'risk_category': row.Risk_Category
            }
            
            cursor.close()
            return customer_data
            
        except Exception as e:
            print(f"❌ Error retrieving customer data: {str(e)}")
            return None
    
    def perform_underwriting_analysis(self, customer_id: str, verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive underwriting analysis using verification results and database data
        
        Args:
            customer_id: Customer identifier
            verification_results: Results from identity, income, guarantor, inspection, valuation agents
            
        Returns:
            Dict containing underwriting analysis and recommendation
        """
        print(f"\n🏦 Starting Underwriting Analysis for Customer {customer_id}")
        print("=" * 60)
        
        # Initialize underwriting result structure
        underwriting_result = {
            'customer_id': customer_id,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'verification_summary': {},
            'financial_analysis': {},
            'risk_assessment': {},
            'underwriting_decision': {},
            'recommendations': []
        }
        
        # Initialize database connection if not already done
        if not self.db_connected:
            self.initialize_database_connection()
        
        # Get customer data from database
        customer_data = self.get_customer_data(customer_id)
        
        # Analyze verification results
        verification_summary = self._analyze_verification_results(verification_results)
        underwriting_result['verification_summary'] = verification_summary
        
        # Perform financial analysis
        financial_analysis = self._perform_financial_analysis(customer_data, verification_results)
        underwriting_result['financial_analysis'] = financial_analysis
        
        # Assess risk
        risk_assessment = self._assess_risk(customer_data, verification_summary, financial_analysis)
        underwriting_result['risk_assessment'] = risk_assessment
        
        # Make underwriting decision
        decision = self._make_underwriting_decision(verification_summary, financial_analysis, risk_assessment)
        underwriting_result['underwriting_decision'] = decision
        
        # Generate recommendations
        recommendations = self._generate_recommendations(decision, risk_assessment, customer_data)
        underwriting_result['recommendations'] = recommendations
        
        return underwriting_result
    
    def _analyze_verification_results(self, verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the results from all verification agents"""
        verification_summary = {
            'total_agents': 0,
            'passed_agents': 0,
            'failed_agents': 0,
            'agent_details': {},
            'overall_verification_score': 0
        }
        
        for agent_key, result in verification_results.items():
            verification_summary['total_agents'] += 1
            
            status = result.get('status', 'unknown')
            if status == 'passed':
                verification_summary['passed_agents'] += 1
                score = 20  # Each passed agent contributes 20 points
            else:
                verification_summary['failed_agents'] += 1
                score = 0
            
            verification_summary['agent_details'][agent_key] = {
                'status': status,
                'score': score,
                'summary': result.get('summary', '')[:200] + "..." if len(result.get('summary', '')) > 200 else result.get('summary', '')
            }
        
        # Calculate overall verification score (out of 100)
        if verification_summary['total_agents'] > 0:
            verification_summary['overall_verification_score'] = (verification_summary['passed_agents'] / verification_summary['total_agents']) * 100
        
        return verification_summary
    
    def _perform_financial_analysis(self, customer_data: Optional[Dict[str, Any]], verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform financial analysis using database data and verification results"""
        financial_analysis = {
            'income_assessment': {},
            'debt_analysis': {},
            'ratios': {},
            'affordability': {}
        }
        
        if customer_data:
            # Use safe defaults for None values
            monthly_income = customer_data.get('total_monthly_income', 0) or 0
            loan_amount = customer_data.get('loan_amount', 0) or 0
            emi = customer_data.get('emi', 0) or 0
            work_experience = customer_data.get('work_experience_years', 0) or 0
            
            # Income assessment
            financial_analysis['income_assessment'] = {
                'monthly_income': monthly_income,
                'annual_income': monthly_income * 12,
                'income_stability': 'Stable' if work_experience >= 2 else 'Limited'
            }
            
            # Calculate key ratios with safe division
            if monthly_income > 0:
                emi_to_income_ratio = (emi / monthly_income) * 100
                loan_to_income_ratio = (loan_amount / (monthly_income * 12)) * 100
            else:
                emi_to_income_ratio = 0
                loan_to_income_ratio = 0
            
            financial_analysis['ratios'] = {
                'emi_to_income_ratio': round(emi_to_income_ratio, 2),
                'loan_to_income_ratio': round(loan_to_income_ratio, 2),
                'emi_to_income_assessment': 'Good' if emi_to_income_ratio <= 40 else 'Moderate' if emi_to_income_ratio <= 60 else 'High Risk'
            }
            
            # Affordability analysis
            financial_analysis['affordability'] = {
                'proposed_emi': emi,
                'affordable_emi': monthly_income * 0.4,  # 40% of income
                'affordability_status': 'Affordable' if emi <= (monthly_income * 0.4) else 'Tight' if emi <= (monthly_income * 0.6) else 'Unaffordable'
            }
        
        return financial_analysis
    
    def _assess_risk(self, customer_data: Optional[Dict[str, Any]], verification_summary: Dict[str, Any], financial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall risk based on all available data"""
        risk_factors = []
        risk_score = 0  # Start with 0, add points for positive factors
        
        # Verification score impact (max 40 points)
        verification_score = verification_summary.get('overall_verification_score', 0) or 0
        risk_score += (verification_score / 100) * 40
        
        if verification_score < 80:
            risk_factors.append(f"Incomplete verification ({verification_score:.1f}% passed)")
        
        # Credit score impact (max 25 points)
        if customer_data:
            credit_score = customer_data.get('credit_score', 0) or 0
            if credit_score >= 750:
                risk_score += 25
            elif credit_score >= 650:
                risk_score += 15
                risk_factors.append("Moderate credit score")
            elif credit_score > 0:
                risk_score += 5
                risk_factors.append("Low credit score")
            else:
                risk_factors.append("No credit score available")
        
        # Financial ratios impact (max 25 points)
        ratios = financial_analysis.get('ratios', {})
        emi_ratio = ratios.get('emi_to_income_ratio', 0) or 0
        
        if emi_ratio <= 40:
            risk_score += 25
        elif emi_ratio <= 60:
            risk_score += 15
            risk_factors.append("Moderate EMI burden")
        else:
            risk_factors.append("High EMI to income ratio")
        
        # Employment stability (max 10 points)
        if customer_data:
            experience = customer_data.get('work_experience_years', 0) or 0
            if experience >= 3:
                risk_score += 10
            elif experience >= 1:
                risk_score += 5
                risk_factors.append("Limited work experience")
            else:
                risk_factors.append("Insufficient work experience")
        
        # Determine risk category
        if risk_score >= 80:
            risk_category = "Low Risk"
        elif risk_score >= 60:
            risk_category = "Medium Risk"
        else:
            risk_category = "High Risk"
        
        return {
            'risk_score': round(risk_score, 1),
            'risk_category': risk_category,
            'risk_factors': risk_factors,
            'max_possible_score': 100
        }
    
    def _make_underwriting_decision(self, verification_summary: Dict[str, Any], financial_analysis: Dict[str, Any], risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Make the final underwriting decision"""
        # Handle None values with safe defaults
        risk_score = risk_assessment.get('risk_score', 0)
        verification_score = verification_summary.get('overall_verification_score', 0)
        
        # Ensure values are not None before comparison
        if risk_score is None:
            risk_score = 0
        if verification_score is None:
            verification_score = 0
        
        # Decision logic
        if risk_score >= 80 and verification_score >= 80:
            decision = "APPROVED"
            confidence = "High"
        elif risk_score >= 60 and verification_score >= 60:
            decision = "CONDITIONAL APPROVAL"
            confidence = "Medium"
        else:
            decision = "REJECTED"
            confidence = "High"
        
        return {
            'decision': decision,
            'confidence': confidence,
            'decision_rationale': f"Risk Score: {risk_score}/100, Verification Score: {verification_score:.1f}%"
        }
    
    def _generate_recommendations(self, decision: Dict[str, Any], risk_assessment: Dict[str, Any], customer_data: Optional[Dict[str, Any]]) -> list:
        """Generate specific recommendations based on the underwriting decision"""
        recommendations = []
        
        decision_result = decision.get('decision', '')
        risk_factors = risk_assessment.get('risk_factors', [])
        
        if decision_result == "APPROVED":
            recommendations.append("✅ Loan approved with standard terms")
            recommendations.append("📋 Proceed with loan documentation")
            recommendations.append("💰 Standard interest rate applicable")
            
        elif decision_result == "CONDITIONAL APPROVAL":
            recommendations.append("⚠️ Conditional approval granted")
            
            # Specific recommendations based on risk factors
            if any("credit score" in factor.lower() for factor in risk_factors):
                recommendations.append("🔒 Require additional collateral or guarantor")
                recommendations.append("📈 Higher interest rate (+1-2%) recommended")
            
            if any("emi" in factor.lower() for factor in risk_factors):
                recommendations.append("💼 Reduce loan amount or extend tenure")
                recommendations.append("📊 Monthly income verification required")
            
            if any("verification" in factor.lower() for factor in risk_factors):
                recommendations.append("📄 Complete pending document verification")
                recommendations.append("✅ Re-verify failed verification steps")
                
        else:  # REJECTED
            recommendations.append("❌ Loan application rejected")
            recommendations.append("📋 Customer should address the following issues:")
            
            for factor in risk_factors:
                recommendations.append(f"   • {factor}")
            
            recommendations.append("🔄 Customer may reapply after 6 months")
            recommendations.append("💡 Suggest credit improvement measures")
        
        return recommendations
    
    def close_connection(self):
        """Close database connection"""
        if self.db_connection:
            self.db_connection.close()
            self.db_connected = False
            print("✅ Underwriting Agent: Database connection closed")

# Global underwriting agent instance
underwriting_agent = UnderwritingAgent()
