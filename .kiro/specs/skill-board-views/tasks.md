# Skill Board Views & Capability Metrics Implementation Plan

## Task Overview

This implementation plan converts the Skill Board Views design into actionable coding tasks. Each task builds incrementally on previous work, focusing on core functionality first with comprehensive testing throughout.

## Implementation Tasks

- [x] 1. Financial Data Filter Service


  - Create FinancialDataFilter class with field exclusion logic
  - Implement list of excluded financial fields (billing_rate, revenue, cost, unbilled, etc.)
  - Build validate_no_financial_data method for response validation
  - Add sanitize_for_export method for data export operations
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_



- [x] 1.1 Write property test for financial data exclusion



  - **Property 4: Financial Data Exclusion**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.3, 4.5**

- [ ] 2. Proficiency Display Service
  - Create ProficiencyDisplay model with level, color, icon, and numeric value
  - Implement proficiency mapping function (Beginner=1 through Expert=5)


  - Build get_proficiency_display method for consistent visual indicators
  - Add color and icon mappings for each proficiency level
  - _Requirements: 1.2_

- [ ] 2.1 Write property test for proficiency display consistency
  - **Property 7: Proficiency Display Consistency**
  - **Validates: Requirements 1.2**

- [ ] 3. Skill Board Service Implementation
  - Create SkillBoardService class for employee skill operations
  - Implement get_employee_skills method to retrieve all skills with proficiency
  - Build get_skill_gaps method to identify skills below requirements
  - Add employee profile data retrieval (home capability, team)
  - _Requirements: 1.1, 1.4, 1.5_

- [ ] 3.1 Write property test for skill board completeness
  - **Property 1: Employee Skill Board Completeness**
  - **Validates: Requirements 1.1, 1.2, 1.5**

- [ ] 4. Capability Alignment Service
  - Create CapabilityAlignmentCalculator for alignment calculations
  - Implement compare_skills_to_requirements method
  - Build calculate_alignment_score method (0-100 scale)
  - Add skill gap identification with requirement comparison
  - _Requirements: 1.3, 1.4_

- [ ] 4.1 Write property test for capability alignment accuracy
  - **Property 2: Capability Alignment Accuracy**
  - **Validates: Requirements 1.3, 1.4**

- [ ] 5. Checkpoint - Core Services Testing
  - Ensure all tests pass, ask the user if questions arise

- [ ] 6. Metrics Service Implementation
  - Create MetricsService class for aggregate calculations
  - Implement get_skill_counts_by_proficiency method
  - Build get_capability_distribution method for skill distributions
  - Add get_capability_coverage method for coverage percentages
  - Implement get_training_needs method for gap analysis
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 5.1, 5.3_

- [ ] 6.1 Write property test for metrics aggregation correctness
  - **Property 3: Metrics Aggregation Correctness**
  - **Validates: Requirements 2.1, 2.2, 5.1, 5.3**

- [ ] 6.2 Write property test for coverage percentage calculation
  - **Property 9: Coverage Percentage Calculation**
  - **Validates: Requirements 5.3**

- [ ] 6.3 Write property test for training needs identification
  - **Property 10: Training Needs Identification**
  - **Validates: Requirements 2.3, 2.4**

- [ ] 7. Data Anonymization Service
  - Create anonymization functions for aggregate metrics
  - Implement remove_personal_identifiers method
  - Build aggregate_without_individuals method for trend data
  - Add validation to ensure no personal data in aggregates
  - _Requirements: 5.2, 5.4_

- [ ] 7.1 Write property test for data anonymization
  - **Property 5: Data Anonymization for Aggregate Metrics**
  - **Validates: Requirements 5.2, 5.4**

- [ ] 8. Metrics Filtering Service
  - Implement filter_by_capability method
  - Add filter_by_team method
  - Build combined filtering with multiple criteria
  - Ensure filtered results maintain accuracy
  - _Requirements: 5.5_

- [ ] 8.1 Write property test for metrics filtering correctness
  - **Property 8: Metrics Filtering Correctness**
  - **Validates: Requirements 5.5**

- [ ] 9. Reconciliation Service Implementation
  - Create ReconciliationService class for assignment comparison
  - Implement compare_assignments method to compare skill board vs HRMS
  - Build detect_discrepancies method for mismatch identification
  - Add generate_reconciliation_report method (without financial data)
  - Implement export_reconciliation_data with sanitization
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 9.1 Write property test for reconciliation comparison accuracy
  - **Property 6: Reconciliation Comparison Accuracy**
  - **Validates: Requirements 4.1, 4.2, 4.4**

- [ ] 10. Checkpoint - All Services Testing
  - Ensure all tests pass, ask the user if questions arise

- [ ] 11. API Endpoints for Skill Board
  - Create GET /api/skill-board/{employee_id} endpoint
  - Implement response filtering through FinancialDataFilter
  - Add role-based access control (employees see only their own data)
  - Build error handling for not found and unauthorized cases
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 12. API Endpoints for Metrics
  - Create GET /api/metrics/capability/{capability} endpoint
  - Implement GET /api/metrics/distribution endpoint for org-wide data
  - Add GET /api/metrics/coverage/{capability} endpoint
  - Build GET /api/metrics/trends endpoint for trend data
  - Implement role-based filtering (CP sees their area, HR sees all)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 13. API Endpoints for Reconciliation
  - Create GET /api/reconciliation/compare/{employee_id} endpoint
  - Implement GET /api/reconciliation/discrepancies endpoint
  - Add GET /api/reconciliation/report endpoint with export
  - Ensure all responses pass through FinancialDataFilter
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 14. Checkpoint - API Testing
  - Ensure all tests pass, ask the user if questions arise

- [ ] 15. Frontend - Employee Skill Board Component
  - Create EmployeeSkillBoard React component
  - Implement skill list with proficiency visual indicators
  - Build capability alignment gauge component
  - Add skill gap highlighting
  - Display home capability and team information
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 16. Frontend - Capability View Component
  - Create CapabilityView React component for CPs/HR
  - Implement skill distribution charts
  - Build coverage metrics display
  - Add training needs table
  - Implement filter controls for capability and team
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 17. Frontend - Metrics Dashboard Component
  - Create MetricsDashboard React component
  - Implement high-level skill counts display
  - Build distribution visualization charts
  - Add trend charts for skill growth
  - Ensure no personal data is displayed
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 18. Frontend - Reconciliation View Component
  - Create ReconciliationView React component
  - Implement assignment comparison table
  - Build discrepancy highlighting
  - Add export functionality with sanitized data
  - Ensure no financial data is displayed
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 19. Role-Based Access Control Integration
  - Implement access control for skill board (employees see own data)
  - Add CP access restrictions (capability area only)
  - Build HR access for organisation-wide data
  - Implement manager access for team-level aggregates
  - Add access logging for audit trails
  - _Requirements: 2.1, 2.2, 5.1, 5.2_

- [ ] 20. Final Checkpoint - System Integration
  - Ensure all tests pass, ask the user if questions arise
  - Validate financial data exclusion across all endpoints
  - Test role-based access control
  - Verify metrics accuracy with sample data
  - Confirm reconciliation functionality
